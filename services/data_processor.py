"""
Data processing service for handling file uploads - Corrected for actual data structure
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
    
    def __init__(self):
        # Track Lead IDs that passed/failed affordability checks
        self.passed_lead_ids = set()
        self.failed_lead_ids = set()
    
    def process_applications_file(self, filepath):
        """Process affordability check files - Extract only Lead IDs"""
        try:
            file_ext = os.path.splitext(filepath)[1].lower()
            filename_lower = os.path.basename(filepath).lower()
            
            if file_ext == '.csv':
                # Read CSV file
                df = pd.read_csv(filepath)
                
                # Check if Lead ID column exists
                if 'Lead ID' not in df.columns:
                    raise ValueError("Lead ID column not found in CSV file")
                
                # Extract Lead IDs
                lead_ids = df['Lead ID'].dropna().unique()
                count = len(lead_ids)
                
                # Determine if passed or failed
                if 'passed' in filename_lower:
                    self.passed_lead_ids.update(str(int(lid)) if isinstance(lid, (int, float)) else str(lid) for lid in lead_ids)
                    logger.info(f"Loaded {count} passed Lead IDs")
                    return {
                        'records_processed': count,
                        'passed_count': count,
                        'failed_count': 0,
                        'file_type': 'CSV - Passed Lead IDs'
                    }
                elif 'failed' in filename_lower:
                    self.failed_lead_ids.update(str(int(lid)) if isinstance(lid, (int, float)) else str(lid) for lid in lead_ids)
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
                        'error': 'Could not determine if passed or failed from filename'
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
                    self.passed_lead_ids.update(str(int(lid)) if isinstance(lid, (int, float)) else str(lid) for lid in lead_ids)
                    passed_count = len(lead_ids)
            
            # Process failed sheet
            if 'Affordability data - failed' in xls.sheet_names:
                df_failed = pd.read_excel(xls, 'Affordability data - failed')
                if 'Lead ID' in df_failed.columns:
                    lead_ids = df_failed['Lead ID'].dropna().unique()
                    self.failed_lead_ids.update(str(int(lid)) if isinstance(lid, (int, float)) else str(lid) for lid in lead_ids)
                    failed_count = len(lead_ids)
            
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
            file_ext = os.path.splitext(filepath)[1].lower()
            
            if file_ext == '.csv':
                # Read CSV file
                df = pd.read_csv(filepath)
                
                # Expected columns
                expected_columns = [
                    'Lead ID', 'Date & time received', 'Status', 'Marketing source',
                    'Capital amount', 'Repayment frequency', 'Total interest',
                    'Regular repayments', 'Total amount to pay', 'Product details'
                ]
                
                # Check if all expected columns exist
                missing_columns = [col for col in expected_columns if col not in df.columns]
                if missing_columns:
                    logger.warning(f"Missing columns: {missing_columns}")
                
                # Process data
                new_products = set()
                unmapped_sources = set()
                count = 0
                applications_created = 0
                
                for _, row in df.iterrows():
                    try:
                        # Get Lead ID
                        lead_id_raw = row.get('Lead ID')
                        if pd.isna(lead_id_raw):
                            continue
                        
                        lead_id = str(int(lead_id_raw)) if isinstance(lead_id_raw, (int, float)) else str(lead_id_raw)
                        
                        # Create FLG record
                        existing_flg = FLGData.query.filter_by(reference=lead_id).first()
                        if existing_flg:
                            flg = existing_flg
                        else:
                            flg = FLGData()
                        
                        # Set FLG fields
                        flg.reference = lead_id
                        flg.received_datetime = self._parse_datetime_safe(row.get('Date & time received'))
                        flg.status = str(row.get('Status')) if pd.notna(row.get('Status')) else None
                        flg.marketing_source = str(row.get('Marketing source')) if pd.notna(row.get('Marketing source')) else None
                        flg.data5_value = self._parse_float(row.get('Capital amount'))
                        flg.data6_payment_type = str(row.get('Repayment frequency')) if pd.notna(row.get('Repayment frequency')) else None
                        flg.data7_value = self._parse_float(row.get('Total interest'))
                        flg.data8_value = self._parse_float(row.get('Regular repayments'))
                        flg.data10_value = self._parse_float(row.get('Total amount to pay'))
                        flg.data29_product_description = str(row.get('Product details')) if pd.notna(row.get('Product details')) else None
                        
                        # Calculate sale value
                        flg.sale_value = flg.calculate_sale_value()
                        
                        # Extract product from description
                        if flg.data29_product_description:
                            product_name = Product.extract_product_from_description(flg.data29_product_description)
                            flg.product_name = product_name
                            
                            # Check if product exists
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
                        
                        if not existing_flg:
                            db.session.add(flg)
                        
                        # Now create/update Application record based on affordability result
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
                            app.lead_partner = flg.marketing_source  # Store marketing source
                            
                            if not existing_app:
                                db.session.add(app)
                        
                        count += 1
                        
                    except Exception as row_error:
                        logger.warning(f"Error processing FLG row: {row_error}")
                        continue
                
                # Create new products
                for product_name in new_products:
                    product = Product(name=product_name)
                    db.session.add(product)
                
                db.session.commit()
                
                logger.info(f"Processed {count} FLG records, created {applications_created} applications")
                
                return {
                    'records_processed': count,
                    'applications_created': applications_created,
                    'new_products': list(new_products),
                    'unmapped_sources': list(unmapped_sources),
                    'file_type': 'CSV - All Leads'
                }
                
            else:
                # Original Excel processing
                return self._process_flg_excel(filepath)
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing FLG data file: {e}")
            raise
    
    def _process_flg_excel(self, filepath):
        """Process FLG Excel file (legacy support)"""
        try:
            df = pd.read_excel(filepath, sheet_name='ALL')
            
            # Find header row and process...
            # (keeping existing Excel logic)
            
            raise NotImplementedError("Excel FLG processing not fully implemented yet")
            
        except Exception as e:
            logger.error(f"Error processing FLG Excel file: {e}")
            raise
    
    def process_ad_spend_file(self, filepath):
        """Process ad spend Excel file - handles various formats"""
        try:
            filename_lower = os.path.basename(filepath).lower()
            
            # Determine if this is historic data based on filename
            is_historic = 'historic' in filename_lower
            
            # Try to read Excel file
            xls = pd.ExcelFile(filepath)
            logger.info(f"Found sheets in ad spend file: {xls.sheet_names}")
            
            # Process all sheets and combine results
            all_records = []
            total_spend = 0
            new_campaigns = set()
            
            for sheet_name in xls.sheet_names:
                try:
                    df = pd.read_excel(filepath, sheet_name=sheet_name)
                    
                    if len(df) == 0:
                        continue
                    
                    logger.info(f"Processing sheet '{sheet_name}' with {len(df)} rows")
                    logger.info(f"Columns in sheet: {list(df.columns)}")
                    
                    # Try to identify columns
                    date_col = None
                    campaign_col = None
                    adset_col = None
                    spend_col = None
                    
                    # Look for columns by name patterns
                    for col in df.columns:
                        col_lower = str(col).lower().strip()
                        
                        # Date columns
                        if not date_col and any(term in col_lower for term in ['date', 'week', 'month', 'period', 'reporting']):
                            date_col = col
                            logger.info(f"Found date column: {col}")
                        
                        # Campaign columns
                        elif not campaign_col and any(term in col_lower for term in ['campaign', 'meta campaign']):
                            campaign_col = col
                            logger.info(f"Found campaign column: {col}")
                        
                        # Ad set/level columns
                        elif not adset_col and any(term in col_lower for term in ['ad set', 'adset', 'ad level', 'level']):
                            adset_col = col
                            logger.info(f"Found ad set column: {col}")
                        
                        # Spend columns
                        elif not spend_col and any(term in col_lower for term in ['spend', 'cost', 'amount', 'gmp']):
                            spend_col = col
                            logger.info(f"Found spend column: {col}")
                    
                    # If we couldn't find columns by name, try by position and content
                    if not all([date_col, campaign_col, spend_col]):
                        logger.warning("Could not identify all columns by name, trying by content...")
                        
                        # Show sample data
                        logger.info("Sample data from first 3 rows:")
                        for idx, row in df.head(3).iterrows():
                            logger.info(f"Row {idx}: {dict(row)}")
                        
                        # Skip this sheet if we can't identify columns
                        continue
                    
                    # Process rows
                    sheet_records = 0
                    for _, row in df.iterrows():
                        try:
                            # Skip empty rows
                            if pd.isna(row.get(campaign_col)) or pd.isna(row.get(spend_col)):
                                continue
                            
                            # Parse date
                            date_value = self._parse_date_safe(row.get(date_col))
                            if not date_value:
                                # For historic data, try to extract month/year from sheet name or filename
                                if is_historic:
                                    date_value = self._extract_date_from_context(sheet_name, filename_lower)
                                
                                if not date_value:
                                    logger.warning(f"Could not parse date: {row.get(date_col)}")
                                    continue
                            
                            # Get values
                            campaign_name = str(row.get(campaign_col)).strip()
                            ad_level = str(row.get(adset_col)).strip() if adset_col and pd.notna(row.get(adset_col)) else None
                            spend_amount = self._parse_float(row.get(spend_col))
                            
                            if not spend_amount or spend_amount <= 0:
                                continue
                            
                            # Create campaign if needed
                            campaign = Campaign.query.filter_by(meta_name=campaign_name).first()
                            if not campaign:
                                campaign = Campaign(
                                    name=campaign_name,
                                    meta_name=campaign_name
                                )
                                db.session.add(campaign)
                                new_campaigns.add(campaign_name)
                            
                            # Create ad spend record
                            ad_spend = AdSpend(
                                reporting_end_date=date_value,
                                meta_campaign_name=campaign_name,
                                ad_level=ad_level,
                                spend_amount=spend_amount,
                                is_new=False,  # Historic data
                                campaign=campaign
                            )
                            
                            db.session.add(ad_spend)
                            total_spend += spend_amount
                            sheet_records += 1
                            
                        except Exception as row_error:
                            logger.warning(f"Error processing ad spend row: {row_error}")
                            continue
                    
                    logger.info(f"Processed {sheet_records} records from sheet '{sheet_name}'")
                    all_records.append(sheet_records)
                    
                except Exception as sheet_error:
                    logger.error(f"Error processing sheet '{sheet_name}': {sheet_error}")
                    continue
            
            # Commit all records
            db.session.commit()
            
            total_records = sum(all_records)
            logger.info(f"Total: Processed {total_records} ad spend records, total spend: £{total_spend:,.2f}")
            
            return {
                'records_processed': total_records,
                'new_campaigns': list(new_campaigns),
                'total_spend': total_spend,
                'file_type': 'Excel - Historic' if is_historic else 'Excel',
                'sheets_processed': len(all_records),
                'is_historic': is_historic
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing ad spend file: {e}")
            raise
    
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
    
    def _looks_like_date(self, series):
        """Check if a series looks like it contains dates"""
        if len(series) == 0:
            return False
        
        # Check if any values can be parsed as dates
        date_count = 0
        for val in series.head(5):
            try:
                self._parse_date_safe(val)
                date_count += 1
            except:
                pass
        
        return date_count >= 3  # At least 3 out of 5 should be parseable as dates
    
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
            
        # If it's a string, try multiple formats
        if isinstance(value, str):
            # Clean the string
            value = value.strip()
            
            formats = [
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%m/%d/%Y',
                '%d-%m-%Y',
                '%Y/%m/%d',
                '%d.%m.%Y',
                '%Y.%m.%d',
                '%d %B %Y',  # 01 January 2025
                '%B %d, %Y',  # January 01, 2025
                '%d %b %Y',   # 01 Jan 2025
                '%b %d, %Y'   # Jan 01, 2025
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.date()
                except:
                    continue
        
        return None