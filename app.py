"""
HandyBridge - Main Application
An Online Marketplace for Home Services
CSCI 4333 - Database Design and Implementation
"""

import os
import logging
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_talisman import Talisman

from routes.auth import auth_bp
from routes.client import client_bp
from routes.provider import provider_bp
from routes.admin import admin_bp
from routes.api import api_bp
from utils.extensions import csrf, limiter

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ============ SECRET KEY — crash fast if missing ============
_secret = os.environ.get('SECRET_KEY')
if not _secret:
    raise RuntimeError("SECRET_KEY environment variable is not set. "
                       "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\"")
app.secret_key = _secret

# ============ SESSION COOKIE SECURITY ============
_is_production = os.environ.get('FLASK_ENV') == 'production'
app.config.update(
    SESSION_COOKIE_SECURE=_is_production,   # HTTPS-only in production
    SESSION_COOKIE_HTTPONLY=True,            # no JS access to cookie
    SESSION_COOKIE_SAMESITE='Lax',           # blocks cross-site cookie sending
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
)

# ============ EXTENSIONS ============
csrf.init_app(app)
limiter.init_app(app)

# ============ SECURITY HEADERS ============
_csp = {
    'default-src': "'self'",
    'script-src': ["'self'", 'cdn.jsdelivr.net'],
    'style-src': ["'self'", 'cdn.jsdelivr.net', 'cdnjs.cloudflare.com'],
    'font-src': ["'self'", 'cdnjs.cloudflare.com', 'data:'],
    'img-src': ["'self'", 'data:', 'https:'],
}
Talisman(
    app,
    force_https=_is_production,   # set FLASK_ENV=production to enable
    content_security_policy=_csp,
    content_security_policy_nonce_in=['script-src'],
)

# ============ BLUEPRINTS ============
app.register_blueprint(auth_bp)
app.register_blueprint(client_bp, url_prefix='/client')
app.register_blueprint(provider_bp, url_prefix='/provider')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(api_bp, url_prefix='/api')


# ============ PUBLIC ROUTES ============
@app.route('/')
def home():
    return render_template('public/home.html')


@app.route('/about')
def about():
    return render_template('public/about.html')


@app.route('/search')
def search():
    from utils.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM ServiceCategory ORDER BY Category_Name")
    categories = cursor.fetchall()

    category_id = request.args.get('category')
    max_price = request.args.get('max_price')
    min_rating = request.args.get('min_rating')

    providers = []
    if request.args:
        query = """
            SELECT sl.*, u.First_Name, u.Last_Name, u.City, u.State,
                   sc.Category_Name,
                   COALESCE(AVG(r.Rating), 0) as avg_rating,
                   COUNT(r.Review_ID) as review_count
            FROM ServiceListing sl
            JOIN User u ON sl.Provider_ID = u.User_ID
            JOIN ServiceCategory sc ON sl.Category_ID = sc.Category_ID
            LEFT JOIN Booking b ON b.Provider_ID = sl.Provider_ID
            LEFT JOIN Review r ON r.Booking_ID = b.Booking_ID AND r.Reviewee_ID = sl.Provider_ID
            WHERE sl.Is_Active = TRUE
        """
        params = []

        if category_id:
            query += " AND sl.Category_ID = %s"
            params.append(category_id)

        if max_price:
            query += " AND sl.Price_Per_Hour <= %s"
            params.append(max_price)

        query += " GROUP BY sl.Listing_ID"

        if min_rating:
            query += " HAVING avg_rating >= %s"
            params.append(min_rating)

        query += " ORDER BY avg_rating DESC"

        cursor.execute(query, params)
        providers = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('public/search.html',
                           categories=categories,
                           providers=providers,
                           filters=request.args)


@app.route('/profile/<int:provider_id>')
def provider_profile(provider_id):
    from utils.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT u.User_ID, u.First_Name, u.Last_Name, u.City, u.State, u.Zip_Code,
               u.Profile_Image_URL,
               MAX(CASE WHEN bc.Check_Status = 'passed' THEN 'passed' END) as bg_check_status
        FROM User u
        LEFT JOIN BackgroundCheck bc ON bc.User_ID = u.User_ID
        WHERE u.User_ID = %s AND u.Account_Type IN ('provider', 'both')
        GROUP BY u.User_ID
    """, (provider_id,))
    provider = cursor.fetchone()

    if not provider:
        cursor.close()
        conn.close()
        return render_template('public/404.html'), 404

    cursor.execute("""
        SELECT sl.*, sc.Category_Name
        FROM ServiceListing sl
        JOIN ServiceCategory sc ON sl.Category_ID = sc.Category_ID
        WHERE sl.Provider_ID = %s AND sl.Is_Active = TRUE
        ORDER BY sl.Date_Created DESC
    """, (provider_id,))
    listings = cursor.fetchall()

    cursor.execute("""
        SELECT * FROM Availability WHERE Provider_ID = %s
        ORDER BY FIELD(Day_Of_Week,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'), Start_Time
    """, (provider_id,))
    availability = cursor.fetchall()

    cursor.execute("""
        SELECT r.Rating, r.Comment, r.Date_Posted,
               u.First_Name as reviewer_first, u.Last_Name as reviewer_last
        FROM Review r
        JOIN User u ON r.Reviewer_ID = u.User_ID
        WHERE r.Reviewee_ID = %s
        ORDER BY r.Date_Posted DESC
    """, (provider_id,))
    reviews = cursor.fetchall()

    avg_rating = sum(r['Rating'] for r in reviews) / len(reviews) if reviews else 0

    cursor.close()
    conn.close()

    return render_template('public/provider_profile.html',
                           provider=provider,
                           listings=listings,
                           availability=availability,
                           reviews=reviews,
                           avg_rating=avg_rating)


# ============ ERROR HANDLERS ============
@app.errorhandler(404)
def not_found(e):
    return render_template('public/404.html'), 404


@app.errorhandler(500)
def server_error(e):
    logger.error("Internal server error: %s", e)
    return render_template('public/500.html'), 500


if __name__ == '__main__':
    app.run(
        debug=os.environ.get('FLASK_DEBUG') == '1',
        host='0.0.0.0',
        port=5000,
    )
