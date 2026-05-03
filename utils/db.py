"""
Database connection utility for HandyBridge
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
load_dotenv()


# Database configuration - update these for your environment
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'HandyBridge'),
}


def get_db_connection():
    """Establish and return a MySQL database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
        raise e


def execute_query(query, params=None):
    """Execute a SELECT query and return results."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        results = cursor.fetchall()
        return results
    finally:
        cursor.close()
        conn.close()


def execute_update(query, params=None):
    """Execute an INSERT, UPDATE, or DELETE statement. Returns lastrowid for inserts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()
