# routes/auth.py
"""
Authentication module for Bon Laundry Station.
All users (Manager, Staff, Customer) authenticate exclusively through Google OAuth.
No custom email/password forms are presented to users.

Flow:
  /login or /register  ->  "Continue with Google"  ->  /auth/google/login
  ->  Google OAuth consent  ->  /auth/google/callback
  ->  _login_or_register_google_user (matches email to DB role)
  ->  get_role_home(role)  ->  workspace dashboard
"""
import os
import json
import re
import secrets
import urllib.request
import urllib.parse
from pathlib import Path
from urllib.error import HTTPError
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from sqlalchemy import case
from config.database import SessionLocal
from models.schemas import User
from services.rbac import Role, get_role_home, api_roles_required, get_current_user_role, is_authenticated
from services.audit_service import AuditService, AuditAction
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_env():
    """Ensure .env values are loaded into os.environ at runtime."""
    env_file = Path(__file__).resolve().parent.parent / '.env'
    if env_file.exists():
        for line in env_file.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

def _get_google_client_id():
    if not os.environ.get('GOOGLE_CLIENT_ID'):
        _load_env()
    return os.environ.get('GOOGLE_CLIENT_ID', '').strip()

def _get_google_client_secret():
    if not os.environ.get('GOOGLE_CLIENT_SECRET'):
        _load_env()
    return os.environ.get('GOOGLE_CLIENT_SECRET', '').strip()

def _get_google_redirect_uri():
    if not os.environ.get('GOOGLE_REDIRECT_URI'):
        _load_env()
    custom = os.environ.get('GOOGLE_REDIRECT_URI', '').strip()
    if custom:
        return custom
    uri = url_for('auth.google_callback', _external=True)
    if request.headers.get('X-Forwarded-Proto') == 'https' and uri.startswith('http://'):
        uri = 'https://' + uri[7:]
    return uri


def _login_or_register_google_user(email, name, google_id=None, avatar_url=None):
    """
    Resolves an authenticated Google user to a system account.

    Logic:
      1. Match by google_id (most specific).
      2. Fall back to email match — this links existing Staff/Manager accounts to Google.
      3. If neither matches, auto-create a new Customer account.

    Returns (user, redirect_url).
    """
    email = (email or '').strip().lower()
    name = (name or '').strip() or email.split('@')[0].replace('.', ' ').title()

    db = SessionLocal()
    try:
        user = None

        # Priority 1: exact Google sub match
        if google_id:
            user = db.query(User).filter(User.google_id == str(google_id)).first()

        # Priority 2: email match — upgrades existing accounts (Staff/Manager)
        if not user and email:
            user = db.query(User).filter(User.email == email).first()

        if user:
            # Link Google ID and avatar if not already set
            if google_id and not user.google_id:
                user.google_id = str(google_id)
            if avatar_url and not user.avatar_url:
                user.avatar_url = avatar_url
            # Update display name from Google (keeps it fresh)
            if name:
                user.name = name
            user.failed_login_attempts = 0
            user.login_locked_until = None
            db.commit()
        else:
            # New visitor → auto-provision as Customer
            user = User(
                name=name,
                email=email,
                password=None,
                user_role=Role.CUSTOMER,
                google_id=str(google_id) if google_id else None,
                avatar_url=avatar_url,
                failed_login_attempts=0
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Populate session
        session['user_id'] = user.user_id
        session['user_name'] = user.name
        session['user_email'] = user.email
        session['user_role'] = user.user_role
        session['base_user_role'] = user.user_role
        session['avatar_url'] = (
            user.avatar_url
            or f"https://ui-avatars.com/api/?name={urllib.parse.quote(user.name)}&background=0284c7&color=fff"
        )

        AuditService.log(
            action=AuditAction.USER_LOGIN,
            entity_type='User',
            entity_id=str(user.user_id),
            details=f"User signed in via Google OAuth as {user.user_role}",
            user_id=user.user_id,
            user_name=user.name,
            user_email=user.email,
            user_role=user.user_role
        )

        return user, get_role_home(user.user_role)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Public routes: /login and /register both show the Google-only sign-in page
# ---------------------------------------------------------------------------

@auth_bp.route('/login')
def login():
    """Unified entry point — shows Google Sign-In page. No password form."""
    if is_authenticated():
        return redirect(get_role_home())
    return render_template('auth/login.html', google_client_id=_get_google_client_id())


@auth_bp.route('/register')
def register():
    """Alias for /login — customers use Google to create accounts."""
    if is_authenticated():
        return redirect(get_role_home())
    return redirect(url_for('auth.login'))


# Redirect legacy staff/admin direct URLs to the unified portal
@auth_bp.route('/staff')
@auth_bp.route('/admin')
def staff_portal_redirect():
    return redirect(url_for('auth.login'))


# ---------------------------------------------------------------------------
# Google OAuth 2.0 — Authorization Code Flow
# ---------------------------------------------------------------------------

@auth_bp.route('/auth/google/login')
def google_login():
    """Initiates Google OAuth2 Authorization Code flow."""
    client_id = _get_google_client_id()
    if not client_id:
        flash('Google Sign-In is not configured. Please contact the administrator.', 'danger')
        return redirect(url_for('auth.login'))

    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    redirect_uri = _get_google_redirect_uri()

    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'prompt': 'select_account',   # Always let the user pick their account
        'access_type': 'online',
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)


