"""
Provider routes: Dashboard, Listings, Availability, Bookings, Earnings
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.db import get_db_connection
from utils.decorators import provider_required

provider_bp = Blueprint('provider', __name__)


@provider_bp.route('/dashboard')
@provider_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    user_id = session['user_id']

    cursor.execute("""
        SELECT COUNT(*) as count FROM Booking
        WHERE Provider_ID = %s AND Status IN ('pending', 'confirmed', 'in_progress')
    """, (user_id,))
    active_bookings = cursor.fetchone()['count']

    cursor.execute("""
        SELECT COUNT(*) as count FROM ServiceListing
        WHERE Provider_ID = %s AND Is_Active = TRUE
    """, (user_id,))
    active_listings = cursor.fetchone()['count']

    cursor.execute("""
        SELECT COALESCE(SUM(p.Amount), 0) as total
        FROM Payment p JOIN Booking b ON p.Booking_ID = b.Booking_ID
        WHERE b.Provider_ID = %s AND p.Payment_Status = 'completed'
    """, (user_id,))
    total_earnings = cursor.fetchone()['total']

    cursor.execute("""
        SELECT b.*, u.First_Name as client_first, u.Last_Name as client_last
        FROM Booking b JOIN User u ON b.Client_ID = u.User_ID
        WHERE b.Provider_ID = %s
        ORDER BY b.Date_Created DESC LIMIT 5
    """, (user_id,))
    recent_bookings = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('provider/dashboard.html',
                           active_bookings=active_bookings,
                           active_listings=active_listings,
                           total_earnings=total_earnings,
                           recent_bookings=recent_bookings)


@provider_bp.route('/listings')
@provider_required
def listings():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT sl.*, sc.Category_Name
        FROM ServiceListing sl
        JOIN ServiceCategory sc ON sl.Category_ID = sc.Category_ID
        WHERE sl.Provider_ID = %s
        ORDER BY sl.Date_Created DESC
    """, (session['user_id'],))
    listings = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('provider/listings.html', listings=listings)


