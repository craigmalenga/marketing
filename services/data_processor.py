"""
Data processing service for handling file uploads - Enhanced version with better date parsing
services/data_processor.py
"""

import pandas as pd
import logging
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from models import (
    Application, FLGData, AdSpend, Product, Campaign,
    StatusMapping, FLGMetaMapping
)
from services.product_extractor import ProductExtractor
import os
import numpy as np
import re

logger = logging.getLogger(__name__)

class DataProcessor:
    """Service for processing uploaded data files"""
    
    def __init__(self):
        # Track Lead IDs that passed/failed affordability checks
        self.passed_lead_ids = set()
        self.failed_lead_ids = set()
        # Track processing state
        self.processing_state = {
            'affordability_loaded': False,
            'flg_loaded': False,
            'mappings_loaded': False
        }
    
    def validate_processing_order(self):
        """Validate that files are being processed in correct order"""
        warnings = []
        
        if not self.processing_state['mappings_loaded']:
            # Check if any mappings exist in database
            mapping_count = FLGMetaMapping.query.count()
            if mapping_count == 0:
                warnings.append("No FLG to Meta mappings loaded. Upload mapping file first for best results.")
        
        if not self.processing_state['affordability_loaded']:
            if not self.passed_lead_ids and not self.failed_lead_ids:
                warnings.append("No affordability data loaded. Applications will not be created.")
        
        return warnings
    
    def process_applications_file(self, filepath):
        """Process affordability check files - Extract only Lead IDs"""
        try:
            file_ext = os.path.splitext(filepath)[1].lower()
            filename_lower = os.path.basename(filepath).lower()
            
            if file_ext == '.csv':
                # Read CSV file
                df = pd.read_csv(filepath)
                
                # Check if Lead ID column exists
                lead_id_column = None
                for col in df.columns:
                    if 'lead' in col.lower() and 'id' in col.lower():
                        lead_id_column = col
                        break
                
                if not lead_id_column:
                    raise ValueError("Lead ID column not found in CSV file. Expected column containing 'Lead' and 'ID'")
                
                # Extract Lead IDs
                lead_ids = df[lead_id_column].dropna().unique()
                count = len(lead_ids)
                
                # Normalize Lead IDs to strings
                normalized_ids = set()
                for lid in lead_ids:
                    if isinstance(lid, (int, float)):
                        normalized_ids.add(str(int(lid)))
                    else:
                        normalized_ids.add(str(lid).strip())
                
                # Determine if passed or failed
                if 'passed' in filename_lower:
                    self.passed_lead_ids.update(normalized_ids)
                    self.processing_state['affordability_loaded'] = True
                    logger.info(f"Loaded {count} passed Lead IDs")
                    return {
                        'records_processed': count,
                        'passed_count': count,
                        'failed_count': 0,
                        'file_type': 'CSV - Passed Lead IDs'
                    }
                elif 'failed' in filename_lower:
                    self.failed_lead_ids.update(normalized_ids)
                    self.processing_state['affordability_loaded'] = True
                    logger.info(f"Loaded {count} failed Lead IDs")
                    return {
                        'records_processed': count,
                        'passed_count': 0,
                        'failed_count': count,
                        'file_type': 'CSV - Failed Lead IDs'
                    }
                else:
                    logger.warning("Could not determine if passed or failed from filename")
                    return {
                        'records_processed': 0,
                        'passed_count': 0,
                        'failed_count': 0,
                        'file_type': 'CSV - Unknown',
                        'error': 'Could not determine if passed or failed from filename. File should contain "passed" or "failed" in name.'
                    }
            
            else:
                # Original Excel processing (if still needed)
                return self._process_applications_excel(filepath)
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing applications file: {e}")
            raise
    
    def _process_applications_excel(self, filepath):
        """Process Excel affordability files (legacy support)"""
        try:
            xls = pd.ExcelFile(filepath)
            
            passed_count = 0
            failed_count = 0
            
            # Process passed sheet
            if 'Affordability data - passed' in xls.sheet_names:
                df_passed = pd.read_excel(xls, 'Affordability data - passed')
                if 'Lead ID' in df_passed.columns:
                    lead_ids = df_passed['Lead ID'].dropna().unique()
                    normalized_ids = set()
                    for lid in lead_ids:
                        if isinstance(lid, (int, float)):
                            normalized_ids.add(str(int(lid)))
                        else:
                            normalized_ids.add(str(lid).strip())
                    self.passed_lead_ids.update(normalized_ids)
                    passed_count = len(normalized_ids)
            
            # Process failed sheet
            if 'Affordability data - failed' in xls.sheet_names:
                df_failed = pd.read_excel(xls, 'Affordability data - failed')
                if 'Lead ID' in df_failed.columns:
                    lead_ids = df_failed['Lead ID'].dropna().unique()
                    normalized_ids = set()
                    for lid in lead_ids:
                        if isinstance(lid, (int, float)):
                            normalized_ids.add(str(int(lid)))
                        else:
                            normalized_ids.add(str(lid).strip())
                    self.failed_lead_ids.update(normalized_ids)
                    failed_count = len(normalized_ids)
            
            self.processing_state['affordability_loaded'] = True
            
            return {
                'records_processed': passed_count + failed_count,
                'passed_count': passed_count,
                'failed_count': failed_count,
                'file_type': 'Excel'
            }
            
        except Exception as e:
            logger.error(f"Error processing Excel applications file: {e}")
            raise
    
    def process_flg_data_file(self, filepath):
        """Process FLG data (all_leads_all_time) - Main data source"""
        try:
            # Check processing order
            warnings = self.validate_processing_order()
            
            file_ext = os.path.splitext(filepath)[1].lower()
            
            if file_ext == '.csv':
                # Read CSV file
                df = pd.read_csv(filepath)
                
                # Map columns flexibly
                column_mapping = self._map_csv_columns(df.columns)
                
                if not column_mapping['lead_id']:
                    raise ValueError("Lead ID column not found in CSV file")
                
                # Process data
                new_products = set()
                unmapped_sources = set()
                count = 0
                applications_created = 0
                products_extracted = 0
                
                for _, row in df.iterrows():
                    try:
                        # Get Lead ID
                        lead_id_raw = row.get(column_mapping['lead_id'])
                        if pd.isna(lead_id_raw):
                            continue
                        
                        # Normalize Lead ID
                        if isinstance(lead_id_raw, (int, float)):
                            lead_id = str(int(lead_id_raw))
                        else:
                            lead_id = str(lead_id_raw).strip()
                        
                        # Create/Update FLG record
                        existing_flg = FLGData.query.filter_by(reference=lead_id).first()
                        if existing_flg:
                            flg = existing_flg
                        else:
                            flg = FLGData()
                        
                        # Set FLG fields
                        flg.reference = lead_id
                        
                        if column_mapping['datetime']:
                            flg.received_datetime = self._parse_datetime_safe(row.get(column_mapping['datetime']))
                        
                        if column_mapping['status']:
                            flg.status = str(row.get(column_mapping['status'])) if pd.notna(row.get(column_mapping['status'])) else None
                        
                        if column_mapping['marketing_source']:
                            flg.marketing_source = str(row.get(column_mapping['marketing_source'])) if pd.notna(row.get(column_mapping['marketing_source'])) else None
                        
                        if column_mapping['capital_amount']:
                            flg.data5_value = self._parse_float(row.get(column_mapping['capital_amount']))
                        
                        if column_mapping['payment_type']:
                            flg.data6_payment_type = str(row.get(column_mapping['payment_type'])) if pd.notna(row.get(column_mapping['payment_type'])) else None
                        
                        if column_mapping['total_interest']:
                            flg.data7_value = self._parse_float(row.get(column_mapping['total_interest']))
                        
                        if column_mapping['regular_repayments']:
                            flg.data8_value = self._parse_float(row.get(column_mapping['regular_repayments']))
                        
                        if column_mapping['total_amount']:
                            flg.data10_value = self._parse_float(row.get(column_mapping['total_amount']))
                        
                        if column_mapping['product_details']:
                            flg.data29_product_description = str(row.get(column_mapping['product_details'])) if pd.notna(row.get(column_mapping['product_details'])) else None
                        
                        # Calculate sale value
                        flg.sale_value = flg.calculate_sale_value()
                        
                        # Extract products using ProductExtractor
                        if flg.data29_product_description:
                            products_prices = ProductExtractor.extract_products_and_prices(flg.data29_product_description)
                            
                            # For now, use the primary product
                            if products_prices:
                                primary_product = products_prices[0][0]
                                flg.product_name = primary_product
                                products_extracted += 1
                                
                                # Check if product exists
                                product = Product.query.filter_by(name=primary_product).first()
                                if not product and primary_product != 'Other':
                                    new_products.add(primary_product)
                        
                        # Map marketing source to campaign
                        if flg.marketing_source:
                            mapping = FLGMetaMapping.query.filter_by(flg_name=flg.marketing_source).first()
                            if mapping:
                                flg.campaign_name = mapping.meta_name
                            else:
                                unmapped_sources.add(flg.marketing_source)
                        
                        if not existing_flg:
                            db.session.add(flg)
                        
                        # Create/Update Application record based on affordability result
                        affordability_result = None
                        if lead_id in self.passed_lead_ids:
                            affordability_result = 'passed'
                        elif lead_id in self.failed_lead_ids:
                            affordability_result = 'failed'
                        
                        if affordability_result:
                            existing_app = Application.query.filter_by(lead_id=lead_id).first()
                            if existing_app:
                                app = existing_app
                            else:
                                app = Application()
                                applications_created += 1
                            
                            # Set application fields from FLG data
                            app.lead_id = lead_id
                            app.datetime = flg.received_datetime
                            app.status = flg.status
                            app.lead_datetime = flg.received_datetime
                            app.lead_value = flg.data5_value
                            app.current_status = flg.status
                            app.affordability_result = affordability_result
                            app.lead_partner = flg.marketing_source
                            
                            if not existing_app:
                                db.session.add(app)
                        
                        count += 1
                        
                    except Exception as row_error:
                        logger.warning(f"Error processing FLG row: {row_error}")
                        continue
                
                # Create new products
                for product_name in new_products:
                    # Determine category based on product name
                    category = self._determine_product_category(product_name)
                    product = Product(name=product_name, category=category)
                    db.session.add(product)
                
                db.session.commit()
                
                self.processing_state['flg_loaded'] = True
                
                logger.info(f"Processed {count} FLG records, created {applications_created} applications, extracted {products_extracted} products")
                
                result = {
                    'records_processed': count,
                    'applications_created': applications_created,
                    'products_extracted': products_extracted,
                    'new_products': list(new_products),
                    'unmapped_sources': list(unmapped_sources),
                    'file_type': 'CSV - All Leads'
                }
                
                if warnings:
                    result['warnings'] = warnings
                
                return result
                
            else:
                # Excel processing
                return self._process_flg_excel(filepath)
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing FLG data file: {e}")
            raise
    
    def _map_csv_columns(self, columns):
        """Map CSV columns to expected fields"""
        column_mapping = {
            'lead_id': None,
            'datetime': None,
            'status': None,
            'marketing_source': None,
            'capital_amount': None,
            'payment_type': None,
            'total_interest': None,
            'regular_repayments': None,
            'total_amount': None,
            'product_details': None
        }
        
        for col in columns:
            col_lower = col.lower().strip()
            
            # Lead ID
            if 'lead' in col_lower and 'id' in col_lower:
                column_mapping['lead_id'] = col
            
            # Date/time
            elif any(term in col_lower for term in ['date', 'time', 'received', 'activity']):
                column_mapping['datetime'] = col
            
            # Status
            elif 'status' in col_lower:
                column_mapping['status'] = col
            
            # Marketing source
            elif any(term in col_lower for term in ['marketing', 'source', 'channel']):
                column_mapping['marketing_source'] = col
            
            # Capital amount
            elif any(term in col_lower for term in ['capital', 'loan', 'amount borrowed']):
                column_mapping['capital_amount'] = col
            
            # Payment type
            elif any(term in col_lower for term in ['payment', 'frequency', 'repayment type']):
                column_mapping['payment_type'] = col
            
            # Total interest
            elif any(term in col_lower for term in ['interest', 'charge']):
                column_mapping['total_interest'] = col
            
            # Regular repayments
            elif any(term in col_lower for term in ['regular', 'repayment', 'instalment']):
                column_mapping['regular_repayments'] = col
            
            # Total amount
            elif any(term in col_lower for term in ['total', 'pay', 'repay']):
                column_mapping['total_amount'] = col
            
            # Product details
            elif any(term in col_lower for term in ['product', 'description', 'details', 'item']):
                column_mapping['product_details'] = col
        
        return column_mapping
    
    def _determine_product_category(self, product_name):
        """Determine product category based on product name"""
        if 'Sofa' in product_name:
            return 'Sofa'
        elif product_name in ['Rattan', 'Bed', 'Dining set']:
            return 'Furniture'
        elif product_name in ['Cooker', 'Fridge freezer', 'Washer dryer', 'Dish washer', 
                              'Microwave', 'Vacuum', 'Air fryer', 'Ninja products', 
                              'Kitchen Bundle']:
            return 'Appliances'
        elif product_name in ['TV', 'Console', 'Laptop']:
            return 'Electronics'
        elif product_name == 'Hot tub':
            return 'Leisure'
        elif product_name == 'BBQ':
            return 'Outdoor'
        else:
            return 'Other'
    
    def _process_flg_excel(self, filepath):
        """Process FLG Excel file (legacy support)"""
        try:
            # Try different sheet names
            sheet_names = ['ALL', 'All', 'FLG', 'Data', 'Sheet1']
            df = None
            
            for sheet_name in sheet_names:
                try:
                    df = pd.read_excel(filepath, sheet_name=sheet_name)
                    logger.info(f"Successfully read sheet '{sheet_name}'")
                    break
                except:
                    continue
            
            if df is None:
                # Read first sheet
                df = pd.read_excel(filepath, sheet_name=0)
            
            # Process similar to CSV
            column_mapping = self._map_csv_columns(df.columns)
            
            # Continue processing as with CSV...
            # (Similar logic to CSV processing)
            
            raise NotImplementedError("Excel FLG processing not fully implemented yet")
            
        except Exception as e:
            logger.error(f"Error processing FLG Excel file: {e}")
            raise
    




    def process_ad_spend_file(self, filepath):
        """Fixed version that properly reports results and handles mixed date formats"""
        try:
            filename_lower = os.path.basename(filepath).lower()
            is_historic = 'historic' in filename_lower
            
            # Read Excel file
            xls = pd.ExcelFile(filepath)
            logger.info(f"Found sheets: {xls.sheet_names}")
            
            all_records = []
            total_spend = 0
            new_campaigns = set()
            ad_spend_records = []
            unique_dates = set()
            failed_rows = []
            
            for sheet_name in xls.sheet_names:
                try:
                    # Read the sheet
                    df = pd.read_excel(filepath, sheet_name=sheet_name)
                    
                    if len(df) == 0:
                        continue
                    
                    logger.info(f"Processing sheet '{sheet_name}' with {len(df)} rows")
                    logger.info(f"Columns: {list(df.columns)}")
                    
                    # Find columns
                    date_col = None
                    campaign_col = None
                    spend_col = None
                    
                    # Find date column
                    for col in df.columns:
                        col_lower = str(col).lower()
                        if 'reporting ends' in col_lower or 'reporting_ends' in col_lower:
                            date_col = col
                            break
                        elif 'date' in col_lower or 'week' in col_lower:
                            date_col = col
                    
                    # Find campaign column
                    for col in df.columns:
                        col_lower = str(col).lower()
                        if 'campaign' in col_lower:
                            campaign_col = col
                            break
                    
                    # Find spend column - look for spend/cost/amount
                    for col in df.columns:
                        col_lower = str(col).lower()
                        if any(term in col_lower for term in ['spend', 'cost', 'amount', 'spent', 'gmp']):
                            spend_col = col
                            break
                    
                    # If no spend column found, use last numeric column
                    if not spend_col:
                        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                        if numeric_cols:
                            spend_col = numeric_cols[-1]
                    
                    logger.info(f"Column mapping - Date: {date_col}, Campaign: {campaign_col}, Spend: {spend_col}")
                    
                    if not campaign_col or not spend_col:
                        logger.warning(f"Missing required columns in sheet '{sheet_name}'")
                        continue
                    
                    # Process rows - DON'T FAIL ON INDIVIDUAL ROW ERRORS
                    sheet_records = 0
                    sheet_spend = 0
                    
                    for idx, row in df.iterrows():
                        try:
                            # Get campaign name
                            campaign_name = str(row[campaign_col]).strip() if pd.notna(row[campaign_col]) else None
                            
                            # Skip invalid campaign names
                            if not campaign_name or campaign_name == 'nan' or campaign_name.lower() in ['total', 'grand total']:
                                continue
                            
                            # Parse date - USE OUR SIMPLE PARSER
                            date_value = None
                            if date_col and pd.notna(row[date_col]):
                                date_value = self._parse_date_enhanced(row[date_col], sheet_name, filename_lower)
                            
                            # Skip if no date (don't default to June 30!)
                            if not date_value:
                                failed_rows.append((idx, row[date_col] if date_col else 'No date column'))
                                continue
                            
                            # Parse spend amount
                            spend_amount = 0
                            if pd.notna(row[spend_col]):
                                if isinstance(row[spend_col], (int, float)):
                                    spend_amount = float(row[spend_col])
                                else:
                                    # Clean string amounts
                                    spend_str = str(row[spend_col]).replace('£', '').replace('$', '').replace(',', '').replace('GBP', '').strip()
                                    try:
                                        spend_amount = float(spend_str)
                                    except:
                                        logger.debug(f"Could not parse spend in row {idx}: {row[spend_col]}")
                                        continue
                            
                            # Skip zero or negative amounts
                            if spend_amount <= 0:
                                continue
                            
                            # Track unique dates
                            unique_dates.add(date_value)
                            
                            # Create or get campaign
                            campaign = Campaign.query.filter_by(meta_name=campaign_name).first()
                            if not campaign:
                                campaign = Campaign(
                                    name=campaign_name,
                                    meta_name=campaign_name
                                )
                                db.session.add(campaign)
                                db.session.flush()
                                new_campaigns.add(campaign_name)
                            
                            # Create ad spend record
                            ad_spend = AdSpend(
                                reporting_end_date=date_value,
                                meta_campaign_name=campaign_name,
                                spend_amount=spend_amount,
                                is_new=not is_historic,
                                campaign_id=campaign.id
                            )
                            
                            ad_spend_records.append(ad_spend)
                            sheet_records += 1
                            sheet_spend += spend_amount
                            
                            # Log progress every 100 rows
                            if idx % 100 == 0:
                                logger.info(f"Processed {idx} rows...")
                            
                        except Exception as e:
                            logger.warning(f"Error processing row {idx}: {e}")
                            failed_rows.append((idx, str(e)))
                            continue  # DON'T FAIL - CONTINUE TO NEXT ROW
                    
                    logger.info(f"Sheet '{sheet_name}': {sheet_records} records, £{sheet_spend:,.2f} total")
                    all_records.append(sheet_records)
                    total_spend += sheet_spend
                    
                except Exception as e:
                    logger.error(f"Error processing sheet '{sheet_name}': {e}")
                    continue
            
            # Log results
            logger.info(f"\n{'='*60}")
            logger.info(f"PROCESSING COMPLETE:")
            logger.info(f"Total records to save: {len(ad_spend_records)}")
            logger.info(f"Total spend: £{total_spend:,.2f}")
            logger.info(f"Failed rows: {len(failed_rows)}")
            
            if unique_dates:
                sorted_dates = sorted(unique_dates)
                logger.info(f"Unique dates: {len(sorted_dates)}")
                logger.info(f"Date range: {sorted_dates[0]} to {sorted_dates[-1]}")
            
            if failed_rows:
                logger.warning(f"Failed to parse dates for {len(failed_rows)} rows:")
                for idx, reason in failed_rows[:5]:
                    logger.warning(f"  Row {idx}: {reason}")
            
            # Bulk insert all records
            if ad_spend_records:
                logger.info(f"Saving {len(ad_spend_records)} records to database...")
                try:
                    for record in ad_spend_records:
                        db.session.add(record)
                    db.session.commit()
                    logger.info("Successfully saved all records")
                except Exception as e:
                    logger.error(f"Error saving to database: {e}")
                    db.session.rollback()
                    raise
            
            # RETURN CORRECT SUMMARY
            return {
                'records_processed': len(ad_spend_records),  # This was the issue - sum(all_records) could be 0
                'new_campaigns': list(new_campaigns),
                'total_spend': total_spend,
                'file_type': f'Excel - {"Historic" if is_historic else "Recent"}',
                'sheets_processed': len([r for r in all_records if r > 0]),
                'unique_dates': len(unique_dates),
                'failed_rows': len(failed_rows),
                'date_range': f"{sorted_dates[0]} to {sorted_dates[-1]}" if unique_dates else None
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing ad spend file: {e}", exc_info=True)
            raise

    def _parse_date_by_section(self, value, row_idx, section, total_rows):
        """Parse date with awareness of which section of the file we're in"""
        
        # Log what we're trying to parse
        logger.debug(f"Parsing row {row_idx} ({section}): '{value}' (type: {type(value).__name__})")
        
        # If it's None or NaN
        if pd.isna(value) or value is None:
            return None
        
        # If it's already a datetime/date object
        if hasattr(value, 'date'):
            return value.date()
        if isinstance(value, pd.Timestamp):
            return value.date()
        
        # HANDLE DIFFERENT FORMATS BASED ON SECTION
        
        # For LAST section (last 10 rows) - might have different format
        if section == "LAST":
            # Try month/year formats first for last rows
            value_str = str(value).strip()
            
            # Common patterns for summary rows
            summary_formats = [
                '%B %Y',      # July 2025
                '%b %Y',      # Jul 2025
                '%B-%Y',      # July-2025
                '%b-%Y',      # Jul-2025
                '%m/%Y',      # 07/2025
                '%m-%Y',      # 07-2025
                '%Y-%m',      # 2025-07
                'FY %Y',      # FY 2025
                'Q%q %Y',     # Q3 2025
            ]
            
            for fmt in summary_formats:
                try:
                    # Special handling for fiscal year
                    if 'FY' in value_str:
                        year = int(value_str.replace('FY', '').strip())
                        # Assume fiscal year ends in June
                        return datetime(year, 6, 30).date()
                    
                    # Special handling for quarters
                    if value_str.startswith('Q'):
                        parts = value_str.split()
                        if len(parts) == 2:
                            quarter = int(parts[0][1])
                            year = int(parts[1])
                            # Last day of quarter
                            quarter_ends = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
                            month, day = quarter_ends.get(quarter, (6, 30))
                            return datetime(year, month, day).date()
                    
                    # Try normal parsing
                    dt = datetime.strptime(value_str, fmt)
                    # For month/year only, use last day of month
                    if '%d' not in fmt:
                        # Get last day of month
                        if dt.month == 12:
                            next_month = datetime(dt.year + 1, 1, 1)
                        else:
                            next_month = datetime(dt.year, dt.month + 1, 1)
                        last_day = next_month - timedelta(days=1)
                        return last_day.date()
                    return dt.date()
                except:
                    continue
        
        # For FIRST and MIDDLE sections - try standard date formats
        # Try Excel serial number first if it's numeric
        if isinstance(value, (int, float)):
            try:
                excel_base = datetime(1899, 12, 30)
                dt = excel_base + timedelta(days=float(value))
                parsed_date = dt.date()
                
                # Sanity check
                if datetime(2020, 1, 1).date() <= parsed_date <= datetime(2030, 12, 31).date():
                    return parsed_date
            except:
                pass
        
        # Standard date parsing
        value_str = str(value).strip()
        
        # Remove common suffixes
        for suffix in ['W/E', 'w/e', 'WE', 'Week Ending', 'week ending']:
            value_str = value_str.replace(suffix, '').strip()
        
        # Standard formats
        standard_formats = [
            '%Y-%m-%d',           # 2025-07-31
            '%d/%m/%Y',           # 31/07/2025
            '%m/%d/%Y',           # 07/31/2025
            '%d-%m-%Y',           # 31-07-2025
            '%d.%m.%Y',           # 31.07.2025
            '%Y/%m/%d',           # 2025/07/31
            '%d %B %Y',           # 31 July 2025
            '%d %b %Y',           # 31 Jul 2025
            '%B %d, %Y',          # July 31, 2025
            '%d-%b-%Y',           # 31-Jul-2025
            '%Y%m%d',             # 20250731
            '%d/%m/%y',           # 31/07/25
            '%m/%d/%y',           # 07/31/25
        ]
        
        for fmt in standard_formats:
            try:
                dt = datetime.strptime(value_str, fmt)
                return dt.date()
            except:
                continue
        
        # Last resort - pandas
        try:
            dt = pd.to_datetime(value_str, dayfirst=True, errors='coerce')
            if pd.notna(dt):
                return dt.date()
        except:
            pass
        
        logger.warning(f"Failed to parse date in row {row_idx} ({section}): '{value}'")
        return None

    def _guess_date_from_context(self, sheet_name, row_idx, total_rows):
        """Guess date based on context when parsing fails"""
        
        # Check sheet name for clues
        sheet_lower = sheet_name.lower()
        
        # Month mapping
        months = {
            'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
            'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
            'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'october': 10, 'oct': 10,
            'november': 11, 'nov': 11, 'december': 12, 'dec': 12
        }
        
        # Look for month in sheet name
        for month_name, month_num in months.items():
            if month_name in sheet_lower:
                # Assume 2025 if no year found
                year = 2025
                
                # Try to find year
                import re
                year_match = re.search(r'20\d{2}', sheet_name)
                if year_match:
                    year = int(year_match.group())
                
                # For last rows, use end of month
                if row_idx >= total_rows - 10:
                    if month_num == 12:
                        return datetime(year, 12, 31).date()
                    else:
                        next_month = datetime(year, month_num + 1, 1)
                        return (next_month - timedelta(days=1)).date()
                else:
                    # For other rows, distribute across the month
                    day = min(28, max(1, int((row_idx / total_rows) * 28) + 1))
                    return datetime(year, month_num, day).date()
        
        # Default fallback - this is probably what's causing June 30!
        logger.warning(f"Using fallback date for row {row_idx} in sheet '{sheet_name}'")
        return datetime(2025, 6, 30).date()  # This is likely the culprit!


    def _parse_date_enhanced_debug(self, value, sheet_name=None, filename=None):
        """Enhanced date parsing with detailed debugging"""
        if pd.isna(value) or value is None:
            logger.debug("Date value is None or NaN")
            return None
        
        # Log the raw value and its type
        logger.debug(f"Parsing date - Raw value: '{value}' | Type: {type(value).__name__} | Sheet: {sheet_name}")
        
        # If it's already a date object, return it
        if hasattr(value, 'date'):
            logger.debug(f"Value has date method, returning: {value.date()}")
            return value.date()
        if hasattr(value, 'year') and hasattr(value, 'month') and hasattr(value, 'day'):
            logger.debug(f"Value is already a date object: {value}")
            return value
        
        # Check if it's a pandas Timestamp
        if isinstance(value, pd.Timestamp):
            logger.debug(f"Value is pandas Timestamp: {value.date()}")
            return value.date()
        
        # Convert to string for consistent handling
        value_str = str(value).strip()
        logger.debug(f"String representation: '{value_str}'")
        
        # Check if it looks like an Excel serial date (pure number)
        try:
            # First check if the string is purely numeric
            if value_str.replace('.', '').replace('-', '').isdigit() and '/' not in value_str and len(value_str) <= 6:
                serial_num = float(value_str)
                if 1 < serial_num < 100000:  # Reasonable range for Excel dates
                    excel_base_date = datetime(1899, 12, 30)
                    dt = excel_base_date + timedelta(days=serial_num)
                    logger.debug(f"Parsed as Excel serial date {serial_num} -> {dt.date()}")
                    return dt.date()
        except:
            pass
        
        # If the original value was numeric, try Excel serial date
        if isinstance(value, (int, float)):
            try:
                excel_base_date = datetime(1899, 12, 30)
                dt = excel_base_date + timedelta(days=float(value))
                logger.debug(f"Parsed numeric value as Excel serial date: {value} -> {dt.date()}")
                return dt.date()
            except:
                pass
        
        # Extended list of date formats to try
        date_formats = [
            # ISO formats
            '%Y-%m-%d',           # 2025-07-31
            '%Y/%m/%d',           # 2025/07/31
            '%Y.%m.%d',           # 2025.07.31
            '%Y%m%d',             # 20250731
            
            # European formats
            '%d/%m/%Y',           # 31/07/2025
            '%d-%m-%Y',           # 31-07-2025
            '%d.%m.%Y',           # 31.07.2025
            '%d/%m/%y',           # 31/07/25
            '%d-%m-%y',           # 31-07-25
            '%d %m %Y',           # 31 07 2025
            
            # US formats
            '%m/%d/%Y',           # 07/31/2025
            '%m-%d-%Y',           # 07-31-2025
            '%m/%d/%y',           # 07/31/25
            '%m-%d-%y',           # 07-31-25
            
            # With time components
            '%Y-%m-%d %H:%M:%S',  # 2025-07-31 00:00:00
            '%Y/%m/%d %H:%M:%S',  # 2025/07/31 00:00:00
            '%d/%m/%Y %H:%M:%S',  # 31/07/2025 00:00:00
            '%d/%m/%Y %H:%M',     # 31/07/2025 00:00
            '%m/%d/%Y %H:%M:%S',  # 07/31/2025 00:00:00
            '%Y-%m-%dT%H:%M:%S',  # 2025-07-31T00:00:00
            
            # Month names
            '%d %B %Y',           # 31 July 2025
            '%d %b %Y',           # 31 Jul 2025
            '%d-%B-%Y',           # 31-July-2025  
            '%d-%b-%Y',           # 31-Jul-2025
            '%B %d, %Y',          # July 31, 2025
            '%b %d, %Y',          # Jul 31, 2025
            '%d %B %y',           # 31 July 25
            '%d %b %y',           # 31 Jul 25
            
            # Special formats
            '%d/%m',              # 31/07 (assume current year)
            '%m/%d',              # 07/31 (assume current year)
        ]
        
        # Remove common suffixes/prefixes
        cleaned_value = value_str
        for suffix in ['W/E', 'w/e', 'WE', 'we', 'Week Ending', 'week ending', 'Week ending']:
            cleaned_value = cleaned_value.replace(suffix, '').strip()
        
        # Try each format
        for fmt in date_formats:
            try:
                dt = datetime.strptime(cleaned_value, fmt)
                
                # Handle formats without year
                if '%Y' not in fmt and '%y' not in fmt:
                    current_year = datetime.now().year
                    dt = dt.replace(year=current_year)
                
                logger.debug(f"Successfully parsed '{value_str}' as {dt.date()} using format '{fmt}'")
                return dt.date()
            except:
                continue
        
        # Try pandas to_datetime with various settings
        try:
            # Try with dayfirst=True (European format)
            dt = pd.to_datetime(value_str, dayfirst=True, errors='coerce')
            if pd.notna(dt):
                logger.debug(f"Pandas parsed '{value_str}' as {dt.date()} (dayfirst=True)")
                return dt.date()
        except:
            pass
        
        try:
            # Try with dayfirst=False (US format)
            dt = pd.to_datetime(value_str, dayfirst=False, errors='coerce')
            if pd.notna(dt):
                logger.debug(f"Pandas parsed '{value_str}' as {dt.date()} (dayfirst=False)")
                return dt.date()
        except:
            pass
        
        # Try to extract date from context
        if sheet_name or filename:
            context_date = self._extract_date_from_context(sheet_name, filename)
            if context_date:
                logger.warning(f"Could not parse '{value_str}', using context date: {context_date}")
                return context_date
        
        logger.warning(f"FAILED to parse date: '{value_str}' | Original type: {type(value).__name__}")
        
        # Last resort: Check if it's June 30, 2025 hardcoded somehow
        if '2025-06-30' in str(value) or '30/06/2025' in str(value) or '06/30/2025' in str(value):
            logger.error(f"WARNING: Date appears to be hardcoded as June 30, 2025: '{value}'")
        
        return None
    
    def _extract_date_from_context(self, sheet_name, filename):
        """Try to extract date from sheet name or filename for historic data"""
        import re
        
        # Common month names
        months = {
            'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
            'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
            'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'october': 10, 'oct': 10,
            'november': 11, 'nov': 11, 'december': 12, 'dec': 12
        }
        
        # Try to find month in text
        text = f"{sheet_name} {filename}".lower()
        
        for month_name, month_num in months.items():
            if month_name in text:
                # Default to 2025 if no year found
                year = 2025
                
                # Try to find year
                year_match = re.search(r'20\d{2}', text)
                if year_match:
                    year = int(year_match.group())
                
                # Return last day of the month
                if month_num == 12:
                    return datetime(year, month_num, 31).date()
                else:
                    next_month = datetime(year, month_num + 1, 1)
                    last_day = next_month - timedelta(days=1)
                    return last_day.date()
        
        # Try to find date patterns
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # DD/MM/YYYY or MM/DD/YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',    # YYYY/MM/DD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    # Try different date formats
                    date_str = match.group()
                    for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d', '%d-%m-%Y', '%m-%d-%Y', '%Y-%m-%d']:
                        try:
                            return datetime.strptime(date_str, fmt).date()
                        except:
                            continue
                except:
                    continue
        
        return None
    
    def _parse_date_enhanced(self, value, sheet_name=None, filename=None):
        """Simple date parser that handles both text and Excel dates"""
        if pd.isna(value) or value is None:
            return None
        
        # If it's already a date/datetime object
        if hasattr(value, 'date'):
            return value.date()
        if isinstance(value, pd.Timestamp):
            return value.date()
        
        # HANDLE EXCEL SERIAL DATES (numbers like 45473)
        if isinstance(value, (int, float)):
            try:
                # Excel dates are days since 1899-12-30
                excel_base_date = datetime(1899, 12, 30)
                dt = excel_base_date + timedelta(days=float(value))
                # Sanity check - make sure date is reasonable
                if datetime(2020, 1, 1) <= dt <= datetime(2030, 12, 31):
                    logger.debug(f"Parsed Excel serial {value} as {dt.date()}")
                    return dt.date()
            except Exception as e:
                logger.debug(f"Failed to parse as Excel serial: {value} - {e}")
        
        # HANDLE TEXT DATES
        # Convert to string and clean up
        value_str = str(value).strip()
        
        # Remove common suffixes
        for suffix in ['W/E', 'w/e', 'WE', 'Week Ending', 'week ending']:
            value_str = value_str.replace(suffix, '').strip()
        
        # Try common date formats
        date_formats = [
            '%Y-%m-%d',     # 2025-07-31 (most common in your data)
            '%d/%m/%Y',     # 31/07/2025
            '%d-%m-%Y',     # 31-07-2025
            '%m/%d/%Y',     # 07/31/2025
            '%Y/%m/%d',     # 2025/07/31
            '%d/%m/%y',     # 31/07/25
            '%d %B %Y',     # 31 July 2025
            '%d %b %Y',     # 31 Jul 2025
            '%B %Y',        # July 2025
            '%b %Y',        # Jul 2025
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(value_str, fmt)
                # For month-only formats, use last day of month
                if '%d' not in fmt:
                    if dt.month == 12:
                        next_month = datetime(dt.year + 1, 1, 1)
                    else:
                        next_month = datetime(dt.year, dt.month + 1, 1)
                    dt = next_month - timedelta(days=1)
                
                logger.debug(f"Parsed '{value_str}' as {dt.date()} using format {fmt}")
                return dt.date()
            except:
                continue
        
        # If all parsing fails, log it but don't crash
        logger.warning(f"Could not parse date: '{value}' (type: {type(value).__name__})")
        return None


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
                table_found = False
                for table_idx, table in enumerate(doc.tables):
                    logger.info(f"Processing table {table_idx + 1} with {len(table.rows)} rows")
                    
                    for row_idx, row in enumerate(table.rows):
                        # Check if this looks like a header row
                        cells = row.cells
                        if len(cells) >= 2:
                            cell0_text = cells[0].text.strip().lower()
                            cell1_text = cells[1].text.strip().lower()
                            
                            # Skip if it looks like a header
                            if any(term in cell0_text for term in ['flg', 'campaign', 'name']) and \
                               any(term in cell1_text for term in ['meta', 'campaign', 'name']):
                                logger.info(f"Skipping header row: {cells[0].text} | {cells[1].text}")
                                continue
                            
                            flg_name = cells[0].text.strip()
                            meta_name = cells[1].text.strip()
                            
                            if flg_name and meta_name and not flg_name.startswith('**'):
                                table_found = True
                                
                                # Clean up the names (remove ? prefix if present)
                                if flg_name.startswith('?'):
                                    flg_name = flg_name[1:].strip()
                                
                                # Check if mapping exists
                                existing = FLGMetaMapping.query.filter_by(flg_name=flg_name).first()
                                
                                if existing:
                                    existing.meta_name = meta_name
                                    mappings_updated += 1
                                    logger.info(f"Updated mapping: {flg_name} -> {meta_name}")
                                else:
                                    mapping = FLGMetaMapping(
                                        flg_name=flg_name,
                                        meta_name=meta_name
                                    )
                                    db.session.add(mapping)
                                    mappings_created += 1
                                    logger.info(f"Created mapping: {flg_name} -> {meta_name}")
                
                if not table_found:
                    logger.warning("No valid mapping data found in Word document tables")
            
            elif file_ext in ['.xlsx', '.xls']:
                # Process Excel file
                df = pd.read_excel(filepath)
                
                # Assume first two columns are FLG name and Meta name
                for _, row in df.iterrows():
                    flg_name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
                    meta_name = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else None
                    
                    if flg_name and meta_name:
                        # Clean up names
                        if flg_name.startswith('?'):
                            flg_name = flg_name[1:].strip()
                        
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
            
            self.processing_state['mappings_loaded'] = True
            
            logger.info(f"Mapping file processed: {mappings_created} created, {mappings_updated} updated")
            
            return {
                'mappings_created': mappings_created,
                'mappings_updated': mappings_updated,
                'file_type': file_ext
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
                # Handle GBP notation
                value = value.replace('GBP', '').replace('gbp', '').strip()
            return float(value)
        except:
            return None
    
    def _parse_boolean(self, value):
        """Parse boolean value from various formats"""
        if pd.isna(value):
            return False
        
        if isinstance(value, bool):
            return value
        
        str_val = str(value).upper().strip()
        return str_val in ['NEW', 'TRUE', 'YES', '1', 'Y']
    
    def _parse_datetime_safe(self, value):
        """Safely parse datetime using multiple formats"""
        if pd.isna(value) or value is None:
            return None
            
        # If it's a number (Excel serial date)
        if isinstance(value, (int, float)):
            excel_base_date = datetime(1899, 12, 30)
            return excel_base_date + timedelta(days=value)
        
        # If it's already a datetime
        if isinstance(value, datetime):
            return value
            
        # If it's a string, try multiple formats
        if isinstance(value, str):
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%d/%m/%Y %H:%M:%S',
                '%d/%m/%Y',
                '%m/%d/%Y %H:%M:%S',
                '%m/%d/%Y',
                '%d-%m-%Y %H:%M:%S',
                '%d-%m-%Y',
                '%Y/%m/%d %H:%M:%S',
                '%Y/%m/%d',
                '%d/%m/%Y %H:%M',
                '%d-%m-%Y %H:%M'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(value.strip(), fmt)
                except:
                    continue
        
        return None
    
    def _parse_date_safe(self, value):
        """Safely parse date for ad spend - delegates to enhanced parser"""
        return self._parse_date_enhanced(value)