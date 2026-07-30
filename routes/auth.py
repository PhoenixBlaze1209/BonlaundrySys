# routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from config.database import SessionLocal
from models.schemas import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'Customer') # Default to customer

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