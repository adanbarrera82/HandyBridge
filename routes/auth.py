"""
Authentication routes: Register, Login, Logout, Password Reset
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.db import get_db_connection
from utils.auth import hash_password, verify_password

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone = request.form.get('phone', '').strip()
        street_address = request.form.get('street_address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        account_type = request.form.get('account_type', 'client')

        # Validation
        errors = []
        if not first_name or not last_name:
            errors.append('First and last name are required.')
        if not email or '@' not in email:
            errors.append('A valid email address is required.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('public/register.html', form=request.form)

        # Check if email already exists
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT User_ID FROM User WHERE Email = %s", (email,))
        existing = cursor.fetchone()

        if existing:
            flash('An account with this email already exists.', 'danger')
            cursor.close()
            conn.close()
            return render_template('public/register.html', form=request.form)

        # Create user
        hashed = hash_password(password)
        cursor.execute("""
            INSERT INTO User (First_Name, Last_Name, Email, Password_Hash, Phone,
                            Street_Address, City, State, Zip_Code, Account_Type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (first_name, last_name, email, hashed, phone,
              street_address, city, state, zip_code, account_type))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('public/register.html', form={})


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM User WHERE Email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and verify_password(password, user['Password_Hash']):
            session['user_id'] = user['User_ID']
            session['first_name'] = user['First_Name']
            session['last_name'] = user['Last_Name']
            session['email'] = user['Email']
            session['account_type'] = user['Account_Type']

            flash(f"Welcome back, {user['First_Name']}!", 'success')

            # Redirect based on role
            if user['Account_Type'] == 'provider':
                return redirect(url_for('provider.dashboard'))
            elif user['Account_Type'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('client.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('public/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))
