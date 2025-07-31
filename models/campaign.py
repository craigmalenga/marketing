"""
Campaign model
"""

from app import db
from datetime import datetime

class Campaign(db.Model):
    """Campaign model for storing marketing campaign information"""
    __tablename__ = 'campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    meta_name = db.Column(db.String(200))  # Meta/Facebook campaign name
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ad_spends = db.relationship('AdSpend', backref='campaign', lazy='dynamic')
    
    def __repr__(self):
        return f'<Campaign {self.name}>'
    
    def to_dict(self):
        """Convert campaign to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'meta_name': self.meta_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }