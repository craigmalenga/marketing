"""
Database models for Marketing Analytics Platform
"""

from .campaign import Campaign
from .product import Product
from .status_mapping import StatusMapping
from .application import Application
from .flg_data import FLGData
from .ad_spend import AdSpend
from .flg_meta_mapping import FLGMetaMapping

__all__ = [
    'Campaign',
    'Product', 
    'StatusMapping',
    'Application',
    'FLGData',
    'AdSpend',
    'FLGMetaMapping'
]