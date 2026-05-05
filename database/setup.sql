-- ============================================
-- HandyBridge.com Database Setup
-- Run this to create the database, tables, and sample data
-- ============================================

CREATE DATABASE IF NOT EXISTS HandyBridge;
USE HandyBridge;

-- Drop tables in reverse dependency order if they exist
DROP TABLE IF EXISTS PasswordReset;
DROP TABLE IF EXISTS Notification;
DROP TABLE IF EXISTS Review;
DROP TABLE IF EXISTS Payment;
DROP TABLE IF EXISTS Booking;
DROP TABLE IF EXISTS ServiceRequest;
DROP TABLE IF EXISTS Availability;
DROP TABLE IF EXISTS ServiceListing;
DROP TABLE IF EXISTS BackgroundCheck;
DROP TABLE IF EXISTS ServiceCategory;
DROP TABLE IF EXISTS User;

-- 1. User
CREATE TABLE User (
    User_ID INT AUTO_INCREMENT PRIMARY KEY,
    First_Name VARCHAR(50) NOT NULL,
    Last_Name VARCHAR(50) NOT NULL,
    Email VARCHAR(100) NOT NULL UNIQUE,
    Password_Hash VARCHAR(255) NOT NULL,
    Phone VARCHAR(15),
    Street_Address VARCHAR(100),
    City VARCHAR(50),
    State VARCHAR(2),
    Zip_Code VARCHAR(10),
    Account_Type ENUM('provider','client','both','admin') NOT NULL DEFAULT 'client',
    Date_Registered DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Profile_Image_URL VARCHAR(255)
);

-- 2. BackgroundCheck
CREATE TABLE BackgroundCheck (
    Check_ID INT AUTO_INCREMENT PRIMARY KEY,
    User_ID INT NOT NULL,
    Check_Date DATE NOT NULL,
    Check_Status ENUM('pending','passed','failed') NOT NULL DEFAULT 'pending',
    Expiration_Date DATE,
    Verification_Agency VARCHAR(100),
    FOREIGN KEY (User_ID) REFERENCES User(User_ID) ON DELETE CASCADE
);

-- 3. ServiceCategory
CREATE TABLE ServiceCategory (
    Category_ID INT AUTO_INCREMENT PRIMARY KEY,
    Category_Name VARCHAR(50) NOT NULL UNIQUE,
    Description TEXT
);

-- 4. ServiceListing
CREATE TABLE ServiceListing (
    Listing_ID INT AUTO_INCREMENT PRIMARY KEY,
    Provider_ID INT NOT NULL,
    Category_ID INT NOT NULL,
    Title VARCHAR(100) NOT NULL,
    Description TEXT,
    Price_Per_Hour DECIMAL(10,2),
    Price_Per_Job DECIMAL(10,2),
    Service_Radius_Miles INT,
    Is_Active BOOLEAN NOT NULL DEFAULT TRUE,
    Date_Created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Provider_ID) REFERENCES User(User_ID) ON DELETE CASCADE,
    FOREIGN KEY (Category_ID) REFERENCES ServiceCategory(Category_ID)
);

-- 5. Availability
CREATE TABLE Availability (
    Availability_ID INT AUTO_INCREMENT PRIMARY KEY,
    Provider_ID INT NOT NULL,
    Day_Of_Week ENUM('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday') NOT NULL,
    Start_Time TIME NOT NULL,
    End_Time TIME NOT NULL,
    FOREIGN KEY (Provider_ID) REFERENCES User(User_ID) ON DELETE CASCADE
);

-- 6. ServiceRequest
CREATE TABLE ServiceRequest (
    Request_ID INT AUTO_INCREMENT PRIMARY KEY,
    Client_ID INT NOT NULL,
    Category_ID INT NOT NULL,
    Title VARCHAR(100) NOT NULL,
    Description TEXT,
    Urgency ENUM('low','medium','high','emergency') NOT NULL DEFAULT 'medium',
    Preferred_Date DATE,
    Preferred_Time TIME,
    Service_Address VARCHAR(100) NOT NULL,
    Service_City VARCHAR(50) NOT NULL,
    Service_State VARCHAR(2) NOT NULL,
    Service_Zip VARCHAR(10) NOT NULL,
    Status ENUM('open','matched','completed','cancelled') NOT NULL DEFAULT 'open',
    Date_Created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Client_ID) REFERENCES User(User_ID) ON DELETE CASCADE,
    FOREIGN KEY (Category_ID) REFERENCES ServiceCategory(Category_ID)
);

