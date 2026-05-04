# HandyBridge — Home Services Marketplace
 
A web application that connects home service providers (plumbers, cleaners, electricians, HVAC technicians) with homeowners and renters who need reliable, trustworthy help with household tasks.
 
## Features
 
- **User Authentication**: Register, login, and manage your account with bcrypt password hashing
- **Role-Based Access**: Separate dashboards and permissions for clients, providers, and admins
- **Service Listings**: Providers create listings with pricing, descriptions, and service radius
- **Provider Search**: Clients search for providers by category, location, price, and rating
- **Service Requests**: Clients submit requests with urgency levels and scheduling preferences
- **Booking System**: Create, confirm, start, and complete bookings between providers and clients
- **Payment Processing**: Record payments with multiple payment methods
- **Review System**: Two-way ratings and reviews after completed bookings
- **Availability Management**: Providers set weekly availability schedules
- **Notifications**: System notifications for booking updates, payments, and reviews
- **Admin Panel**: Platform statistics, user management, and category management
## Tech Stack
 
| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, Bootstrap 5, JavaScript, Font Awesome 6 |
| **Backend** | Python 3.12, Flask 3.0 |
| **Database** | MySQL 8.0 |
| **Auth** | Session-based with bcrypt password hashing |
| **Security** | Flask-WTF (CSRF protection), Flask-Limiter (rate limiting), Flask-Talisman (security headers) |
| **Templating** | Jinja2 |
| **Version Control** | Git + GitHub |
 
## Data Model
 
### User
 
| Column | Type | Description |
|---|---|---|
| User_ID | INT (PK) | Unique user ID, auto-increment |
| First_Name | VARCHAR(50) | User's first name |
| Last_Name | VARCHAR(50) | User's last name |
| Email | VARCHAR(100) | Unique email, used for login |
| Password_Hash | VARCHAR(255) | Hashed password (bcrypt) |
| Phone | VARCHAR(15) | Contact phone number |
| Street_Address | VARCHAR(100) | Street address |
| City | VARCHAR(50) | City |
| State | VARCHAR(2) | Two-letter state abbreviation |
| Zip_Code | VARCHAR(10) | Postal zip code |
| Account_Type | ENUM | 'provider', 'client', 'both', 'admin' |
| Date_Registered | DATETIME | Timestamp of account creation |
| Profile_Image_URL | VARCHAR(255) | URL to profile image |
 
### BackgroundCheck
 
| Column | Type | Description |
|---|---|---|
| Check_ID | INT (PK) | Unique check ID |
| User_ID | INT (FK) | References User |
| Check_Date | DATE | Date check was conducted |
| Check_Status | ENUM | 'pending', 'passed', 'failed' |
| Expiration_Date | DATE | When the check expires |
| Verification_Agency | VARCHAR(100) | Agency that performed the check |
 
### ServiceCategory
 
| Column | Type | Description |
|---|---|---|
| Category_ID | INT (PK) | Unique category ID |
| Category_Name | VARCHAR(50) | Name (e.g., Plumbing, Cleaning) |
| Description | TEXT | Brief description of category |
 
### ServiceListing
 
| Column | Type | Description |
|---|---|---|
| Listing_ID | INT (PK) | Unique listing ID |
| Provider_ID | INT (FK) | References User |
| Category_ID | INT (FK) | References ServiceCategory |
| Title | VARCHAR(100) | Listing title |
| Description | TEXT | Detailed description |
| Price_Per_Hour | DECIMAL(10,2) | Hourly rate |
| Price_Per_Job | DECIMAL(10,2) | Flat rate per job |
| Service_Radius_Miles | INT | Max travel distance |
| Is_Active | BOOLEAN | Whether listing is visible |
| Date_Created | DATETIME | When listing was created |
 
### Availability
 
| Column | Type | Description |
|---|---|---|
| Availability_ID | INT (PK) | Unique slot ID |
| Provider_ID | INT (FK) | References User |
| Day_Of_Week | ENUM | 'Monday' through 'Sunday' |
| Start_Time | TIME | Start of available slot |
| End_Time | TIME | End of available slot |
 
### ServiceRequest
 
| Column | Type | Description |
|---|---|---|
| Request_ID | INT (PK) | Unique request ID |
| Client_ID | INT (FK) | References User |
| Category_ID | INT (FK) | References ServiceCategory |
| Title | VARCHAR(100) | Short title |
| Description | TEXT | Detailed problem description |
| Urgency | ENUM | 'low', 'medium', 'high', 'emergency' |
| Preferred_Date | DATE | Client's preferred date |
| Preferred_Time | TIME | Client's preferred time |
| Service_Address | VARCHAR(100) | Address where service is needed |
| Service_City | VARCHAR(50) | City |
| Service_State | VARCHAR(2) | State |
| Service_Zip | VARCHAR(10) | Zip code |
| Status | ENUM | 'open', 'matched', 'completed', 'cancelled' |
| Date_Created | DATETIME | When request was submitted |
 
### Booking
 
| Column | Type | Description |
|---|---|---|
| Booking_ID | INT (PK) | Unique booking ID |
| Provider_ID | INT (FK) | References User (provider) |
| Client_ID | INT (FK) | References User (client) |
| Request_ID | INT (FK) | References ServiceRequest (nullable) |
| Listing_ID | INT (FK) | References ServiceListing (nullable) |
| Scheduled_Date | DATE | Date of service |
| Scheduled_Start_Time | TIME | Scheduled start |
| Scheduled_End_Time | TIME | Scheduled end |
| Actual_Start_Time | DATETIME | When provider started |
| Actual_End_Time | DATETIME | When provider finished |
| Status | ENUM | 'pending', 'confirmed', 'in_progress', 'completed', 'cancelled' |
| Total_Amount | DECIMAL(10,2) | Total cost |
| Notes | TEXT | Additional notes |
| Date_Created | DATETIME | When booking was created |
 