@auth_bp.route('/auth/google/callback')
def google_callback():
    """Handles Google OAuth2 callback. Creates or logs in the user, then RBAC-routes them."""
    error = request.args.get('error')
    if error:
        flash(f'Google sign-in was cancelled or denied: {error}', 'danger')
        return redirect(url_for('auth.login'))

    code = request.args.get('code')
    state = request.args.get('state')
    if not code:
        flash('Authorization code missing from Google. Please try again.', 'danger')
        return redirect(url_for('auth.login'))

    saved_state = session.pop('oauth_state', None)
    if saved_state and state != saved_state:
        flash('Security check failed (state mismatch). Please try again.', 'danger')
        return redirect(url_for('auth.login'))

    client_id = _get_google_client_id()
    client_secret = _get_google_client_secret()
    redirect_uri = _get_google_redirect_uri()

    try:
        # Step 1: Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        post_data = urllib.parse.urlencode({
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }).encode('utf-8')

        req = urllib.request.Request(
            token_url, data=post_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            token_json = json.loads(resp.read().decode('utf-8'))

        access_token = token_json.get('access_token')
        if not access_token:
            flash('Failed to retrieve access token from Google. Please try again.', 'danger')
            return redirect(url_for('auth.login'))

        # Step 2: Fetch user profile from Google
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        user_req = urllib.request.Request(
            userinfo_url,
            headers={'Authorization': f'Bearer {access_token}'}
        )
        with urllib.request.urlopen(user_req, timeout=10) as user_resp:
            profile = json.loads(user_resp.read().decode('utf-8'))

        email      = profile.get('email')
        name       = profile.get('name') or profile.get('given_name')
        google_id  = profile.get('sub')
        avatar_url = profile.get('picture')

        if not email:
            flash('Google did not return an email address. Please try a different account.', 'danger')
            return redirect(url_for('auth.login'))

        # Step 3: Resolve user record + set session + RBAC dispatch
        user, dest = _login_or_register_google_user(email, name, google_id, avatar_url)

        role_label = {'Super Admin': 'Super Admin', 'Manager': 'Manager', 'Staff': 'Staff', 'Customer': 'Customer'}.get(user.user_role, user.user_role)
        flash(f'Welcome, {user.name}! Signed in as {role_label}.', 'success')
        return redirect(dest)

    except HTTPError as e:
        flash(f'Google sign-in failed (HTTP {e.code}). Please try again.', 'danger')
        return redirect(url_for('auth.login'))
    except Exception as e:
        flash(f'Google sign-in error: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))


@auth_bp.route('/auth/google/token', methods=['POST'])
def google_token_verify():
    """
    Optional: Verifies a Google Identity Services ID token (one-tap/popup flows).
    Returns JSON {status, redirect_url} for JavaScript-driven sign-in widgets.
    """
    payload = request.get_json(silent=True) or request.form
    token = payload.get('credential') or payload.get('id_token')
    if not token:
        return jsonify({'status': 'error', 'message': 'Missing Google credential token.'}), 400

    try:
        verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={urllib.parse.quote(token)}"
        req = urllib.request.Request(verify_url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            id_info = json.loads(resp.read().decode('utf-8'))

        email      = id_info.get('email')
        name       = id_info.get('name')
        google_id  = id_info.get('sub')
        avatar_url = id_info.get('picture')

        if not email:
            return jsonify({'status': 'error', 'message': 'Google token missing email claim.'}), 400

        user, dest = _login_or_register_google_user(email, name, google_id, avatar_url)
        return jsonify({'status': 'success', 'redirect_url': dest, 'role': user.user_role})

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Token verification failed: {str(e)}'}), 400


# ---------------------------------------------------------------------------
# Session Logout
# ---------------------------------------------------------------------------

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been signed out successfully.', 'info')
    return redirect(url_for('auth.login'))


# ---------------------------------------------------------------------------
# Manager-only: Account Provisioning API
# ---------------------------------------------------------------------------

@auth_bp.route('/manager/accounts', methods=['POST'])
@api_roles_required(Role.MANAGER)
def create_account():
    """
    Manager-only endpoint to provision Staff or Manager accounts.
    Staff accounts are pre-registered with their Gmail address so that
    when they sign in with Google, the system finds their record and grants
    the correct role automatically.
    """
    payload = request.get_json(silent=True) or request.form
    name  = (payload.get('name') or '').strip()
    email = (payload.get('email') or '').strip().lower()
    role  = (payload.get('role') or Role.CUSTOMER).strip()

    current_actor_role = session.get('user_role')
    allowed_roles = [Role.STAFF, Role.CUSTOMER, Role.MANAGER]
    if current_actor_role == Role.SUPER_ADMIN:
        allowed_roles.append(Role.SUPER_ADMIN)

    if not name or not email:
        return jsonify({'status': 'error', 'message': 'Name and email are required.'}), 400
    if role not in allowed_roles:
        return jsonify({'status': 'error', 'message': f'Invalid role selection.'}), 400
    if not re.fullmatch(r'^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$', email):
        return jsonify({'status': 'error', 'message': 'Invalid email address format.'}), 400

    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            return jsonify({'status': 'error', 'message': 'An account with that email already exists.'}), 409

        user = User(
            name=name,
            email=email,
            password=None,   # No password — Google-only sign-in
            user_role=role,
            failed_login_attempts=0
        )
        db.add(user)
        db.flush()
        user_data = {
            'user_id': user.user_id,
            'name': user.name,
            'email': user.email,
            'role': user.user_role
        }
        db.commit()

        AuditService.log(
            action=AuditAction.USER_PROVISIONED,
            entity_type='User',
            entity_id=str(user.user_id),
            details=f"Pre-registered {role} account for {name} ({email})"
        )

        return jsonify({
            'status': 'success',
            'message': f'{role} account created for {name}. They can now sign in directly with Google.',
            'data': user_data
        }), 201

    except Exception as error:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(error)}), 500
    finally:
        db.close()


@auth_bp.route('/api/manager/users')
@api_roles_required(Role.MANAGER)
def list_users():
    """Returns a page of registered users, roles, and OAuth connection status."""
    page = max(request.args.get('page', 1, type=int) or 1, 1)
    per_page = min(max(request.args.get('per_page', 10, type=int) or 10, 1), 50)
    db = SessionLocal()
    try:
        total = db.query(User).count()
        users = db.query(User).order_by(
            case(
                (User.user_role == Role.SUPER_ADMIN, 1),
                (User.user_role == Role.MANAGER, 2),
                (User.user_role == Role.STAFF, 3),
                else_=4
            ),
            User.user_id.desc()
        ).offset((page - 1) * per_page).limit(per_page).all()
        data = [{
            'user_id': u.user_id,
            'name': u.name,
            'email': u.email,
            'role': u.user_role,
            'avatar_url': u.avatar_url,
            'is_google_linked': bool(u.google_id),
        } for u in users]
        return jsonify({
            'status': 'success', 'data': data,
            'page': page, 'per_page': per_page, 'total': total,
            'has_next': page * per_page < total,
        })
    finally:
        db.close()


@auth_bp.route('/api/manager/users/<int:user_id>/role', methods=['POST'])
@api_roles_required(Role.MANAGER)
def change_user_role(user_id):
    """Allows Super Admin/Manager to change a user's role (promote/demote)."""
    payload = request.get_json(silent=True) or request.form
    new_role = (payload.get('role') or '').strip()

    current_actor_role = session.get('user_role')
    allowed_roles = [Role.STAFF, Role.CUSTOMER, Role.MANAGER]
    if current_actor_role == Role.SUPER_ADMIN:
        allowed_roles.append(Role.SUPER_ADMIN)

    if new_role not in allowed_roles:
        return jsonify({'status': 'error', 'message': f'Invalid role: {new_role}'}), 400

    db = SessionLocal()
    try:
        target_user = db.get(User, user_id)
        if not target_user:
            return jsonify({'status': 'error', 'message': 'User not found.'}), 404

        # Only a Super Admin can modify another Super Admin or promote anyone to Super Admin
        if target_user.user_role == Role.SUPER_ADMIN and current_actor_role != Role.SUPER_ADMIN:
            return jsonify({'status': 'error', 'message': 'Only a Super Admin can modify Super Admin accounts.'}), 403

        if new_role == Role.SUPER_ADMIN and current_actor_role != Role.SUPER_ADMIN:
            return jsonify({'status': 'error', 'message': 'Only a Super Admin can promote someone to Super Admin.'}), 403

        old_role = target_user.user_role
        target_user.user_role = new_role
        db.commit()

        AuditService.log(
            action=AuditAction.USER_ROLE_CHANGED,
            entity_type='User',
            entity_id=str(target_user.user_id),
            details=f"Changed role of {target_user.name} ({target_user.email}) from {old_role} to {new_role}"
        )

        return jsonify({
            'status': 'success',
            'message': f'Role updated to {new_role} for {target_user.name}.',
            'data': {'user_id': target_user.user_id, 'role': target_user.user_role}
        })
    except Exception as e:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        db.close()


@auth_bp.route('/api/auth/switch-role', methods=['POST'])
def switch_active_role():
    """Allows Super Admin and Manager to switch their active session view/role."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Authentication required.'}), 401

    data = request.get_json(silent=True) or {}
    target_role = data.get('role')

    valid_roles = [Role.SUPER_ADMIN, Role.MANAGER, Role.STAFF, Role.CUSTOMER]
    if target_role not in valid_roles:
        return jsonify({'status': 'error', 'message': f'Invalid role: {target_role}'}), 400

    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found.'}), 404

        base_role = user.user_role
        session['base_user_role'] = base_role

        # Strict security rule: ONLY Super Admin can switch perspectives.
        # Managers and Staff are NOT permitted to switch as user/customer or any other role.
        if base_role != Role.SUPER_ADMIN:
            return jsonify({
                'status': 'error',
                'message': 'Only Super Admins can switch view perspectives. Staff and Managers cannot switch roles.'
            }), 403

        previous_role = session.get('user_role', base_role)
        session['user_role'] = target_role

        AuditService.log(
            action=AuditAction.ROLE_VIEW_SWITCHED,
            entity_type='User',
            entity_id=str(user.user_id),
            details=f"{user.name} switched view mode from {previous_role} to {target_role} (Base Role: {base_role})",
            user_id=user.user_id,
            user_name=user.name,
            user_email=user.email,
            user_role=target_role
        )

        redirect_url = get_role_home(target_role)
        return jsonify({
            'status': 'success',
            'message': f'Switched view mode to {target_role}',
            'active_role': target_role,
            'base_role': base_role,
            'redirect_url': redirect_url
        })
    finally:
        db.close()