-- 7. Booking
CREATE TABLE Booking (
    Booking_ID INT AUTO_INCREMENT PRIMARY KEY,
    Provider_ID INT NOT NULL,
    Client_ID INT NOT NULL,
    Request_ID INT,
    Listing_ID INT,
    Scheduled_Date DATE NOT NULL,
    Scheduled_Start_Time TIME NOT NULL,
    Scheduled_End_Time TIME NOT NULL,
    Actual_Start_Time DATETIME,
    Actual_End_Time DATETIME,
    Status ENUM('pending','confirmed','in_progress','completed','cancelled') NOT NULL DEFAULT 'pending',
    Total_Amount DECIMAL(10,2),
    Notes TEXT,
    Date_Created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Provider_ID) REFERENCES User(User_ID) ON DELETE CASCADE,
    FOREIGN KEY (Client_ID) REFERENCES User(User_ID) ON DELETE CASCADE,
    FOREIGN KEY (Request_ID) REFERENCES ServiceRequest(Request_ID) ON DELETE SET NULL,
    FOREIGN KEY (Listing_ID) REFERENCES ServiceListing(Listing_ID) ON DELETE SET NULL
);

-- 8. Payment
CREATE TABLE Payment (
    Payment_ID INT AUTO_INCREMENT PRIMARY KEY,
    Booking_ID INT NOT NULL UNIQUE,
    Amount DECIMAL(10,2) NOT NULL,
    Payment_Method ENUM('credit_card','debit_card','paypal','bank_transfer') NOT NULL,
    Payment_Status ENUM('pending','completed','refunded','failed') NOT NULL DEFAULT 'pending',
    Transaction_Date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Transaction_Reference VARCHAR(100),
    FOREIGN KEY (Booking_ID) REFERENCES Booking(Booking_ID) ON DELETE CASCADE
);

-- 9. Review
CREATE TABLE Review (
    Review_ID INT AUTO_INCREMENT PRIMARY KEY,
    Booking_ID INT NOT NULL,
    Reviewer_ID INT NOT NULL,
    Reviewee_ID INT NOT NULL,
    Rating INT NOT NULL CHECK (Rating >= 1 AND Rating <= 5),
    Comment TEXT,
    Date_Posted DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Booking_ID) REFERENCES Booking(Booking_ID) ON DELETE CASCADE,
    FOREIGN KEY (Reviewer_ID) REFERENCES User(User_ID) ON DELETE CASCADE,
    FOREIGN KEY (Reviewee_ID) REFERENCES User(User_ID) ON DELETE CASCADE
);

-- 10. PasswordReset
CREATE TABLE PasswordReset (
    Reset_ID INT AUTO_INCREMENT PRIMARY KEY,
    User_ID INT NOT NULL,
    Token VARCHAR(64) NOT NULL UNIQUE,
    Expires_At DATETIME NOT NULL,
    Is_Used BOOLEAN NOT NULL DEFAULT FALSE,
    Created_At DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (User_ID) REFERENCES User(User_ID) ON DELETE CASCADE
);

-- 11. Notification
CREATE TABLE Notification (
    Notification_ID INT AUTO_INCREMENT PRIMARY KEY,
    User_ID INT NOT NULL,
    Message TEXT NOT NULL,
    Type ENUM('booking','payment','review','system') NOT NULL DEFAULT 'system',
    Is_Read BOOLEAN NOT NULL DEFAULT FALSE,
    Date_Sent DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (User_ID) REFERENCES User(User_ID) ON DELETE CASCADE
);


