"""
Shared Flask extension instances — imported by app.py (init_app)
and by individual blueprints that need them (e.g. limiter on login).
Kept here to avoid circular imports.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

# No default limits — applied per-route where needed
limiter = Limiter(key_func=get_remote_address, default_limits=[])

csrf = CSRFProtect()
