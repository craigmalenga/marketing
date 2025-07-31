"""
Application model for affordability check data
"""

from app import db
from datetime import datetime

class Application(db.Model):
    """Application model for storing affordability check data (passed/failed)"""
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.String(50), nullable=False)
    datetime = db.Column(db.DateTime)
    status = db.Column(db.String(100))
    user = db.Column(db.String(100))
    lead_datetime = db.Column(db.DateTime)
    lead_name = db.Column(db.String(200))
    lead_postcode = db.Column(db.String(20))
    lead_introducer = db.Column(db.String(100))
    lead_partner = db.Column(db.String(100))
    lead_cost = db.Column(db.Float)
    lead_value = db.Column(db.Float)
    current_status = db.Column(db.String(100))
    affordability_result = db.Column(db.String(20))  # 'passed' or 'failed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Index for performance
    __table_args__ = (
        db.Index('idx_lead_id', 'lead_id'),
        db.Index('idx_datetime', 'datetime'),
        db.Index('idx_affordability_result', 'affordability_result'),
    )
    
    def __repr__(self):
        return f'<Application {self.lead_id} - {self.affordability_result}>'
    
    def to_dict(self):
        """Convert application to dictionary"""
        return {
            'id': self.id,
            'lead_id': self.lead_id,
            'datetime': self.datetime.isoformat() if self.datetime else None,
            'status': self.status,
            'user': self.user,
            'lead_datetime': self.lead_datetime.isoformat() if self.lead_datetime else None,
            'lead_name': self.lead_name,
            'lead_postcode': self.lead_postcode,
            'lead_introducer': self.lead_introducer,
            'lead_partner': self.lead_partner,
            'lead_cost': self.lead_cost,
            'lead_value': self.lead_value,
            'current_status': self.current_status,
            'affordability_result': self.affordability_result,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def parse_excel_datetime(value):
        """Parse datetime from Excel (could be serial number or string)"""
        if value is None:
            return None
            
        # If it's a number (Excel serial date)
        if isinstance(value, (int, float)):
            # Excel dates are days since 1900-01-01 (with leap year bug)
            from datetime import datetime, timedelta
            excel_base_date = datetime(1899, 12, 30)  # Adjusted for Excel's leap year bug
            return excel_base_date + timedelta(days=value)
        
        # If it's already a datetime
        if isinstance(value, datetime):
            return value
            
        # If it's a string, try to parse it
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except:
                try:
                    return datetime.strptime(value, '%Y-%m-%d')
                except:
                    return None
        
        return None