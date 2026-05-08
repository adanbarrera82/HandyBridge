"""
Client routes: Dashboard, Service Requests, Bookings, Reviews, Payments
"""

from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.db import get_db_connection
from utils.decorators import login_required

client_bp = Blueprint('client', __name__)


@client_bp.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    user_id = session['user_id']

    cursor.execute("""
        SELECT COUNT(*) as count FROM Booking
        WHERE Client_ID = %s AND Status IN ('pending', 'confirmed', 'in_progress')
    """, (user_id,))
    active_bookings = cursor.fetchone()['count']

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


@client_bp.route('/request/<int:request_id>/cancel', methods=['POST'])
@login_required
def cancel_request(request_id):
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Single atomic update: ownership + cancellable status enforced in WHERE clause
        cursor.execute("""
            UPDATE ServiceRequest
            SET Status = 'cancelled'
            WHERE Request_ID = %s
              AND Client_ID = %s
              AND Status IN ('open', 'in_progress')
        """, (request_id, session['user_id']))
        rows = cursor.rowcount

        if rows == 0:
            # Diagnose why nothing was updated
            cursor.execute(
                "SELECT Status FROM ServiceRequest WHERE Request_ID = %s AND Client_ID = %s",
                (request_id, session['user_id'])
            )
            rec = cursor.fetchone()
            if not rec:
                flash('Request not found.', 'danger')
            elif rec['Status'] in ('matched', 'completed'):
                flash('Cannot cancel a request that has already been matched or completed.', 'warning')
            elif rec['Status'] == 'cancelled':
                flash('This request is already cancelled.', 'info')
            else:
                flash('Unable to cancel this request.', 'danger')
        else:
            conn.commit()
            flash('Service request cancelled successfully.', 'success')

    except Exception:
        conn.rollback()
        flash('An error occurred. Please try again.', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('client.service_request'))


@client_bp.route('/request', methods=['GET', 'POST'])
@login_required
def service_request():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        try:
            cursor.execute("""
                INSERT INTO ServiceRequest (Client_ID, Category_ID, Title, Description,
                                           Urgency, Preferred_Date, Preferred_Time,
                                           Service_Address, Service_City, Service_State, Service_Zip)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                session['user_id'],
                request.form['category_id'],
                request.form['title'],
                request.form.get('description', ''),
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
        except Exception:
            conn.rollback()
            flash('Error submitting request. Please try again.', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('client.service_request'))

    cursor.execute("SELECT * FROM ServiceCategory ORDER BY Category_Name")
    categories = cursor.fetchall()

    cursor.execute("""
        SELECT sr.*, sc.Category_Name
        FROM ServiceRequest sr
        JOIN ServiceCategory sc ON sr.Category_ID = sc.Category_ID
        WHERE sr.Client_ID = %s
        ORDER BY sr.Date_Created DESC LIMIT 20
    """, (session['user_id'],))
    past_requests = cursor.fetchall()

    cursor.execute(
        "SELECT Street_Address, City, State, Zip_Code FROM User WHERE User_ID = %s",
        (session['user_id'],)
    )
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('client/service_request.html',
                           categories=categories,
                           past_requests=past_requests,
                           user=user)


@client_bp.route('/bookings')
@login_required
def bookings():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.*, u.First_Name as provider_first, u.Last_Name as provider_last,
               sc.Category_Name,
               r.Review_ID as review_id
        FROM Booking b
        JOIN User u ON b.Provider_ID = u.User_ID
        LEFT JOIN ServiceListing sl ON b.Listing_ID = sl.Listing_ID
        LEFT JOIN ServiceCategory sc ON sl.Category_ID = sc.Category_ID
        LEFT JOIN Review r ON r.Booking_ID = b.Booking_ID AND r.Reviewer_ID = %s
        WHERE b.Client_ID = %s
        ORDER BY b.Scheduled_Date DESC
    """, (session['user_id'], session['user_id']))
    bookings_list = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('client/bookings.html', bookings=bookings_list)