@provider_bp.route('/listings/new', methods=['GET', 'POST'])
@provider_required
def new_listing():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("""
            INSERT INTO ServiceListing (Provider_ID, Category_ID, Title, Description,
                                       Price_Per_Hour, Price_Per_Job, Service_Radius_Miles)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            session['user_id'],
            request.form['category_id'],
            request.form['title'],
            request.form['description'],
            request.form.get('price_per_hour') or None,
            request.form.get('price_per_job') or None,
            request.form.get('service_radius') or None,
        ))
        conn.commit()
        flash('Listing created!', 'success')
        cursor.close()
        conn.close()
        return redirect(url_for('provider.listings'))

    cursor.execute("SELECT * FROM ServiceCategory ORDER BY Category_Name")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('provider/new_listing.html', categories=categories)


@provider_bp.route('/listings/<int:listing_id>/edit', methods=['GET', 'POST'])
@provider_required
def edit_listing(listing_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("""
            UPDATE ServiceListing SET Title=%s, Description=%s, Price_Per_Hour=%s,
                Price_Per_Job=%s, Service_Radius_Miles=%s, Is_Active=%s
            WHERE Listing_ID = %s AND Provider_ID = %s
        """, (
            request.form['title'], request.form['description'],
            request.form.get('price_per_hour') or None,
            request.form.get('price_per_job') or None,
            request.form.get('service_radius') or None,
            1 if request.form.get('is_active') else 0,
            listing_id, session['user_id']
        ))
        conn.commit()
        flash('Listing updated!', 'success')
        cursor.close()
        conn.close()
        return redirect(url_for('provider.listings'))

    cursor.execute("""
        SELECT sl.*, sc.Category_Name FROM ServiceListing sl
        JOIN ServiceCategory sc ON sl.Category_ID = sc.Category_ID
        WHERE sl.Listing_ID = %s AND sl.Provider_ID = %s
    """, (listing_id, session['user_id']))
    listing = cursor.fetchone()

    cursor.execute("SELECT * FROM ServiceCategory ORDER BY Category_Name")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('provider/edit_listing.html', listing=listing, categories=categories)


@provider_bp.route('/listings/<int:listing_id>/delete', methods=['POST'])
@provider_required
def delete_listing(listing_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE ServiceListing SET Is_Active = FALSE
        WHERE Listing_ID = %s AND Provider_ID = %s
    """, (listing_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Listing deactivated.', 'info')
    return redirect(url_for('provider.listings'))


@provider_bp.route('/availability', methods=['GET', 'POST'])
@provider_required
def availability():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("""
            INSERT INTO Availability (Provider_ID, Day_Of_Week, Start_Time, End_Time)
            VALUES (%s, %s, %s, %s)
        """, (session['user_id'], request.form['day_of_week'],
              request.form['start_time'], request.form['end_time']))
        conn.commit()
        flash('Availability slot added!', 'success')

    cursor.execute("""
        SELECT * FROM Availability WHERE Provider_ID = %s
        ORDER BY FIELD(Day_Of_Week, 'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'), Start_Time
    """, (session['user_id'],))
    slots = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('provider/availability.html', slots=slots)


@provider_bp.route('/availability/<int:slot_id>/delete', methods=['POST'])
@provider_required
def delete_availability(slot_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Availability WHERE Availability_ID = %s AND Provider_ID = %s",
                   (slot_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Availability slot removed.', 'info')
    return redirect(url_for('provider.availability'))


@provider_bp.route('/bookings')
@provider_required
def bookings():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.*, u.First_Name as client_first, u.Last_Name as client_last,
               u.Phone as client_phone
        FROM Booking b JOIN User u ON b.Client_ID = u.User_ID
        WHERE b.Provider_ID = %s
        ORDER BY b.Scheduled_Date DESC
    """, (session['user_id'],))
    bookings = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('provider/bookings.html', bookings=bookings)


@provider_bp.route('/bookings/<int:booking_id>/update', methods=['POST'])
@provider_required
def update_booking(booking_id):
    new_status = request.form['status']
    conn = get_db_connection()
    cursor = conn.cursor()

    if new_status == 'in_progress':
        cursor.execute("""
            UPDATE Booking SET Status = %s, Actual_Start_Time = NOW()
            WHERE Booking_ID = %s AND Provider_ID = %s
        """, (new_status, booking_id, session['user_id']))
    elif new_status == 'completed':
        cursor.execute("""
            UPDATE Booking SET Status = %s, Actual_End_Time = NOW()
            WHERE Booking_ID = %s AND Provider_ID = %s
        """, (new_status, booking_id, session['user_id']))
    else:
        cursor.execute("""
            UPDATE Booking SET Status = %s
            WHERE Booking_ID = %s AND Provider_ID = %s
        """, (new_status, booking_id, session['user_id']))

    conn.commit()
    cursor.close()
    conn.close()

    flash(f'Booking status updated to {new_status}.', 'success')
    return redirect(url_for('provider.bookings'))


@provider_bp.route('/earnings')
@provider_required
def earnings():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, b.Scheduled_Date, u.First_Name, u.Last_Name
        FROM Payment p
        JOIN Booking b ON p.Booking_ID = b.Booking_ID
        JOIN User u ON b.Client_ID = u.User_ID
        WHERE b.Provider_ID = %s
        ORDER BY p.Transaction_Date DESC
    """, (session['user_id'],))
    payments = cursor.fetchall()

    cursor.execute("""
        SELECT COALESCE(SUM(p.Amount), 0) as total
        FROM Payment p JOIN Booking b ON p.Booking_ID = b.Booking_ID
        WHERE b.Provider_ID = %s AND p.Payment_Status = 'completed'
    """, (session['user_id'],))
    total = cursor.fetchone()['total']

    cursor.close()
    conn.close()

    return render_template('provider/earnings.html', payments=payments, total=total)
