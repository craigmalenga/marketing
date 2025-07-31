"""
Ad Spend model
"""

from app import db
from datetime import datetime

class AdSpend(db.Model):
    """Ad Spend model for storing campaign and ad level spending data"""
    __tablename__ = 'ad_spend'
    
    id = db.Column(db.Integer, primary_key=True)
    reporting_end_date = db.Column(db.Date, nullable=False)
    meta_campaign_name = db.Column(db.String(200), nullable=False)
    ad_level = db.Column(db.String(200))  # Ad level name/identifier
    spend_amount = db.Column(db.Float, nullable=False)
    is_new = db.Column(db.Boolean, default=False)  # Flag for new campaigns
    
    # Foreign key to campaigns table
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_reporting_end_date', 'reporting_end_date'),
        db.Index('idx_meta_campaign_name', 'meta_campaign_name'),
        db.Index('idx_campaign_id', 'campaign_id'),
    )
    
    def __repr__(self):
        return f'<AdSpend {self.meta_campaign_name} - {self.reporting_end_date}>'
    
    def to_dict(self):
        """Convert ad spend to dictionary"""
        return {
            'id': self.id,
            'reporting_end_date': self.reporting_end_date.isoformat() if self.reporting_end_date else None,
            'meta_campaign_name': self.meta_campaign_name,
            'ad_level': self.ad_level,
            'spend_amount': self.spend_amount,
            'is_new': self.is_new,
            'campaign_id': self.campaign_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def parse_excel_date(value):
        """Parse date from Excel (could be serial number or string)"""
        if value is None:
            return None
            
        # If it's a number (Excel serial date)
        if isinstance(value, (int, float)):
            from datetime import datetime, timedelta
            excel_base_date = datetime(1899, 12, 30)
            dt = excel_base_date + timedelta(days=value)
            return dt.date()
        
        # If it's already a date/datetime
        if hasattr(value, 'date'):
            return value.date()
        if hasattr(value, 'year') and hasattr(value, 'month'):
            return value
            
        # If it's a string, try to parse it
        if isinstance(value, str):
            try:
                dt = datetime.strptime(value, '%Y-%m-%d')
                return dt.date()
            except:
                try:
                    dt = datetime.strptime(value, '%d/%m/%Y')
                    return dt.date()
                except:
                    return None
        
        return None