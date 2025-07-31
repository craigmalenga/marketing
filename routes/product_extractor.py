"""
Product extraction service - Replicates Excel VBA macro functionality
services/product_extractor.py
"""

import re
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class ProductExtractor:
    """
    Service to extract product names and prices from descriptions
    Replicates the VBA macro 'Populate_product_types_and_prices()'
    """
    
    # Product patterns matching Excel logic
    PRODUCT_PATTERNS = {
        'Sofa - Aldis': [
            r'\baldis\b',
            r'aldis\s*sofa',
            r'sofa\s*aldis'
        ],
        'Sofa - Kyle': [
            r'\bkyle\b',
            r'kyle\s*sofa',
            r'sofa\s*kyle'
        ],
        'Sofa - Hamilton': [
            r'\bhamilton\b',
            r'hamilton\s*sofa',
            r'sofa\s*hamilton'
        ],
        'Sofa - Lawson': [
            r'\blawson\b',
            r'lawson\s*sofa',
            r'sofa\s*lawson'
        ],
        'Sofa - Lucy': [
            r'\blucy\b',
            r'lucy\s*sofa',
            r'sofa\s*lucy'
        ],
        'Sofa - Roma': [
            r'\broma\b',
            r'roma\s*sofa',
            r'sofa\s*roma'
        ],
        'Rattan': [
            r'\brattan\b',
            r'rattan\s*furniture',
            r'rattan\s*set'
        ],
        'Bed': [
            r'\bbed\b(?!\s*room)',
            r'\bmattress\b',
            r'\bdivan\b',
            r'bed\s*frame'
        ],
        'Dining set': [
            r'dining\s*set',
            r'dining\s*table',
            r'dining\s*chairs',
            r'table\s*and\s*chairs'
        ],
        'Cooker': [
            r'\bcooker\b',
            r'\boven\b',
            r'\bhob\b',
            r'\brange\b',
            r'cooking\s*range'
        ],
        'Fridge freezer': [
            r'fridge\s*freezer',
            r'fridge\s*/\s*freezer',
            r'refrigerator',
            r'american\s*style\s*fridge'
        ],
        'Washer dryer': [
            r'washer\s*dryer',
            r'washer\s*/\s*dryer',
            r'washing\s*machine',
            r'washer'
        ],
        'Dish washer': [
            r'dish\s*washer',
            r'dishwasher',
            r'dish\s*washing\s*machine'
        ],
        'Microwave': [
            r'\bmicrowave\b',
            r'micro\s*wave'
        ],
        'TV': [
            r'\btv\b',
            r'\btelevision\b',
            r'smart\s*tv',
            r'\d+"\s*tv',
            r'tv\s*\d+"'
        ],
        'Console': [
            r'\bplaystation\b',
            r'\bps\d\b',
            r'\bxbox\b',
            r'\bnintendo\b',
            r'gaming\s*console',
            r'games\s*console'
        ],
        'Laptop': [
            r'\blaptop\b',
            r'\bnotebook\b',
            r'\bmacbook\b',
            r'\bchromebook\b'
        ],
        'Vacuum': [
            r'\bvacuum\b',
            r'\bhoover\b',
            r'\bdyson\b(?!\s*hair)',
            r'vacuum\s*cleaner'
        ],
        'Hot tub': [
            r'hot\s*tub',
            r'spa\s*pool',
            r'jacuzzi',
            r'inflatable\s*spa'
        ],
        'BBQ': [
            r'\bbbq\b',
            r'\bbarbecue\b',
            r'\bgrill\b(?!\s*pan)',
            r'charcoal\s*grill',
            r'gas\s*grill'
        ],
        'Air fryer': [
            r'air\s*fryer',
            r'airfryer',
            r'air\s*fry'
        ],
        'Ninja products': [
            r'\bninja\b',
            r'ninja\s*foodi',
            r'ninja\s*air\s*fryer'
        ],
        'Kitchen Bundle': [
            r'kitchen\s*bundle',
            r'appliance\s*bundle',
            r'kitchen\s*set',
            r'appliance\s*package'
        ],
        'Sofa - other': [
            r'\bsofa\b',
            r'\bcouch\b',
            r'\bsettee\b',
            r'corner\s*sofa',
            r'recliner\s*sofa'
        ]
    }
    
    # Price extraction patterns
    PRICE_PATTERNS = [
        r'£\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # £1,234.56
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:pounds?|gbp)',  # 1234.56 pounds
        r'(?:price|cost|total|amount):\s*£?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # price: 1234.56
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:each|per\s*item)',  # 1234.56 each
        r'(?:rrp|retail):\s*£?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # RRP: 1234.56
    ]
    
    @classmethod
    def extract_products_and_prices(cls, description: str) -> List[Tuple[str, float]]:
        """
        Extract product names and prices from description
        Returns list of (product_name, price) tuples
        """
        if not description:
            return [('Other', 0.0)]
        
        description_lower = description.lower()
        found_products = []
        
        # Extract products - check specific sofas first
        specific_sofas = ['Sofa - Aldis', 'Sofa - Kyle', 'Sofa - Hamilton', 
                         'Sofa - Lawson', 'Sofa - Lucy', 'Sofa - Roma']
        
        # Check for specific sofa models first
        for product_name in specific_sofas:
            patterns = cls.PRODUCT_PATTERNS[product_name]
            for pattern in patterns:
                if re.search(pattern, description_lower, re.IGNORECASE):
                    found_products.append(product_name)
                    break
        
        # If no specific sofa found, check other products
        if not found_products:
            for product_name, patterns in cls.PRODUCT_PATTERNS.items():
                if product_name in specific_sofas:
                    continue  # Skip specific sofas
                
                for pattern in patterns:
                    if re.search(pattern, description_lower, re.IGNORECASE):
                        # For generic sofa, only add if no specific sofa found
                        if product_name == 'Sofa - other' and any('Sofa' in p for p in found_products):
                            continue
                        found_products.append(product_name)
                        break
        
        # Extract prices
        prices = cls._extract_prices(description)
        
        # If no products found, mark as Other
        if not found_products:
            found_products = ['Other']
        
        # Match products with prices
        return cls._match_products_prices(found_products, prices, description)
    
    @classmethod
    def _extract_prices(cls, description: str) -> List[float]:
        """Extract all prices from description"""
        prices = []
        
        for pattern in cls.PRICE_PATTERNS:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                try:
                    price_str = match.group(1)
                    # Remove commas and convert to float
                    price = float(price_str.replace(',', ''))
                    if price > 0:  # Only add positive prices
                        prices.append(price)
                except (ValueError, IndexError):
                    continue
        
        # Remove duplicates and sort
        prices = sorted(list(set(prices)), reverse=True)
        
        return prices
    
    @classmethod
    def _match_products_prices(cls, products: List[str], prices: List[float], 
                             description: str) -> List[Tuple[str, float]]:
        """
        Match products with prices based on Excel logic
        """
        result = []
        
        # If we have exact match of products and prices
        if len(products) == len(prices):
            for product, price in zip(products, prices):
                result.append((product, price))
        
        # If more prices than products
        elif len(prices) > len(products):
            # Assign highest prices to products
            for i, product in enumerate(products):
                if i < len(prices):
                    result.append((product, prices[i]))
                else:
                    result.append((product, 0.0))
        
        # If more products than prices
        else:
            if prices:
                # Check if description mentions "bundle" or "set"
                if re.search(r'\b(?:bundle|set|package|collection)\b', description, re.IGNORECASE):
                    # Likely a bundle - distribute total price
                    total_price = sum(prices)
                    price_per_item = total_price / len(products)
                    for product in products:
                        result.append((product, price_per_item))
                else:
                    # Assign available prices, rest get 0
                    for i, product in enumerate(products):
                        if i < len(prices):
                            result.append((product, prices[i]))
                        else:
                            result.append((product, 0.0))
            else:
                # No prices found
                for product in products:
                    result.append((product, 0.0))
        
        return result
    
    @classmethod
    def extract_single_product(cls, description: str) -> str:
        """
        Extract a single primary product from description
        Used for backward compatibility
        """
        products_prices = cls.extract_products_and_prices(description)
        if products_prices:
            return products_prices[0][0]  # Return first product
        return 'Other'
    
    @classmethod
    def get_total_value(cls, description: str) -> float:
        """
        Get total value of all products in description
        """
        products_prices = cls.extract_products_and_prices(description)
        return sum(price for _, price in products_prices)
    
    @classmethod
    def format_products_for_display(cls, products_prices: List[Tuple[str, float]]) -> str:
        """
        Format products and prices for display
        """
        if not products_prices:
            return "No products found"
        
        parts = []
        for product, price in products_prices:
            if price > 0:
                parts.append(f"{product} (£{price:,.2f})")
            else:
                parts.append(product)
        
        return " + ".join(parts)