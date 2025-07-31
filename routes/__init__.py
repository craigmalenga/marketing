
"""
Routes package for Marketing Analytics Platform
"""

from .upload import upload_bp
from .reports import reports_bp
from .mappings import mappings_bp

__all__ = ['upload_bp', 'reports_bp', 'mappings_bp']