@client_bp.route('/booking/<int:booking_id>/update', methods=['POST'])
@login_required
def update_booking(booking_id):
    new_status = request.form.get('status')
    allowed_transitions = {
        'cancelled': ('pending', 'confirmed'),
        'completed': ('in_progress',),
    }
    if new_status not in allowed_transitions:
        flash('Invalid action.', 'danger')
        return redirect(url_for('client.bookings'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT Status FROM Booking WHERE Booking_ID = %s AND Client_ID = %s",
        (booking_id, session['user_id'])
    )
    booking = cursor.fetchone()

    if not booking:
        flash('Booking not found.', 'danger')
    elif booking['Status'] not in allowed_transitions[new_status]:
        flash('Cannot perform this action on the current booking status.', 'danger')
    else:
        cursor.execute(
            "UPDATE Booking SET Status = %s WHERE Booking_ID = %s AND Client_ID = %s",
            (new_status, booking_id, session['user_id'])
        )
        conn.commit()
        flash('Booking cancelled.' if new_status == 'cancelled' else 'Booking marked as completed.', 'success')

    cursor.close()
    conn.close()
    return redirect(url_for('client.bookings'))


@client_bp.route('/booking/<int:booking_id>/review', methods=['GET', 'POST'])
@login_required
def review(booking_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT b.*, u.First_Name, u.Last_Name, sc.Category_Name
        FROM Booking b
        JOIN User u ON b.Provider_ID = u.User_ID
        LEFT JOIN ServiceListing sl ON b.Listing_ID = sl.Listing_ID
        LEFT JOIN ServiceCategory sc ON sl.Category_ID = sc.Category_ID
        WHERE b.Booking_ID = %s AND b.Client_ID = %s
    """, (booking_id, session['user_id']))
    booking = cursor.fetchone()

    if not booking:
        flash('Booking not found.', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('client.bookings'))

    if booking['Status'] != 'completed':
        flash('You can only review completed bookings.', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('client.bookings'))

    cursor.execute(
        "SELECT Review_ID FROM Review WHERE Booking_ID = %s AND Reviewer_ID = %s",
        (booking_id, session['user_id'])
    )
    if cursor.fetchone():
        flash('You have already reviewed this booking.', 'warning')
        cursor.close()
        conn.close()
        return redirect(url_for('client.bookings'))

    if request.method == 'POST':
        try:
            rating = int(request.form['rating'])
            if not (1 <= rating <= 5):
                raise ValueError
        except (ValueError, KeyError):
            flash('Rating must be a whole number between 1 and 5.', 'danger')
            cursor.close()
            conn.close()
            return render_template('client/review.html', booking=booking)

        comment = request.form.get('comment', '').strip()
        if len(comment) > 500:
            flash('Comment must be 500 characters or less.', 'danger')
            cursor.close()
            conn.close()
            return render_template('client/review.html', booking=booking)

        cursor.execute("""
            INSERT INTO Review (Booking_ID, Reviewer_ID, Reviewee_ID, Rating, Comment)
            VALUES (%s, %s, %s, %s, %s)
        """, (booking_id, session['user_id'], booking['Provider_ID'], rating, comment))
        conn.commit()
        flash('Review submitted successfully!', 'success')
        cursor.close()
        conn.close()
        return redirect(url_for('client.bookings'))

    cursor.close()
    conn.close()
    return render_template('client/review.html', booking=booking)


@client_bp.route('/booking/<int:booking_id>/pay', methods=['GET', 'POST'])
@login_required
def payment(booking_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("""
            SELECT Total_Amount FROM Booking
            WHERE Booking_ID = %s AND Client_ID = %s
        """, (booking_id, session['user_id']))
        booking = cursor.fetchone()

        if not booking:
            flash('Booking not found.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('client.bookings'))

        cursor.execute("""
            INSERT INTO Payment (Booking_ID, Amount, Payment_Method, Payment_Status)
            VALUES (%s, %s, %s, 'completed')
        """, (booking_id, booking['Total_Amount'], request.form['payment_method']))
        conn.commit()
        flash('Payment processed successfully!', 'success')
        cursor.close()
        conn.close()
        return redirect(url_for('client.bookings'))

    cursor.execute("""
        SELECT b.*, u.First_Name, u.Last_Name
        FROM Booking b JOIN User u ON b.Provider_ID = u.User_ID
        WHERE b.Booking_ID = %s AND b.Client_ID = %s
    """, (booking_id, session['user_id']))
    booking = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('client/payment.html', booking=booking)


@client_bp.route('/provider/<int:provider_id>/book', methods=['POST'])
@login_required
def book_provider(provider_id):
    # Only client (or both) account types may book
    if session.get('account_type') not in ('client', 'both'):
        flash('Only client accounts can book services.', 'danger')
        return redirect(url_for('provider_profile', provider_id=provider_id))

    # Can't book yourself
    if session['user_id'] == provider_id:
        flash('You cannot book yourself.', 'danger')
        return redirect(url_for('provider_profile', provider_id=provider_id))

    listing_id   = request.form.get('listing_id', '').strip()
    date_str     = request.form.get('service_date', '').strip()
    start_str    = request.form.get('start_time', '').strip()
    duration_str = request.form.get('duration', '').strip()
    notes        = request.form.get('notes', '').strip()

    if not all([listing_id, date_str, start_str, duration_str]):
        flash('Please fill in all required fields.', 'danger')
        return redirect(url_for('provider_profile', provider_id=provider_id))

    # Validate date — must be today or future
    try:
        service_date = date.fromisoformat(date_str)
        if service_date < date.today():
            flash('Service date cannot be in the past.', 'danger')
            return redirect(url_for('provider_profile', provider_id=provider_id))
    except ValueError:
        flash('Invalid service date.', 'danger')
        return redirect(url_for('provider_profile', provider_id=provider_id))

    # Validate duration (1–8 hours)
    try:
        duration = int(duration_str)
        if not (1 <= duration <= 8):
            raise ValueError
    except ValueError:
        flash('Please select a valid duration.', 'danger')
        return redirect(url_for('provider_profile', provider_id=provider_id))

    if len(notes) > 500:
        flash('Additional details must be 500 characters or less.', 'danger')
        return redirect(url_for('provider_profile', provider_id=provider_id))

    # Calculate end time; reject if it crosses midnight
    try:
        start_dt = datetime.strptime(start_str, '%H:%M')
        end_dt   = start_dt + timedelta(hours=duration)
        if end_dt.date() > start_dt.date():
            flash('Start time + duration extends past midnight. Please adjust.', 'danger')
            return redirect(url_for('provider_profile', provider_id=provider_id))
        end_str = end_dt.strftime('%H:%M')
    except ValueError:
        flash('Invalid start time.', 'danger')
        return redirect(url_for('provider_profile', provider_id=provider_id))

    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Verify provider exists
        cursor.execute("""
            SELECT User_ID, First_Name, Last_Name FROM User
            WHERE User_ID = %s AND Account_Type IN ('provider', 'both')
        """, (provider_id,))
        provider = cursor.fetchone()
        if not provider:
            flash('Provider not found.', 'danger')
            return redirect(url_for('home'))

        # Verify listing belongs to this provider and is active
        cursor.execute("""
            SELECT Listing_ID, Price_Per_Hour, Price_Per_Job
            FROM ServiceListing
            WHERE Listing_ID = %s AND Provider_ID = %s AND Is_Active = TRUE
        """, (listing_id, provider_id))
        listing = cursor.fetchone()
        if not listing:
            flash('Selected service is not available.', 'danger')
            return redirect(url_for('provider_profile', provider_id=provider_id))

        # Compute total: hourly × duration, or flat rate if no hourly price
        if listing['Price_Per_Hour']:
            total_amount = float(listing['Price_Per_Hour']) * duration
        elif listing['Price_Per_Job']:
            total_amount = float(listing['Price_Per_Job'])
        else:
            total_amount = None

        cursor.execute("""
            INSERT INTO Booking
                (Client_ID, Provider_ID, Listing_ID, Request_ID,
                 Scheduled_Date, Scheduled_Start_Time, Scheduled_End_Time,
                 Status, Total_Amount, Notes, Date_Created)
            VALUES (%s, %s, %s, NULL, %s, %s, %s, 'pending', %s, %s, NOW())
        """, (
            session['user_id'],
            provider_id,
            listing_id,
            service_date,
            start_str,
            end_str,
            total_amount,
            notes or None,
        ))
        conn.commit()

        pname = f"{provider['First_Name']} {provider['Last_Name']}"
        flash(
            f'Booking request sent to {pname}! '
            'They will confirm shortly — check your bookings page to track the status.',
            'success'
        )
        return redirect(url_for('client.bookings'))

    except Exception:
        conn.rollback()
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('provider_profile', provider_id=provider_id))
    finally:
        cursor.close()
        conn.close()


@client_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
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
