"""
Account management routes: Delete Account, Forgot Password, Reset Password
"""

import secrets
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.db import get_db_connection
from utils.auth import hash_password, verify_password
from utils.decorators import login_required
from utils.email import send_reset_email

account_bp = Blueprint('account', __name__)


@account_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    password = request.form.get('password', '')
    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Password_Hash FROM User WHERE User_ID = %s", (user_id,))
    user = cursor.fetchone()

    if not user or not verify_password(password, user['Password_Hash']):
        flash('Incorrect password. Your account was not deleted.', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('client.settings'))

    # CASCADE on the User FK handles all related records automatically
    cursor.execute("DELETE FROM User WHERE User_ID = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

    print(f"[ACCOUNT] User {user_id} deleted their account.")
    session.clear()
    flash('Your account has been permanently deleted.', 'info')
    return redirect(url_for('home'))


@account_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT User_ID FROM User WHERE Email = %s", (email,))
        user = cursor.fetchone()

        if user:
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=1)
            cursor.execute("""
                INSERT INTO PasswordReset (User_ID, Token, Expires_At)
                VALUES (%s, %s, %s)
            """, (user['User_ID'], token, expires_at))
            conn.commit()

            reset_url = url_for('account.reset_password', token=token, _external=True)
            send_reset_email(email, reset_url)

        cursor.close()
        conn.close()

        # Always show the same message — never reveal whether an email exists
        flash('If an account with that email exists, a reset link has been sent. Check your inbox.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('public/forgot_password.html')


@account_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    token = request.args.get('token') or request.form.get('token', '')

    if not token:
        flash('Invalid reset link.', 'danger')
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM PasswordReset
        WHERE Token = %s AND Is_Used = FALSE AND Expires_At > NOW()
    """, (token,))
    reset = cursor.fetchone()

    if not reset:
        cursor.close()
        conn.close()
        flash('This reset link is invalid or has expired. Please request a new one.', 'danger')
        return redirect(url_for('account.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        errors = []
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            cursor.close()
            conn.close()
            return render_template('public/reset_password.html', token=token)

        hashed = hash_password(password)
        cursor.execute("UPDATE User SET Password_Hash = %s WHERE User_ID = %s",
                       (hashed, reset['User_ID']))
        cursor.execute("UPDATE PasswordReset SET Is_Used = TRUE WHERE Reset_ID = %s",
                       (reset['Reset_ID'],))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Password updated successfully. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    cursor.close()
    conn.close()
    return render_template('public/reset_password.html', token=token)
