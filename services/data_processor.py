"""
Data processing service for handling file uploads
"""

import pandas as pd
import logging
from datetime import datetime, timedelta
from app import db
from models import (
    Application, FLGData, AdSpend, Product, Campaign,
    StatusMapping, FLGMetaMapping
)
import os
import numpy as np

logger = logging.getLogger(__name__)

class DataProcessor:
    """Service for processing uploaded data files"""
    
    def process_applications_file(self, filepath):
        """Process applications (affordability check) Excel file"""
        try:
            # Read Excel file with both sheets
            xls = pd.ExcelFile(filepath)
            
            passed_count = 0
            failed_count = 0
            total_processed = 0
            
            # Process passed sheet
            if 'Affordability data - passed' in xls.sheet_names:
                df_passed = pd.read_excel(xls, 'Affordability data - passed')
                passed_count = self._process_applications_sheet(df_passed, 'passed')
                total_processed += passed_count
            
            # Process failed sheet
            if 'Affordability data - failed' in xls.sheet_names:
                df_failed = pd.read_excel(xls, 'Affordability data - failed')
                failed_count = self._process_applications_sheet(df_failed, 'failed')
                total_processed += failed_count
            
            db.session.commit()
            
            return {
                'records_processed': total_processed,
                'passed_count': passed_count,
                'failed_count': failed_count
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing applications file: {e}")
            raise
    
    def _process_applications_sheet(self, df, affordability_result):
        """Process a single sheet of applications data"""
        try:
            # Find the header row
            header_row = None
            for idx, row in df.iterrows():
                # Convert all values to string for comparison
                row_str = ' '.join([str(v) for v in row.values if pd.notna(v)])
                if 'DateTime' in row_str:
                    header_row = idx
                    break
            
            if header_row is None:
                logger.warning("Could not find header row in applications sheet")
                return 0
            
            # Set correct column names
            df.columns = df.iloc[header_row]
            df = df[header_row + 1:].reset_index(drop=True)
            
            # Clean column names
            df.columns = [str(col).strip() for col in df.columns]
            
            # Process each row
            count = 0
            for _, row in df.iterrows():
                try:
                    # Skip empty rows - check if Lead ID is empty
                    lead_id_raw = row.get('Lead ID')
                    if pd.isna(lead_id_raw) or lead_id_raw == '' or lead_id_raw is None:
                        continue
                    
                    # Convert Lead ID safely
                    lead_id = None
                    if isinstance(lead_id_raw, (int, float)) and not pd.isna(lead_id_raw):
                        # Handle numeric lead IDs
                        lead_id = str(int(lead_id_raw))
                    elif isinstance(lead_id_raw, str) and lead_id_raw.strip():
                        # Handle string lead IDs
                        lead_id = lead_id_raw.strip()
                    
                    if not lead_id:
                        continue
                    
                    # Check if application already exists
                    existing = Application.query.filter_by(lead_id=lead_id).first()
                    
                    if existing:
                        # Update existing record
                        app = existing
                    else:
                        # Create new record
                        app = Application()
                    
                    # Set fields
                    app.lead_id = lead_id
                    app.datetime = self._parse_datetime_safe(row.get('DateTime'))
                    app.status = str(row.get('Status')) if pd.notna(row.get('Status')) else None
                    app.user = str(row.get('User')) if pd.notna(row.get('User')) else None
                    app.lead_datetime = self._parse_datetime_safe(row.get('LeadDateTime'))
                    app.lead_name = str(row.get('LeadName')) if pd.notna(row.get('LeadName')) else None
                    app.lead_postcode = str(row.get('LeadPostcode')) if pd.notna(row.get('LeadPostcode')) else None
                    app.lead_introducer = str(row.get('LeadIntroducer')) if pd.notna(row.get('LeadIntroducer')) else None
                    app.lead_partner = str(row.get('LeadPartner')) if pd.notna(row.get('LeadPartner')) else None
                    app.lead_cost = self._parse_float(row.get('LeadCost'))
                    app.lead_value = self._parse_float(row.get('LeadValue'))
                    app.current_status = str(row.get('CurrentStatus')) if pd.notna(row.get('CurrentStatus')) else None
                    app.affordability_result = affordability_result
                    
                    if not existing:
                        db.session.add(app)
                    
                    count += 1
                    
                except Exception as row_error:
                    logger.warning(f"Error processing row: {row_error}")
                    continue
            
            return count
            
        except Exception as e:
            logger.error(f"Error processing applications sheet: {e}")
            raise
    
    def process_flg_data_file(self, filepath):
        """Process FLG data Excel file"""
        try:
            # Read Excel file
            df = pd.read_excel(filepath, sheet_name='ALL')
            
            # Find the header row
            header_row = None
            for idx, row in df.iterrows():
                # Convert all values to string for comparison
                row_str = ' '.join([str(v) for v in row.values if pd.notna(v)])
                if 'Reference' in row_str:
                    header_row = idx
                    break
            
            if header_row is None:
                raise ValueError("Could not find header row in FLG data file")
            
            # Set correct column names
            df.columns = df.iloc[header_row]
            df = df[header_row + 1:].reset_index(drop=True)
            
            # Clean column names
            df.columns = [str(col).strip() for col in df.columns]
            
            # Track new products and unmapped sources
            new_products = set()
            unmapped_sources = set()
            
            # Process each row
            count = 0
            for _, row in df.iterrows():
                try:
                    # Skip empty rows
                    if pd.isna(row.get('Reference')):
                        continue
                    
                    # Handle Reference conversion
                    reference = str(row.get('Reference'))
                    existing = FLGData.query.filter_by(reference=reference).first()
                    
                    if existing:
                        flg = existing
                    else:
                        flg = FLGData()
                    
                    # Set fields
                    flg.reference = reference
                    flg.received_datetime = self._parse_datetime_safe(row.get('ReceivedDateTime'))
                    flg.status = str(row.get('Status')) if pd.notna(row.get('Status')) else None
                    flg.marketing_source = str(row.get('MarketingSource')) if pd.notna(row.get('MarketingSource')) else None
                    flg.data5_value = self._parse_float(row.get('Data5'))
                    flg.data6_payment_type = str(row.get('Data6')) if pd.notna(row.get('Data6')) else None
                    flg.data7_value = self._parse_float(row.get('Data7'))
                    flg.data8_value = self._parse_float(row.get('Data8'))
                    flg.data10_value = self._parse_float(row.get('Data10'))
                    flg.data29_product_description = str(row.get('Data29')) if pd.notna(row.get('Data29')) else None
                    
                    # Calculate sale value
                    flg.sale_value = flg.calculate_sale_value()
                    
                    # Extract product from description
                    if flg.data29_product_description:
                        product_name = Product.extract_product_from_description(flg.data29_product_description)
                        flg.product_name = product_name
                        
                        # Check if product exists in database
                        product = Product.query.filter_by(name=product_name).first()
                        if not product and product_name != 'Other':
                            new_products.add(product_name)
                    
                    # Map marketing source to campaign
                    if flg.marketing_source:
                        mapping = FLGMetaMapping.query.filter_by(flg_name=flg.marketing_source).first()
                        if mapping:
                            flg.campaign_name = mapping.meta_name
                        else:
                            unmapped_sources.add(flg.marketing_source)
                    
                    if not existing:
                        db.session.add(flg)
                    
                    count += 1
                    
                except Exception as row_error:
                    logger.warning(f"Error processing FLG row: {row_error}")
                    continue
            
            # Create new products
            for product_name in new_products:
                product = Product(name=product_name)
                db.session.add(product)
            
            db.session.commit()
            
            return {
                'records_processed': count,
                'new_products': list(new_products),
                'unmapped_sources': list(unmapped_sources)
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing FLG data file: {e}")
            raise
    
    def process_ad_spend_file(self, filepath):
        """Process ad spend Excel file"""
        try:
            # Try to read the Excel file and find Meta sheet
            xls = pd.ExcelFile(filepath)
            
            # Look for Meta sheet (case insensitive)
            meta_sheet = None
            for sheet in xls.sheet_names:
                if sheet.lower() == 'meta':
                    meta_sheet = sheet
                    break
            
            if not meta_sheet:
                # If no Meta sheet, try the first sheet
                meta_sheet = xls.sheet_names[0] if xls.sheet_names else None
                logger.warning(f"No 'Meta' sheet found, using sheet: {meta_sheet}")
            
            if not meta_sheet:
                raise ValueError("No sheets found in Excel file")
            
            # Read the sheet
            df = pd.read_excel(filepath, sheet_name=meta_sheet)
            
            # Find the header row by looking for key columns
            header_row = None
            for idx in range(min(10, len(df))):  # Check first 10 rows
                row_values = df.iloc[idx].astype(str).tolist()
                row_str = ' '.join(row_values)
                # Look for variations of column names
                if any(term in row_str.lower() for term in ['reporting', 'campaign', 'spend']):
                    header_row = idx
                    break
            
            if header_row is None:
                # Try first row as header
                header_row = 0
                logger.warning("Could not find header row, using first row")
            
            # Read again with correct header row
            df = pd.read_excel(filepath, sheet_name=meta_sheet, header=header_row)
            
            # Clean and standardize column names
            df.columns = [str(col).strip() for col in df.columns]
            
            # Try different column name variations
            column_mappings = [
                {
                    'Reporting ends': 'reporting_date',
                    'Meta campaign name': 'campaign_name',
                    'Ad level': 'ad_level',
                    'Spend': 'spend_amount',
                    'New -versus last weel?': 'is_new'
                },
                {
                    'Reporting end': 'reporting_date',
                    'Campaign name': 'campaign_name',
                    'Ad level': 'ad_level',
                    'Amount spent': 'spend_amount',
                    'New': 'is_new'
                },
                {
                    'Date': 'reporting_date',
                    'Campaign': 'campaign_name',
                    'Ad': 'ad_level',
                    'Cost': 'spend_amount',
                    'New?': 'is_new'
                }
            ]
            
            # Try each mapping until we find matching columns
            mapped = False
            for mapping in column_mappings:
                if any(col in df.columns for col in mapping.keys()):
                    df.rename(columns=mapping, inplace=True)
                    mapped = True
                    break
            
            if not mapped:
                logger.warning(f"Could not map columns. Found columns: {list(df.columns)}")
            
            # Track new campaigns
            new_campaigns = set()
            total_spend = 0
            
            # Process each row
            count = 0
            for _, row in df.iterrows():
                try:
                    # Skip empty rows
                    campaign_name = row.get('campaign_name')
                    spend_amount = row.get('spend_amount')
                    
                    if pd.isna(campaign_name) or pd.isna(spend_amount):
                        continue
                    
                    # Parse data
                    reporting_date = self._parse_date_safe(row.get('reporting_date'))
                    if not reporting_date:
                        continue
                    
                    meta_campaign_name = str(campaign_name).strip()
                    ad_level = str(row.get('ad_level')) if pd.notna(row.get('ad_level')) else None
                    spend_amount = self._parse_float(spend_amount)
                    
                    if not spend_amount or spend_amount == 0:
                        continue
                    
                    # Parse is_new field
                    is_new_val = row.get('is_new')
                    is_new = False
                    if pd.notna(is_new_val):
                        is_new_str = str(is_new_val).upper()
                        is_new = is_new_str in ['NEW', 'TRUE', 'YES', '1']
                    
                    # Check if campaign exists
                    campaign = Campaign.query.filter_by(meta_name=meta_campaign_name).first()
                    if not campaign:
                        campaign = Campaign(
                            name=meta_campaign_name,
                            meta_name=meta_campaign_name
                        )
                        db.session.add(campaign)
                        new_campaigns.add(meta_campaign_name)
                    
                    # Create ad spend record
                    ad_spend = AdSpend(
                        reporting_end_date=reporting_date,
                        meta_campaign_name=meta_campaign_name,
                        ad_level=ad_level,
                        spend_amount=spend_amount,
                        is_new=is_new,
                        campaign=campaign
                    )
                    
                    db.session.add(ad_spend)
                    total_spend += spend_amount
                    count += 1
                    
                except Exception as row_error:
                    logger.warning(f"Error processing ad spend row: {row_error}")
                    continue
            
            db.session.commit()
            
            return {
                'records_processed': count,
                'new_campaigns': list(new_campaigns),
                'total_spend': total_spend
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing ad spend file: {e}")
            raise
    
    def process_mapping_file(self, filepath):
        """Process FLG to Meta name mapping file (Word document)"""
        try:
            # Check file extension
            file_ext = os.path.splitext(filepath)[1].lower()
            
            mappings_created = 0
            mappings_updated = 0
            
            if file_ext in ['.docx', '.doc']:
                # Process Word document
                import docx
                doc = docx.Document(filepath)
                
                # Look for table in document
                for table in doc.tables:
                    for row_idx, row in enumerate(table.rows):
                        # Skip header row
                        if row_idx == 0:
                            continue
                        
                        cells = row.cells
                        if len(cells) >= 2:
                            flg_name = cells[0].text.strip()
                            meta_name = cells[1].text.strip()
                            
                            if flg_name and meta_name:
                                # Check if mapping exists
                                existing = FLGMetaMapping.query.filter_by(flg_name=flg_name).first()
                                
                                if existing:
                                    existing.meta_name = meta_name
                                    mappings_updated += 1
                                else:
                                    mapping = FLGMetaMapping(
                                        flg_name=flg_name,
                                        meta_name=meta_name
                                    )
                                    db.session.add(mapping)
                                    mappings_created += 1
            
            elif file_ext in ['.xlsx', '.xls']:
                # Process Excel file
                df = pd.read_excel(filepath)
                
                # Assume first two columns are FLG name and Meta name
                for _, row in df.iterrows():
                    flg_name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
                    meta_name = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else None
                    
                    if flg_name and meta_name:
                        existing = FLGMetaMapping.query.filter_by(flg_name=flg_name).first()
                        
                        if existing:
                            existing.meta_name = meta_name
                            mappings_updated += 1
                        else:
                            mapping = FLGMetaMapping(
                                flg_name=flg_name,
                                meta_name=meta_name
                            )
                            db.session.add(mapping)
                            mappings_created += 1
            
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            db.session.commit()
            
            return {
                'mappings_created': mappings_created,
                'mappings_updated': mappings_updated
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing mapping file: {e}")
            raise
    
    def _parse_float(self, value):
        """Safely parse float value"""
        if pd.isna(value):
            return None
        try:
            # Handle string values that might have currency symbols or commas
            if isinstance(value, str):
                value = value.replace('£', '').replace('$', '').replace(',', '').strip()
            return float(value)
        except:
            return None
    
    def _parse_datetime_safe(self, value):
        """Safely parse datetime using model's method"""
        if pd.isna(value) or value is None:
            return None
            
        # If it's a number (Excel serial date)
        if isinstance(value, (int, float)):
            excel_base_date = datetime(1899, 12, 30)
            return excel_base_date + timedelta(days=value)
        
        # If it's already a datetime
        if isinstance(value, datetime):
            return value
            
        # If it's a string, try to parse it
        if isinstance(value, str):
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y']:
                try:
                    return datetime.strptime(value, fmt)
                except:
                    continue
        
        return None
    
    def _parse_date_safe(self, value):
        """Safely parse date for ad spend"""
        if pd.isna(value) or value is None:
            return None
            
        # If it's a number (Excel serial date)
        if isinstance(value, (int, float)):
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
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.date()
                except:
                    continue
        
        return None