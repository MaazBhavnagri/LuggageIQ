"""
FastAPI backend for LuggageIQ
"""

from .main import app
from .routes import router

__all__ = ['app', 'router']
