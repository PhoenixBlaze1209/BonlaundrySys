# services/rbac.py
"""
Role-Based Access Control (RBAC) Module for Bon Laundry Station.
Provides centralized role constants, hierarchy evaluation, route decorators,
and destination URL resolvers.
"""

from functools import wraps
from flask import session, redirect, url_for, flash, jsonify, request


class Role:
    SUPER_ADMIN = 'Super Admin'
    MANAGER     = 'Manager'
    STAFF       = 'Staff'
    CUSTOMER    = 'Customer'

    ALL = (SUPER_ADMIN, MANAGER, STAFF, CUSTOMER)


# Hierarchical capabilities: Super Admin & Manager can inspect staff workspaces
ROLE_HIERARCHY = {
    Role.SUPER_ADMIN: {Role.SUPER_ADMIN, Role.MANAGER, Role.STAFF},
    Role.MANAGER:     {Role.MANAGER, Role.STAFF},
    Role.STAFF:       {Role.STAFF},
    Role.CUSTOMER:    {Role.CUSTOMER},
}


def get_current_user_role():
    """Returns the role of the currently authenticated user, or None."""
    return session.get('user_role')


def is_authenticated():
    """Checks whether the current session has an active user ID."""
    return bool(session.get('user_id'))


def has_role(*allowed_roles):
    """
    Evaluates whether the current user has any of the allowed roles,
    respecting managerial hierarchy (Manager can access Staff views).
    """
    user_role = get_current_user_role()
    if not user_role:
        return False
    user_capabilities = ROLE_HIERARCHY.get(user_role, {user_role})
    return any(role in user_capabilities for role in allowed_roles)


def get_role_home(role=None):
    """
    Returns the canonical landing URL for a given role.
    If role is not specified, uses the current session role.
    """
    role = role or get_current_user_role()
    if role in (Role.SUPER_ADMIN, Role.MANAGER):
        return url_for('dashboard.manager_home')
    elif role == Role.STAFF:
        return url_for('dashboard.staff_home')
    elif role == Role.CUSTOMER:
        return url_for('dashboard.customer_home')
    return url_for('auth.login')


def login_required(f):
    """Decorator ensuring user is authenticated before accessing a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            flash('Please sign in to access this workspace.', 'info')
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def roles_required(*allowed_roles):
    """
    Decorator requiring authentication and at least one of the specified roles.
    If unauthorized, redirects user to their own authorized role home with a warning.
    Managers automatically inherit access to Staff-permitted views.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not is_authenticated():
                flash('Please sign in to access this workspace.', 'info')
                return redirect(url_for('auth.login', next=request.path))

            user_role = get_current_user_role()
            if not has_role(*allowed_roles):
                allowed_names = ", ".join(allowed_roles)
                flash(
                    f'Access Denied: [{allowed_names}] access required. '
                    f'Your role is {user_role}.',
                    'danger'
                )
                return redirect(get_role_home(user_role))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def api_roles_required(*allowed_roles):
    """
    Decorator for JSON API endpoints enforcing authentication and role permissions.
    Returns HTTP 401 if unauthenticated, HTTP 403 if unauthorized.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not is_authenticated():
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication required. Please sign in.'
                }), 401

            user_role = get_current_user_role()
            if not has_role(*allowed_roles):
                allowed_names = ", ".join(allowed_roles)
                return jsonify({
                    'status': 'error',
                    'message': f'Forbidden: [{allowed_names}] access required. Your role is {user_role}.'
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator
