# HandyBridge — Home Services Marketplace
 
A web application that connects home service providers with clients who need household services. Built with Flask, MySQL, and deployed on Railway.

**Live Demo:** https://handybridge-production.up.railway.app

## Features

- **User Authentication**: Secure registration, login, password reset via email, and account deletion
- **Role-Based Access**: Separate dashboards for clients, providers, and admins
- **Booking System**: Clients book providers directly from profile pages with real-time price estimation
- **Service Management**: Providers create listings, set availability, and manage bookings
- **Reviews & Ratings**: 5-star rating system for completed services
- **Service Requests**: Clients submit general service inquiries with urgency levels
- **Provider Tools**: Earnings dashboard, availability scheduling, listing management
- **Admin Panel**: User management, category management, platform statistics

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.12, Flask 3.0 |
| Database | MySQL 8.0 |
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript |
| Email | Resend API |
| Security | bcrypt, CSRF protection, rate limiting, security headers |
| Deployment | Railway |

## Testing the Application

### Production URL
https://handybridge-production.up.railway.app

### Test Credentials

**Admin:**
- admin@handybridge.com

**Providers:**
- john.smith@email.com (Plumber with active listings)
- mike.johnson@email.com (Electrician)
- emily.davis@email.com (House Cleaner)
- david.brown@email.com (HVAC Technician)
- lisa.garcia@email.com (Landscaper)

**Clients:**
- sarah.johnson@email.com (Has bookings and reviews)
- robert.martinez@email.com (Has service requests)
- jennifer.lopez@email.com (Clean account)
- michael.clark@email.com (Clean account)

**Dual Role:**
- alex.wilson@email.com (Client + Provider)

### Recommended Testing Flow

**1. Client Experience (sarah.johnson@email.com):**
- Search for providers
- View provider profile
- Book a service (fill form, see price calculation)
- View bookings page
- Write a review for completed booking
- Submit and cancel service requests

**2. Provider Experience (john.smith@email.com):**
- View incoming bookings
- Accept/decline booking requests
- Manage service listings (create, edit, toggle active)
- Set weekly availability
- View earnings dashboard

**3. Admin Experience (admin@handybridge.com):**
- Manage users (search, filter, change account types)
- Manage service categories (add, edit, delete)
- View platform statistics

## Database Schema

**11 Tables:** User, ServiceCategory, ServiceListing, Availability, ServiceRequest, Booking, Payment, Review, BackgroundCheck, Notification, PasswordReset

**Key Relationships:**
- Users can be clients, providers, admins, or both
- Providers create service listings under categories
- Clients book providers, creating bookings
- Bookings can be reviewed after completion
- Service requests are separate from direct bookings

See detailed schema documentation in `database/setup.sql`

## Local Development Setup

### Prerequisites
- Python 3.12+
- MySQL 8.0+
- Git

### Installation

```bash
# 1. Clone repository
git clone https://github.com/adanbarrera82/HandyBridge.git
cd HandyBridge

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up database
mysql -u root -p < database/setup.sql

# 5. Create .env file
SECRET_KEY=your-secret-key-here
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-mysql-password
DB_NAME=handybridge
RESEND_API_KEY=your-resend-api-key

# Generate SECRET_KEY:
# python -c "import secrets; print(secrets.token_hex(32))"

# 6. Run application
python app.py
```

Visit http://localhost:5000

## Project Structure