### Payment
 
| Column | Type | Description |
|---|---|---|
| Payment_ID | INT (PK) | Unique payment ID |
| Booking_ID | INT (FK) | References Booking (unique) |
| Amount | DECIMAL(10,2) | Payment amount |
| Payment_Method | ENUM | 'credit_card', 'debit_card', 'paypal', 'bank_transfer' |
| Payment_Status | ENUM | 'pending', 'completed', 'refunded', 'failed' |
| Transaction_Date | DATETIME | When payment was processed |
| Transaction_Reference | VARCHAR(100) | External transaction ID |
 
### Review
 
| Column | Type | Description |
|---|---|---|
| Review_ID | INT (PK) | Unique review ID |
| Booking_ID | INT (FK) | References Booking |
| Reviewer_ID | INT (FK) | References User (who wrote it) |
| Reviewee_ID | INT (FK) | References User (who it's about) |
| Rating | INT | Rating from 1 to 5 |
| Comment | TEXT | Written review |
| Date_Posted | DATETIME | When review was submitted |
 
### Notification
 
| Column | Type | Description |
|---|---|---|
| Notification_ID | INT (PK) | Unique notification ID |
| User_ID | INT (FK) | References User (recipient) |
| Message | TEXT | Notification content |
| Type | ENUM | 'booking', 'payment', 'review', 'system' |
| Is_Read | BOOLEAN | Whether user has read it |
| Date_Sent | DATETIME | When notification was sent |
 
## Local Development Setup
 
### Prerequisites
 
- Python 3.10 or higher
- MySQL 8.0 or higher
- pip (comes with Python)
- Git
### Installation
 
```bash
# 1. Clone the repository
git clone https://github.com/adanbarrera82/HandyBridge.git
cd HandyBridge
 
# 2. Create virtual environment (recommended)
python -m venv venv
 
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
 
# 3. Install dependencies
pip install -r requirements.txt
 
# 4. Set up the database
# Open MySQL Workbench and run database/setup.sql
# Or from command line:
mysql -u root -p < database/setup.sql
 
# 5. Set up environment variables
# Create a .env file in the HandyBridge/ directory:
# SECRET_KEY=<run: python -c "import secrets; print(secrets.token_hex(32))">
# DB_PASSWORD=your_mysql_password
# (SECRET_KEY is required — the app will not start without it)
 
# 6. Run the Flask app
python app.py
```
 
Visit **http://localhost:5000** in your browser.
 
### Test Accounts
 
All sample accounts use the password: `password123`
 
| Role | Email | Description |
|---|---|---|
| Admin | admin@handybridge.com | Platform administrator |
| Provider | joe@example.com | Plumber in Edinburg, TX |
| Provider | jane@example.com | Home cleaner in McAllen, TX |
| Provider | mike@example.com | Electrician/HVAC in Brownsville, TX |
| Client | paul@example.com | Client in Edinburg, TX |
| Client | kassie@example.com | Client in McAllen, TX |
| Both | joey@example.com | Client & handyman in Pharr, TX |
 
> **Note:** After cloning, you may need to regenerate password hashes. Open a Python shell in the project directory and run:
> ```python
> from utils.auth import hash_password
> from utils.db import get_db_connection
> h = hash_password('password123')
> conn = get_db_connection()
> cur = conn.cursor()
> cur.execute("UPDATE User SET Password_Hash = %s WHERE User_ID > 0", (h,))
> conn.commit()
> cur.close()
> conn.close()
> ```
 
## Project Structure
 
```
HandyBridge/
├── app.py                        # Main Flask application
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (not in repo)
├── .gitignore
├── README.md
├── database/
│   └── setup.sql                 # Schema + sample data
├── routes/
│   ├── auth.py                   # Register, Login, Logout
│   ├── client.py                 # Client dashboard, bookings, reviews
│   ├── provider.py               # Provider dashboard, listings, availability
│   ├── admin.py                  # Admin dashboard, user/category management
│   └── api.py                    # JSON API endpoints
├── templates/
│   ├── base.html                 # Shared layout (navbar, footer)
│   ├── public/                   # Home, Login, Register, Search, About, Provider Profile
│   ├── client/                   # Client pages
│   ├── provider/                 # Provider pages
│   └── admin/                    # Admin pages
├── static/
│   ├── css/style.css             # Custom styles
│   ├── js/                       # JavaScript files
│   └── images/                   # Static images
└── utils/
    ├── db.py                     # MySQL connection helper
    ├── auth.py                   # Password hashing utilities
    ├── decorators.py             # login_required, admin_required, provider_required
    └── extensions.py             # Flask-Limiter and Flask-WTF shared instances
```
 
## References
 
- [Flask Documentation](https://flask.palletsprojects.com/)
- [MySQL 8.0 Reference Manual](https://dev.mysql.com/doc/refman/8.0/en/)
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.3/)
- [bcrypt Documentation](https://pypi.org/project/bcrypt/)
- ANTES System Requirements Specification (UTRGV course reference)
- ANTES System Software Design (UTRGV course reference)