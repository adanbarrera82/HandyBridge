"""
Admin routes: Dashboard, User Management, Category Management, Reports
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.db import get_db_connection

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as count FROM User")
    user_count = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM Booking")
    booking_count = cursor.fetchone()['count']

    cursor.execute("SELECT COALESCE(SUM(Amount), 0) as total FROM Payment WHERE Payment_Status='completed'")
    total_revenue = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as count FROM ServiceCategory")
    category_count = cursor.fetchone()['count']

    cursor.close()
    conn.close()

    return render_template('admin/dashboard.html',
                         user_count=user_count,
                         booking_count=booking_count,
                         total_revenue=total_revenue,
                         category_count=category_count)


@admin_bp.route('/users')
def users():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM User ORDER BY Date_Registered DESC")
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM User WHERE User_ID = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash('User deleted.', 'info')
    return redirect(url_for('admin.users'))


@admin_bp.route('/categories', methods=['GET', 'POST'])
def categories():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("""
            INSERT INTO ServiceCategory (Category_Name, Description)
            VALUES (%s, %s)
        """, (request.form['category_name'], request.form.get('description', '')))
        conn.commit()
        flash('Category created!', 'success')

    cursor.execute("SELECT * FROM ServiceCategory ORDER BY Category_Name")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin/categories.html', categories=categories)


@admin_bp.route('/categories/<int:cat_id>/delete', methods=['POST'])
def delete_category(cat_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ServiceCategory WHERE Category_ID = %s", (cat_id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Category deleted.', 'info')
    return redirect(url_for('admin.categories'))
