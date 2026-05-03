"""
API routes for AJAX/JSON requests
"""

from flask import Blueprint, jsonify, session
from utils.db import get_db_connection

api_bp = Blueprint('api', __name__)


@api_bp.route('/notifications/count')
def notification_count():
    if 'user_id' not in session:
        return jsonify({'count': 0})

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT COUNT(*) as count FROM Notification
        WHERE User_ID = %s AND Is_Read = FALSE
    """, (session['user_id'],))
    count = cursor.fetchone()['count']
    cursor.close()
    conn.close()

    return jsonify({'count': count})
