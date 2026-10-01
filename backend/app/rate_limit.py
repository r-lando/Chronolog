"""
Rate limiting configuration using slowapi (a Flask-Limiter-style wrapper
for ASGI apps). Limits are keyed by client IP address. Applied to
endpoints that are attractive to brute-force or abuse: login, register,
and (from Milestone 3) evidence upload.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
