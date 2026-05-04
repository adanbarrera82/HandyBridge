"""
Route protection decorators for HandyBridge.
Import these in blueprints instead of importing from app.py to avoid circular imports.
"""

from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('account_type') != 'admin':
            flash('Access denied.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated


def provider_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('account_type') not in ('provider', 'both', 'admin'):
            flash('Access denied. A provider account is required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated
