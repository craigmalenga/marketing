"""
Status Mapping model
"""

from app import db
from datetime import datetime
from sqlalchemy import func

class StatusMapping(db.Model):
    """Status mapping model for defining 1s and 0s for each status variant"""
    __tablename__ = 'status_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(200), nullable=False, unique=True)
    is_application_received = db.Column(db.Integer, default=0)  # 1 or 0
    is_application_processed = db.Column(db.Integer, default=0)  # 1 or 0
    is_application_approved = db.Column(db.Integer, default=0)  # 1 or 0
    is_future = db.Column(db.Integer, default=0)  # 1 or 0
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f'<StatusMapping {self.status_name}>'
    
    def to_dict(self):
        """Convert status mapping to dictionary"""
        return {
            'id': self.id,
            'status_name': self.status_name,
            'is_application_received': self.is_application_received,
            'is_application_processed': self.is_application_processed,
            'is_application_approved': self.is_application_approved,
            'is_future': self.is_future,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_default_mappings():
        """Get default status mappings based on Excel analysis"""
        return [
            {'status_name': 'Active', 'is_application_received': 1, 'is_application_processed': 1, 'is_application_approved': 1, 'is_future': 0},
            {'status_name': 'Affordability check', 'is_application_received': 0, 'is_application_processed': 0, 'is_application_approved': 0, 'is_future': 0},
            {'status_name': 'Affordability check failed', 'is_application_received': 1, 'is_application_processed': 1, 'is_application_approved': 0, 'is_future': 0},
            {'status_name': 'Affordability check for review', 'is_application_received': 1, 'is_application_processed': 1, 'is_application_approved': 0, 'is_future': 1},
            {'status_name': 'Affordability check partial received', 'is_application_received': 0, 'is_application_processed': 0, 'is_application_approved': 0, 'is_future': 0},
            {'status_name': 'Affordability check passed', 'is_application_received': 1, 'is_application_processed': 1, 'is_application_approved': 1, 'is_future': 0},
            {'status_name': 'Affordability check query', 'is_application_received': 1, 'is_application_processed': 1, 'is_application_approved': 0, 'is_future': 1},
            {'status_name': 'Affordability check received', 'is_application_received': 1, 'is_application_processed': 1, 'is_application_approved': 0, 'is_future': 1},
            {'status_name': 'Agreement sent for signature', 'is_application_received': 1, 'is_application_processed': 1, 'is_application_approved': 1, 'is_future': 0},
            {'status_name': 'Agreement signed', 'is_application_received': 1, 'is_application_processed': 1, 'is_application_approved': 1, 'is_future': 0},
            {'status_name': 'Application checked', 'is_application_received': 0, 'is_application_processed': 0, 'is_application_approved': 0, 'is_future': 0},
            {'status_name': 'Application received', 'is_application_received': 0, 'is_application_processed': 0, 'is_application_approved': 0, 'is_future': 0},
            {'status_name': 'Arrears', 'is_application_received': 1, 'is_application_processed': 1, 'is_application_approved': 1, 'is_future': 0},
            {'status_name': 'Awaiting affordability check', 'is_application_received': 1, 'is_application_processed': 0, 'is_application_approved': 0, 'is_future': 0},
            {'status_name': 'Breathing space', 'is_application_received': 1, 'is_application_processed': 1, 'is_application_approved': 1, 'is_future': 0},
            {'status_name': 'Cancelled', 'is_application_received': 0, 'is_application_processed': 0, 'is_application_approved': 0, 'is_future': 0},
            {'status_name': 'Cancelled - exceeds £2000 limit', 'is_application_received': 1, 'is_application_processed': 0, 'is_application_approved': 0, 'is_future': 0},
            {'status_name': 'Cancelled - income under £1000', 'is_application_received': 1, 'is_application_processed': 0, 'is_application_approved': 0, 'is_future': 0},
            {'status_name': 'Cancelled - under 30 years old', 'is_application_received': 1, 'is_application_processed': 0, 'is_application_approved': 0, 'is_future': 0},
            {'status_name': 'Capture customer direct debit details', 'is_application_received': 1, 'is_application_processed': 1, 'is_application_approved': 1, 'is_future': 0},
            {'status_name': 'Capture customer direct debit details (Sofa/Bed)', 'is_application_received': 1, 'is_application_processed': 1, 'is_application_approved': 1, 'is_future': 0},
            {'status_name': 'Closed - customer doesn\'t want the product anymore', 'is_application_received': 0, 'is_application_processed': 0, 'is_application_approved': 0, 'is_future': 0},
            {'status_name': 'Closed - customer not responding to request', 'is_application_received': 1, 'is_application_processed': 0, 'is_application_approved': 0, 'is_future': 0},
            {'status_name': 'Closed - customer refused to supply bank statement', 'is_application_received': 0, 'is_application_processed': 0, 'is_application_approved': 0, 'is_future': 0},
            {'status_name': 'Closed - no response to pre call', 'is_application_received': 1, 'is_application_processed': 0, 'is_application_approved': 0, 'is_future': 0},
            {'status_name': 'Closed - did not respond to further info req', 'is_application_received': 1, 'is_application_processed': 0, 'is_application_approved': 0, 'is_future': 0},
            {'status_name': 'Closed - not interested anymore', 'is_application_received': 0, 'is_application_processed': 0, 'is_application_approved': 0, 'is_future': 0},
            {'status_name': 'Closed - pending open banking', 'is_application_received': 0, 'is_application_processed': 0, 'is_application_approved': 0, 'is_future': 0},
            {'status_name': 'Closed - previous application failed', 'is_application_received': 0, 'is_application_processed': 0, 'is_application_approved': 0, 'is_future': 0},
            {'status_name': 'Closed - product out of stock', 'is_application_received': 1, 'is_application_processed': 1, 'is_application_approved': 0, 'is_future': 0},
            {'status_name': 'Closed - within post discharge period', 'is_application_received': 1, 'is_application_processed': 1, 'is_application_approved': 1, 'is_future': 0},
            {'status_name': 'Collect initial payment', 'is_application_received': 1, 'is_application_processed': 1, 'is_application_approved': 1, 'is_future': 0},
            {'status_name': 'Future', 'is_application_received': 0, 'is_application_processed': 0, 'is_application_approved': 0, 'is_future': 1}
        ]