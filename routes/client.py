"""
Client routes: Dashboard, Service Requests, Bookings, Reviews, Payments
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.db import get_db_connection

client_bp = Blueprint('client', __name__)


@client_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    user_id = session['user_id']

    # Get active bookings count
    cursor.execute("""
        SELECT COUNT(*) as count FROM Booking
        WHERE Client_ID = %s AND Status IN ('pending', 'confirmed', 'in_progress')
    """, (user_id,))
    active_bookings = cursor.fetchone()['count']

    # Get recent bookings
    cursor.execute("""
        SELECT b.*, u.First_Name as provider_first, u.Last_Name as provider_last,
               sc.Category_Name
        FROM Booking b
        JOIN User u ON b.Provider_ID = u.User_ID
        LEFT JOIN ServiceListing sl ON b.Listing_ID = sl.Listing_ID
        LEFT JOIN ServiceCategory sc ON sl.Category_ID = sc.Category_ID
        WHERE b.Client_ID = %s
        ORDER BY b.Date_Created DESC LIMIT 5
    """, (user_id,))
    recent_bookings = cursor.fetchall()

    # Get unread notifications
    cursor.execute("""
        SELECT * FROM Notification
        WHERE User_ID = %s AND Is_Read = FALSE
        ORDER BY Date_Sent DESC LIMIT 5
    """, (user_id,))
    notifications = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('client/dashboard.html',
                         active_bookings=active_bookings,
                         recent_bookings=recent_bookings,
                         notifications=notifications)


@client_bp.route('/request', methods=['GET', 'POST'])
def service_request():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("""
            INSERT INTO ServiceRequest (Client_ID, Category_ID, Title, Description,
                                       Urgency, Preferred_Date, Preferred_Time,
                                       Service_Address, Service_City, Service_State, Service_Zip)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            session['user_id'],
            request.form['category_id'],
            request.form['title'],
            request.form['description'],
            request.form['urgency'],
            request.form.get('preferred_date') or None,
            request.form.get('preferred_time') or None,
            request.form['service_address'],
            request.form['service_city'],
            request.form['service_state'],
            request.form['service_zip'],
        ))
        conn.commit()
        flash('Service request submitted successfully!', 'success')
        cursor.close()
        conn.close()
        return redirect(url_for('client.dashboard'))

    # GET - show form
    cursor.execute("SELECT * FROM ServiceCategory ORDER BY Category_Name")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('client/service_request.html', categories=categories)


@client_bp.route('/bookings')
def bookings():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.*, u.First_Name as provider_first, u.Last_Name as provider_last,
               sc.Category_Name
        FROM Booking b
        JOIN User u ON b.Provider_ID = u.User_ID
        LEFT JOIN ServiceListing sl ON b.Listing_ID = sl.Listing_ID
        LEFT JOIN ServiceCategory sc ON sl.Category_ID = sc.Category_ID
        WHERE b.Client_ID = %s
        ORDER BY b.Scheduled_Date DESC
    """, (session['user_id'],))
    bookings = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('client/bookings.html', bookings=bookings)


@client_bp.route('/booking/<int:booking_id>/review', methods=['GET', 'POST'])
def review(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("""
            SELECT Provider_ID FROM Booking WHERE Booking_ID = %s AND Client_ID = %s
        """, (booking_id, session['user_id']))
        booking = cursor.fetchone()

        if booking:
            cursor.execute("""
                INSERT INTO Review (Booking_ID, Reviewer_ID, Reviewee_ID, Rating, Comment)
                VALUES (%s, %s, %s, %s, %s)
            """, (booking_id, session['user_id'], booking['Provider_ID'],
                  request.form['rating'], request.form.get('comment', '')))
            conn.commit()
            flash('Review submitted!', 'success')

        cursor.close()
        conn.close()
        return redirect(url_for('client.bookings'))

    # GET
    cursor.execute("""
        SELECT b.*, u.First_Name, u.Last_Name
        FROM Booking b JOIN User u ON b.Provider_ID = u.User_ID
        WHERE b.Booking_ID = %s AND b.Client_ID = %s
    """, (booking_id, session['user_id']))
    booking = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('client/review.html', booking=booking)


@client_bp.route('/booking/<int:booking_id>/pay', methods=['GET', 'POST'])
def payment(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("""
            INSERT INTO Payment (Booking_ID, Amount, Payment_Method, Payment_Status)
            VALUES (%s, %s, %s, 'completed')
        """, (booking_id, request.form['amount'], request.form['payment_method']))
        conn.commit()
        flash('Payment processed successfully!', 'success')
        cursor.close()
        conn.close()
        return redirect(url_for('client.bookings'))

    # GET
    cursor.execute("""
        SELECT b.*, u.First_Name, u.Last_Name
        FROM Booking b JOIN User u ON b.Provider_ID = u.User_ID
        WHERE b.Booking_ID = %s AND b.Client_ID = %s
    """, (booking_id, session['user_id']))
    booking = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('client/payment.html', booking=booking)


@client_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("""
            UPDATE User SET First_Name=%s, Last_Name=%s, Phone=%s,
                Street_Address=%s, City=%s, State=%s, Zip_Code=%s
            WHERE User_ID = %s
        """, (
            request.form['first_name'], request.form['last_name'],
            request.form['phone'], request.form['street_address'],
            request.form['city'], request.form['state'],
            request.form['zip_code'], session['user_id']
        ))
        conn.commit()
        session['first_name'] = request.form['first_name']
        session['last_name'] = request.form['last_name']
        flash('Profile updated!', 'success')

    cursor.execute("SELECT * FROM User WHERE User_ID = %s", (session['user_id'],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('client/settings.html', user=user)
