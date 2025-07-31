"""
Product model
"""

from app import db
from datetime import datetime
from sqlalchemy import func

class Product(db.Model):
    """Product model for storing product information"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=func.now())
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    def to_dict(self):
        """Convert product to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def extract_product_from_description(description):
        """Extract product name from FLG description field"""
        if not description:
            return None
            
        # Define product mapping based on keywords
        product_mappings = {
            'Sofa - Aldis': ['aldis'],
            'Sofa - Kyle': ['kyle'],
            'Sofa - Hamilton': ['hamilton'],
            'Sofa - Lawson': ['lawson'],
            'Sofa - Lucy': ['lucy'],
            'Sofa - Roma': ['roma'],
            'Sofa - other': ['sofa'],  # Generic sofa catch-all
            'Rattan': ['rattan'],
            'Bed': ['bed', 'mattress', 'divan'],
            'Cooker': ['cooker', 'oven', 'hob'],
            'Fridge freezer': ['fridge', 'freezer'],
            'TV': ['tv', 'television', 'smart tv'],
            'Console': ['console', 'playstation', 'xbox', 'nintendo'],
            'Hot tub': ['hot tub', 'spa'],
            'Washer dryer': ['washer', 'washing machine', 'dryer'],
            'Vacuum': ['vacuum', 'hoover', 'dyson'],
            'Ninja products': ['ninja'],
            'Laptop': ['laptop', 'notebook', 'macbook'],
            'BBQ': ['bbq', 'barbecue', 'grill'],
            'Air fryer': ['air fryer', 'airfryer'],
            'Microwave': ['microwave'],
            'Dish washer': ['dishwasher', 'dish washer'],
            'Kitchen Bundle': ['kitchen bundle', 'kitchen set'],
            'Dining set': ['dining', 'table', 'chairs']
        }
        
        description_lower = description.lower()
        
        # Check each product mapping
        for product_name, keywords in product_mappings.items():
            for keyword in keywords:
                if keyword in description_lower:
                    # Special handling for sofas to identify specific models
                    if product_name == 'Sofa - other' and any(model in description_lower for model in ['aldis', 'kyle', 'hamilton', 'lawson', 'lucy', 'roma']):
                        continue  # Skip generic sofa if specific model found
                    return product_name
        
        # If no match found, try to categorize generically
        return 'Other'