-- ============================================
-- SAMPLE DATA
-- ============================================

-- Service Categories
INSERT INTO ServiceCategory (Category_Name, Description) VALUES
('Plumbing', 'Pipe repair, leak fixing, drain cleaning, water heater service'),
('Home Cleaning', 'Regular cleaning, deep cleaning, move-in/move-out cleaning'),
('Electrical', 'Wiring, outlet installation, lighting, panel upgrades'),
('HVAC', 'AC repair, heating service, duct cleaning, thermostat installation'),
('Painting', 'Interior and exterior painting, staining, wallpaper removal'),
('Landscaping', 'Lawn care, tree trimming, garden maintenance, irrigation'),
('Appliance Repair', 'Washer, dryer, refrigerator, dishwasher, oven repair'),
('Handyman', 'General repairs, furniture assembly, minor fixes');

-- Sample Users (password for all: "password123")
-- bcrypt hash of "password123"
INSERT INTO User (First_Name, Last_Name, Email, Password_Hash, Phone, Street_Address, City, State, Zip_Code, Account_Type) VALUES
('Admin', 'User', 'admin@handybridge.com', '$2b$12$LJ3m4ys5Rn.dRiKYlDlpHeGnBHzs/CkFJsR8Vo8OMlWMy/6DK4XW2', '9561234567', '100 Admin St', 'Edinburg', 'TX', '78539', 'admin'),
('Joe', 'Martinez', 'joe@example.com', '$2b$12$LJ3m4ys5Rn.dRiKYlDlpHeGnBHzs/CkFJsR8Vo8OMlWMy/6DK4XW2', '9562345678', '200 Main St', 'Edinburg', 'TX', '78539', 'provider'),
('Jane', 'Garcia', 'jane@example.com', '$2b$12$LJ3m4ys5Rn.dRiKYlDlpHeGnBHzs/CkFJsR8Vo8OMlWMy/6DK4XW2', '9563456789', '300 Oak Ave', 'McAllen', 'TX', '78501', 'provider'),
('Mike', 'Johnson', 'mike@example.com', '$2b$12$LJ3m4ys5Rn.dRiKYlDlpHeGnBHzs/CkFJsR8Vo8OMlWMy/6DK4XW2', '9564567890', '400 Elm St', 'Brownsville', 'TX', '78520', 'provider'),
('Paul', 'Smith', 'paul@example.com', '$2b$12$LJ3m4ys5Rn.dRiKYlDlpHeGnBHzs/CkFJsR8Vo8OMlWMy/6DK4XW2', '9565678901', '500 Pine Rd', 'Edinburg', 'TX', '78539', 'client'),
('Kassie', 'Lopez', 'kassie@example.com', '$2b$12$LJ3m4ys5Rn.dRiKYlDlpHeGnBHzs/CkFJsR8Vo8OMlWMy/6DK4XW2', '9566789012', '600 Cedar Ln', 'McAllen', 'TX', '78501', 'client'),
('Joey', 'Davis', 'joey@example.com', '$2b$12$LJ3m4ys5Rn.dRiKYlDlpHeGnBHzs/CkFJsR8Vo8OMlWMy/6DK4XW2', '9567890123', '700 Birch Dr', 'Pharr', 'TX', '78577', 'both');

-- Background Checks for providers
INSERT INTO BackgroundCheck (User_ID, Check_Date, Check_Status, Expiration_Date, Verification_Agency) VALUES
(2, '2025-01-15', 'passed', '2026-01-15', 'Sterling Volunteers'),
(3, '2025-02-20', 'passed', '2026-02-20', 'GoodHire'),
(4, '2025-03-10', 'passed', '2026-03-10', 'Checkr');

