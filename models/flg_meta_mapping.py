"""
FLG to Meta name mapping model
"""

from app import db
from datetime import datetime
from sqlalchemy import func

class FLGMetaMapping(db.Model):
    """FLG to Meta name mapping model for matching marketing sources to campaigns"""
    __tablename__ = 'flg_meta_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    flg_name = db.Column(db.String(200), nullable=False, unique=True)
    meta_name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())
    
    def __repr__(self):
        return f'<FLGMetaMapping {self.flg_name} -> {self.meta_name}>'
    
    def to_dict(self):
        """Convert mapping to dictionary"""
        return {
            'id': self.id,
            'flg_name': self.flg_name,
            'meta_name': self.meta_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def get_default_mappings():
        """Get default FLG to Meta mappings based on common patterns"""
        return [
            # These would be populated from the Word document upload
            # For now, return empty list
        ]