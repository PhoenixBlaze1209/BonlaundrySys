# routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from config.database import SessionLocal
from models.schemas import User

auth_bp = Blueprint('auth', __name__)

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
        new_user = User(name=name, email=email, password=password, user_role=role)
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
        
        db = SessionLocal()
        user = db.query(User).filter(User.email == email, User.password == password).first()
        db.close()
        
        if user:
            # Save user information in session state
            session['user_id'] = user.user_id
            session['user_name'] = user.name
            session['user_role'] = user.user_role
            
            # Route accordingly based on RBAC rules
            if user.user_role == 'Manager':
                return redirect(url_for('dashboard.manager_home'))
            elif user.user_role == 'Staff':
                return redirect(url_for('dashboard.staff_home'))
            else:
                return redirect(url_for('dashboard.customer_home'))
        else:
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
        user = User(name=name, email=email, password=password, user_role=role)
        db.add(user)
        db.commit()
        return jsonify({'status': 'success', 'message': 'Account created.', 'data': {
            'user_id': user.user_id, 'name': user.name, 'email': user.email, 'role': user.user_role
        }}), 201
    except Exception as error:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(error)}), 500
    finally:
        db.close()