-- Service Listings
INSERT INTO ServiceListing (Provider_ID, Category_ID, Title, Description, Price_Per_Hour, Price_Per_Job, Service_Radius_Miles) VALUES
(2, 1, 'Expert Plumbing Services', 'Leak repair, pipe installation, drain cleaning. 15+ years experience.', 65.00, NULL, 50),
(2, 1, 'Emergency Plumbing', '24/7 emergency plumbing service for urgent issues.', 95.00, NULL, 30),
(3, 2, 'Professional Home Cleaning', 'Thorough home cleaning service. Supplies included.', 35.00, NULL, 15),
(3, 2, 'Deep Cleaning Service', 'Complete deep clean for move-in/move-out.', NULL, 200.00, 15),
(4, 3, 'Electrical Services', 'Residential electrical work, repairs, and installations.', 75.00, NULL, 40),
(4, 4, 'AC & Heating Repair', 'HVAC diagnostics, repair, and maintenance.', 80.00, NULL, 40),
(7, 8, 'General Handyman', 'Furniture assembly, minor repairs, installations.', 45.00, NULL, 20);

-- Availability
INSERT INTO Availability (Provider_ID, Day_Of_Week, Start_Time, End_Time) VALUES
(2, 'Monday', '08:00', '17:00'), (2, 'Tuesday', '08:00', '17:00'), (2, 'Wednesday', '08:00', '17:00'),
(2, 'Thursday', '08:00', '17:00'), (2, 'Friday', '08:00', '15:00'),
(3, 'Monday', '09:00', '14:00'), (3, 'Tuesday', '09:00', '14:00'),
(3, 'Wednesday', '09:00', '14:00'), (3, 'Thursday', '09:00', '14:00'),
(4, 'Monday', '07:00', '18:00'), (4, 'Tuesday', '07:00', '18:00'),
(4, 'Wednesday', '07:00', '18:00'), (4, 'Saturday', '08:00', '12:00');

-- Service Requests
INSERT INTO ServiceRequest (Client_ID, Category_ID, Title, Description, Urgency, Preferred_Date, Service_Address, Service_City, Service_State, Service_Zip) VALUES
(5, 1, 'Ceiling leak in living room', 'Water dripping from ceiling since this morning. Need urgent help.', 'emergency', '2026-03-01', '500 Pine Rd', 'Edinburg', 'TX', '78539'),
(6, 2, 'Weekly home cleaning', 'Need someone to clean my home twice a week.', 'low', '2026-03-05', '600 Cedar Ln', 'McAllen', 'TX', '78501'),
(7, 4, 'AC not cooling', 'AC unit running but not cooling. Rental property needs urgent fix.', 'high', '2026-03-02', '700 Birch Dr', 'Pharr', 'TX', '78577');

-- Bookings
INSERT INTO Booking (Provider_ID, Client_ID, Request_ID, Listing_ID, Scheduled_Date, Scheduled_Start_Time, Scheduled_End_Time, Status, Total_Amount) VALUES
(2, 5, 1, 1, '2026-03-01', '10:00', '12:00', 'completed', 130.00),
(3, 6, 2, 3, '2026-03-05', '09:00', '12:00', 'completed', 105.00),
(4, 7, 3, 6, '2026-03-02', '08:00', '10:00', 'completed', 160.00);

-- Payments
INSERT INTO Payment (Booking_ID, Amount, Payment_Method, Payment_Status) VALUES
(1, 130.00, 'credit_card', 'completed'),
(2, 105.00, 'paypal', 'completed'),
(3, 160.00, 'debit_card', 'completed');

-- Reviews
INSERT INTO Review (Booking_ID, Reviewer_ID, Reviewee_ID, Rating, Comment) VALUES
(1, 5, 2, 5, 'Joe was fantastic! Fixed the leak quickly and professionally.'),
(1, 2, 5, 5, 'Paul was very accommodating and the house was easy to work in.'),
(2, 6, 3, 4, 'Jane did a great job cleaning. Very thorough.'),
(3, 7, 4, 5, 'Mike saved the day! AC is working perfectly now.');

-- Notifications
INSERT INTO Notification (User_ID, Message, Type) VALUES
(5, 'Your booking with Joe Martinez has been completed.', 'booking'),
(2, 'You received a 5-star review from Paul Smith.', 'review'),
(6, 'Your booking with Jane Garcia has been completed.', 'booking');
