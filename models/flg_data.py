"""
FLG Data model
"""

from app import db
from datetime import datetime
from sqlalchemy import func

class FLGData(db.Model):
    """FLG Data model for storing lead and sales information"""
    __tablename__ = 'flg_data'
    
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), nullable=False)  # Lead ID
    received_datetime = db.Column(db.DateTime)
    status = db.Column(db.String(200))
    marketing_source = db.Column(db.String(200))
    data5_value = db.Column(db.Float)  # Sale value
    data6_payment_type = db.Column(db.String(50))  # Monthly, Four Weekly, etc.
    data7_value = db.Column(db.Float)
    data8_value = db.Column(db.Float)
    data10_value = db.Column(db.Float)
    data29_product_description = db.Column(db.Text)
    sale_value = db.Column(db.Float)
    
    # Derived fields
    product_name = db.Column(db.String(200))  # Extracted from description
    campaign_name = db.Column(db.String(200))  # Mapped from marketing source
    
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_reference', 'reference'),
        db.Index('idx_received_datetime', 'received_datetime'),
        db.Index('idx_status', 'status'),
        db.Index('idx_product_name', 'product_name'),
        db.Index('idx_campaign_name', 'campaign_name'),
    )
    
    def __repr__(self):
        return f'<FLGData {self.reference} - {self.status}>'
    
    def to_dict(self):
        """Convert FLG data to dictionary"""
        return {
            'id': self.id,
            'reference': self.reference,
            'received_datetime': self.received_datetime.isoformat() if self.received_datetime else None,
            'status': self.status,
            'marketing_source': self.marketing_source,
            'data5_value': self.data5_value,
            'data6_payment_type': self.data6_payment_type,
            'data7_value': self.data7_value,
            'data8_value': self.data8_value,
            'data10_value': self.data10_value,
            'data29_product_description': self.data29_product_description,
            'sale_value': self.sale_value,
            'product_name': self.product_name,
            'campaign_name': self.campaign_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def calculate_sale_value(self):
        """Calculate sale value based on payment type and values"""
        if not self.data5_value:
            return 0
            
        # Logic based on Excel analysis
        if self.data6_payment_type == 'Monthly':
            # Monthly payments - multiply by term or use data10
            return self.data10_value if self.data10_value else self.data5_value
        elif self.data6_payment_type == 'Four Weekly':
            # Four weekly payments - use data10 or calculate
            return self.data10_value if self.data10_value else self.data5_value
        else:
            # Default to data5 value
            return self.data5_value
    
    @staticmethod
    def parse_excel_datetime(value):
        """Parse datetime from Excel (could be serial number or string)"""
        if value is None:
            return None
            
        # If it's a number (Excel serial date)
        if isinstance(value, (int, float)):
            from datetime import datetime, timedelta
            excel_base_date = datetime(1899, 12, 30)
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