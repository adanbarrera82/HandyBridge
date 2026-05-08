"""
Admin routes: Dashboard, User Management, Category Management
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.db import get_db_connection
from utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
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
@admin_required
def users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM User ORDER BY Date_Registered DESC")
    users_list = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin/users.html', users=users_list)


@admin_bp.route('/users/<int:user_id>/update-type', methods=['POST'])
@admin_required
def update_user_type(user_id):
    if user_id == session['user_id']:
        flash('You cannot change your own account type.', 'danger')
        return redirect(url_for('admin.users'))

    new_type = request.form.get('account_type')
    if new_type not in ('client', 'provider', 'both', 'admin'):
        flash('Invalid account type.', 'danger')
        return redirect(url_for('admin.users'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE User SET Account_Type = %s WHERE User_ID = %s", (new_type, user_id))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Account type updated to {}.'.format(new_type), 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == session['user_id']:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM User WHERE User_ID = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash('User deleted.', 'info')
    return redirect(url_for('admin.users'))


@admin_bp.route('/categories', methods=['GET', 'POST'])
@admin_required
def categories():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form.get('category_name', '').strip()
        description = request.form.get('description', '').strip()
        edit_id = request.form.get('edit_id')
        if not name:
            flash('Category name is required.', 'danger')
        elif edit_id:
            cursor.execute("""
                UPDATE ServiceCategory SET Category_Name=%s, Description=%s
                WHERE Category_ID = %s
            """, (name, description, edit_id))
            conn.commit()
            flash('Category updated!', 'success')
        else:
            cursor.execute("""
                INSERT INTO ServiceCategory (Category_Name, Description)
                VALUES (%s, %s)
            """, (name, description))
            conn.commit()
            flash('Category created!', 'success')

    cursor.execute("""
        SELECT sc.*,
               COUNT(DISTINCT sl.Listing_ID) as listing_count,
               COUNT(DISTINCT CASE WHEN b.Status = 'completed' THEN b.Booking_ID END) as booking_count
        FROM ServiceCategory sc
        LEFT JOIN ServiceListing sl ON sl.Category_ID = sc.Category_ID
        LEFT JOIN Booking b ON b.Listing_ID = sl.Listing_ID
        GROUP BY sc.Category_ID
        ORDER BY sc.Category_Name
    """)
    cats = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin/categories.html', categories=cats)


@admin_bp.route('/categories/<int:cat_id>/delete', methods=['POST'])
@admin_required
def delete_category(cat_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as count FROM ServiceListing WHERE Category_ID = %s", (cat_id,))
    if cursor.fetchone()['count'] > 0:
        flash('Cannot delete a category that has existing listings.', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('admin.categories'))

    cursor.execute("DELETE FROM ServiceCategory WHERE Category_ID = %s", (cat_id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Category deleted.', 'info')
    return redirect(url_for('admin.categories'))
