# routes/auth.py
import re
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from config.database import SessionLocal
from models.schemas import User
from services.email_service import EmailService

auth_bp = Blueprint('auth', __name__)
GMAIL_PATTERN = re.compile(r'^[A-Za-z0-9._%+-]+@gmail\.com$')

def _valid_gmail(email):
    return bool(GMAIL_PATTERN.fullmatch((email or '').strip().lower()))

def _password_matches(user, password):
    return check_password_hash(user.password, password) if user.password.startswith(('pbkdf2:', 'scrypt:')) else user.password == password

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Authenticated operational users must use the manager provisioning flow;
    # staff cannot use the public registration screen to create accounts.
    if session.get('user_role') == 'Staff':
        flash('Account creation is available only to managers.', 'danger')
        return redirect(url_for('dashboard.staff_home'))
    if session.get('user_role') == 'Manager':
        return redirect(url_for('dashboard.manager_home'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        if not _valid_gmail(email):
            flash('Use a valid Gmail address.', 'danger'); return redirect(url_for('auth.register'))
        # Public registration can only create customer accounts. Staff and manager
        # roles must be provisioned by an authorized administrator.
        role = 'Customer'

        db = SessionLocal()
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            flash('Email already registered!', 'danger')
            db.close()
            return redirect(url_for('auth.register'))
        
        # In production, use werkzeug.security to hash passwords. Keeping plain text simple for local dev.
        new_user = User(name=name, email=email.lower(), password=generate_password_hash(password), user_role=role)
        db.add(new_user)
        db.commit()
        db.close()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not _valid_gmail(email):
            flash('Use a valid Gmail address.', 'danger'); return render_template('auth/login.html')
        
        db = SessionLocal()
        user = db.query(User).filter(User.email == email.lower()).first()
        
        if user and user.login_locked_until and user.login_locked_until > datetime.now():
            db.close(); flash('Too many failed attempts. Try again later.', 'danger'); return render_template('auth/login.html')
        if user and _password_matches(user, password):
            # Copy values while the ORM instance is still bound; commit expires
            # attributes and accessing them after close raises DetachedInstanceError.
            user_id, user_name, user_role = user.user_id, user.name, user.user_role
            if not user.password.startswith(('pbkdf2:', 'scrypt:')):
                user.password = generate_password_hash(password)
            user.failed_login_attempts, user.login_locked_until = 0, None
            db.commit(); db.close()
            # Save user information in session state
            session['user_id'] = user_id
            session['user_name'] = user_name
            session['user_role'] = user_role
            
            # Route accordingly based on RBAC rules
            if user_role == 'Manager':
                return redirect(url_for('dashboard.manager_home'))
            elif user_role == 'Staff':
                return redirect(url_for('dashboard.staff_home'))
            else:
                return redirect(url_for('dashboard.customer_home'))
        else:
            if user:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.login_locked_until = datetime.now() + timedelta(minutes=15)
                db.commit()
            db.close()
            flash('Invalid email or password.', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/manager/accounts', methods=['POST'])
def create_account():
    """Manager-only account provisioning; staff never receives this capability."""
    if session.get('user_role') != 'Manager':
        return jsonify({'status': 'error', 'message': 'Manager access is required.'}), 403

    payload = request.get_json(silent=True) or request.form
    name = (payload.get('name') or '').strip()
    email = (payload.get('email') or '').strip().lower()
    password = payload.get('password') or ''
    role = payload.get('role') or 'Customer'
    if not name or not email or not password or role not in ('Manager', 'Staff', 'Customer'):
        return jsonify({'status': 'error', 'message': 'Provide a name, email, password, and valid role.'}), 400

    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            return jsonify({'status': 'error', 'message': 'Email already registered.'}), 409
        if not _valid_gmail(email):
            return jsonify({'status': 'error', 'message': 'Use a valid Gmail address.'}), 400
        user = User(name=name, email=email, password=generate_password_hash(password), user_role=role)
        db.add(user)
        db.flush()
        user_data = {'user_id': user.user_id, 'name': user.name, 'email': user.email, 'role': user.user_role}
        db.commit()
        return jsonify({'status': 'success', 'message': 'Account created.', 'data': {
            **user_data
        }}), 201
    except Exception as error:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(error)}), 500
    finally:
        db.close()


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = (request.form.get('email') or '').lower()
        db = SessionLocal()
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.password_reset_token = secrets.token_urlsafe(24)
            user.password_reset_expires_at = datetime.now() + timedelta(minutes=30)
            db.commit(); EmailService.send_password_reset(user.email, user.password_reset_token)
        db.close(); flash('If the Gmail account exists, a reset token was sent.', 'info'); return redirect(url_for('auth.reset_password'))
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        token, password = request.form.get('token'), request.form.get('password')
        db = SessionLocal(); user = db.query(User).filter(User.password_reset_token == token).first()
        if not user or not user.password_reset_expires_at or user.password_reset_expires_at < datetime.now():
            db.close(); flash('Invalid or expired reset token.', 'danger'); return redirect(url_for('auth.reset_password'))
        user.password, user.password_reset_token, user.password_reset_expires_at = generate_password_hash(password), None, None
        user.failed_login_attempts, user.login_locked_until = 0, None
        db.commit(); db.close(); flash('Password reset. Please sign in.', 'success'); return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html')
