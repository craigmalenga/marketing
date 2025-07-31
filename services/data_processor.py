"""
Data processing service for handling file uploads - Updated for CSV support
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
        """Process applications (affordability check) data - supports Excel and CSV"""
        try:
            file_ext = os.path.splitext(filepath)[1].lower()
            
            if file_ext == '.csv':
                # Process single CSV file
                df = pd.read_csv(filepath)
                
                # Determine if it's passed or failed based on filename or content
                affordability_result = 'unknown'
                filename_lower = os.path.basename(filepath).lower()
                
                if 'passed' in filename_lower:
                    affordability_result = 'passed'
                elif 'failed' in filename_lower:
                    affordability_result = 'failed'
                else:
                    # Try to determine from data
                    if 'Status' in df.columns:
                        status_values = df['Status'].dropna().unique()
                        if any('passed' in str(s).lower() for s in status_values):
                            affordability_result = 'passed'
                        elif any('failed' in str(s).lower() for s in status_values):
                            affordability_result = 'failed'
                
                count = self._process_applications_csv(df, affordability_result)
                
                db.session.commit()
                
                return {
                    'records_processed': count,
                    'passed_count': count if affordability_result == 'passed' else 0,
                    'failed_count': count if affordability_result == 'failed' else 0,
                    'file_type': 'CSV',
                    'affordability_result': affordability_result
                }
                
            else:
                # Original Excel processing
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
                    'failed_count': failed_count,
                    'file_type': 'Excel'
                }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing applications file: {e}")
            raise
    
    def _process_applications_csv(self, df, affordability_result):
        """Process applications data from CSV format"""
        try:
            # Column mapping for CSV files
            column_mapping = {
                'Activity date & time': 'datetime',
                'Lead ID': 'lead_id',
                'Date & time received': 'lead_datetime',
                'Status': 'status',
                'Marketing source': 'marketing_source',
                'Capital amount': 'lead_value',
                'Repayment frequency': 'payment_type',
                'Total interest': 'interest',
                'Regular repayments': 'repayment',
                'Total amount to pay': 'total_amount',
                'Product details': 'product_details'
            }
            
            # Apply column mapping
            df_mapped = df.rename(columns=column_mapping)
            
            # Process each row
            count = 0
            for _, row in df_mapped.iterrows():
                try:
                    # Skip empty rows
                    lead_id_raw = row.get('lead_id')
                    if pd.isna(lead_id_raw) or lead_id_raw == '' or lead_id_raw is None:
                        continue
                    
                    # Convert Lead ID safely
                    lead_id = str(int(lead_id_raw)) if isinstance(lead_id_raw, (int, float)) and not pd.isna(lead_id_raw) else str(lead_id_raw).strip()
                    
                    if not lead_id:
                        continue
                    
                    # Check if application already exists
                    existing = Application.query.filter_by(lead_id=lead_id).first()
                    
                    if existing:
                        app = existing
                    else:
                        app = Application()
                    
                    # Set fields
                    app.lead_id = lead_id
                    app.datetime = self._parse_datetime_safe(row.get('datetime'))
                    app.status = str(row.get('status')) if pd.notna(row.get('status')) else None
                    app.lead_datetime = self._parse_datetime_safe(row.get('lead_datetime'))
                    app.lead_value = self._parse_float(row.get('lead_value'))
                    app.current_status = str(row.get('status')) if pd.notna(row.get('status')) else None
                    app.affordability_result = affordability_result
                    
                    # Store additional data in appropriate fields
                    if pd.notna(row.get('marketing_source')):
                        app.lead_partner = str(row.get('marketing_source'))
                    
                    if not existing:
                        db.session.add(app)
                    
                    count += 1
                    
                except Exception as row_error:
                    logger.warning(f"Error processing CSV row: {row_error}")
                    continue
            
            logger.info(f"Processed {count} applications from CSV with result: {affordability_result}")
            return count
            
        except Exception as e:
            logger.error(f"Error processing applications CSV: {e}")
            raise
    
    def _process_applications_sheet(self, df, affordability_result):
        """Process a single sheet of applications data from Excel"""
        try:
            # Find the header row
            header_row = None
            for idx, row in df.iterrows():
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
                    # Skip empty rows
                    lead_id_raw = row.get('Lead ID')
                    if pd.isna(lead_id_raw) or lead_id_raw == '' or lead_id_raw is None:
                        continue
                    
                    # Convert Lead ID safely
                    lead_id = None
                    if isinstance(lead_id_raw, (int, float)) and not pd.isna(lead_id_raw):
                        lead_id = str(int(lead_id_raw))
                    elif isinstance(lead_id_raw, str) and lead_id_raw.strip():
                        lead_id = lead_id_raw.strip()
                    
                    if not lead_id:
                        continue
                    
                    # Check if application already exists
                    existing = Application.query.filter_by(lead_id=lead_id).first()
                    
                    if existing:
                        app = existing
                    else:
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
        """Process FLG data - supports Excel and CSV"""
        try:
            file_ext = os.path.splitext(filepath)[1].lower()
            
            if file_ext == '.csv':
                # Process CSV file
                df = pd.read_csv(filepath)
                
                # Column mapping for CSV files
                column_mapping = {
                    'Lead ID': 'reference',
                    'Date & time received': 'received_datetime',
                    'Status': 'status',
                    'Marketing source': 'marketing_source',
                    'Capital amount': 'data5_value',
                    'Repayment frequency': 'data6_payment_type',
                    'Total interest': 'data7_value',
                    'Regular repayments': 'data8_value',
                    'Total amount to pay': 'data10_value',
                    'Product details': 'data29_product_description'
                }
                
                # Apply column mapping
                df_mapped = df.rename(columns=column_mapping)
                
                result = self._process_flg_dataframe(df_mapped)
                
                db.session.commit()
                
                result['file_type'] = 'CSV'
                return result
                
            else:
                # Original Excel processing
                df = pd.read_excel(filepath, sheet_name='ALL')
                
                # Find the header row
                header_row = None
                for idx, row in df.iterrows():
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
                
                # Map to expected column names
                excel_mapping = {
                    'Reference': 'reference',
                    'ReceivedDateTime': 'received_datetime',
                    'Status': 'status',
                    'MarketingSource': 'marketing_source',
                    'Data5': 'data5_value',
                    'Data6': 'data6_payment_type',
                    'Data7': 'data7_value',
                    'Data8': 'data8_value',
                    'Data10': 'data10_value',
                    'Data29': 'data29_product_description'
                }
                
                df_mapped = df.rename(columns=excel_mapping)
                
                result = self._process_flg_dataframe(df_mapped)
                
                db.session.commit()
                
                result['file_type'] = 'Excel'
                return result
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing FLG data file: {e}")
            raise
    
    def _process_flg_dataframe(self, df):
        """Process FLG dataframe regardless of source"""
        try:
            # Track new products and unmapped sources
            new_products = set()
            unmapped_sources = set()
            
            # Process each row
            count = 0
            for _, row in df.iterrows():
                try:
                    # Skip empty rows
                    reference = row.get('reference')
                    if pd.isna(reference) or reference == '':
                        continue
                    
                    # Convert reference to string
                    reference = str(int(reference)) if isinstance(reference, (int, float)) and not pd.isna(reference) else str(reference)
                    
                    existing = FLGData.query.filter_by(reference=reference).first()
                    
                    if existing:
                        flg = existing
                    else:
                        flg = FLGData()
                    
                    # Set fields
                    flg.reference = reference
                    flg.received_datetime = self._parse_datetime_safe(row.get('received_datetime'))
                    flg.status = str(row.get('status')) if pd.notna(row.get('status')) else None
                    flg.marketing_source = str(row.get('marketing_source')) if pd.notna(row.get('marketing_source')) else None
                    flg.data5_value = self._parse_float(row.get('data5_value'))
                    flg.data6_payment_type = str(row.get('data6_payment_type')) if pd.notna(row.get('data6_payment_type')) else None
                    flg.data7_value = self._parse_float(row.get('data7_value'))
                    flg.data8_value = self._parse_float(row.get('data8_value'))
                    flg.data10_value = self._parse_float(row.get('data10_value'))
                    flg.data29_product_description = str(row.get('data29_product_description')) if pd.notna(row.get('data29_product_description')) else None
                    
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
            
            logger.info(f"Processed {count} FLG records")
            
            return {
                'records_processed': count,
                'new_products': list(new_products),
                'unmapped_sources': list(unmapped_sources)
            }
            
        except Exception as e:
            logger.error(f"Error processing FLG dataframe: {e}")
            raise
    
    def process_ad_spend_file(self, filepath):
        """Process ad spend Excel file with detailed logging"""
        try:
            # Try to read the Excel file
            xls = pd.ExcelFile(filepath)
            
            logger.info(f"Found sheets in Excel file: {xls.sheet_names}")
            
            # Look for any sheet that might contain ad spend data
            ad_sheet = None
            for sheet in xls.sheet_names:
                sheet_lower = sheet.lower()
                if any(term in sheet_lower for term in ['meta', 'spend', 'ad', 'campaign', 'cost']):
                    ad_sheet = sheet
                    break
            
            if not ad_sheet:
                # Use the first sheet
                ad_sheet = xls.sheet_names[0] if xls.sheet_names else None
                logger.warning(f"No ad spend sheet found by name, using: {ad_sheet}")
            
            if not ad_sheet:
                raise ValueError("No sheets found in Excel file")
            
            # Read the sheet
            df = pd.read_excel(filepath, sheet_name=ad_sheet)
            
            logger.info(f"Read {len(df)} rows from sheet '{ad_sheet}'")
            logger.info(f"Column names found: {list(df.columns)}")
            
            # Find the header row by looking for key columns
            header_row = None
            for idx in range(min(10, len(df))):
                row_values = df.iloc[idx].astype(str).tolist()
                row_str = ' '.join(row_values).lower()
                
                # Look for any indication this is a header row
                if any(term in row_str for term in ['reporting', 'campaign', 'spend', 'cost', 'date']):
                    header_row = idx
                    logger.info(f"Found potential header row at index {idx}")
                    break
            
            if header_row is None:
                header_row = 0
                logger.warning("Could not find header row, using first row")
            
            # Read again with correct header row
            df = pd.read_excel(filepath, sheet_name=ad_sheet, header=header_row)
            
            # Clean column names
            df.columns = [str(col).strip() for col in df.columns]
            logger.info(f"Cleaned column names: {list(df.columns)}")
            
            # Try to identify columns by content
            date_col = None
            campaign_col = None
            spend_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                sample_values = df[col].dropna().head()
                
                # Check for date column
                if any(term in col_lower for term in ['date', 'reporting', 'period', 'week']):
                    date_col = col
                elif pd.api.types.is_datetime64_any_dtype(df[col]) or self._looks_like_date(sample_values):
                    date_col = col
                
                # Check for campaign column
                if any(term in col_lower for term in ['campaign', 'meta', 'name']):
                    campaign_col = col
                
                # Check for spend column
                if any(term in col_lower for term in ['spend', 'cost', 'amount', 'value']):
                    spend_col = col
                elif pd.api.types.is_numeric_dtype(df[col]) and df[col].mean() > 0:
                    # Might be a spend column if it's numeric and positive
                    if not spend_col:  # Only set if we haven't found one yet
                        spend_col = col
            
            logger.info(f"Identified columns - Date: {date_col}, Campaign: {campaign_col}, Spend: {spend_col}")
            
            if not all([date_col, campaign_col, spend_col]):
                # Log what we're missing
                missing = []
                if not date_col: missing.append("date")
                if not campaign_col: missing.append("campaign")
                if not spend_col: missing.append("spend")
                
                logger.error(f"Could not identify required columns: {missing}")
                logger.error(f"Available columns: {list(df.columns)}")
                
                # Show sample data
                logger.error("Sample data from first 3 rows:")
                for idx, row in df.head(3).iterrows():
                    logger.error(f"Row {idx}: {dict(row)}")
                
                raise ValueError(f"Could not identify required columns: {missing}")
            
            # Create standardized dataframe
            df_std = pd.DataFrame({
                'reporting_date': df[date_col],
                'campaign_name': df[campaign_col],
                'spend_amount': df[spend_col]
            })
            
            # Add optional columns if found
            for col in df.columns:
                col_lower = col.lower()
                if 'ad' in col_lower and 'level' in col_lower:
                    df_std['ad_level'] = df[col]
                elif 'new' in col_lower:
                    df_std['is_new'] = df[col]
            
            # Track results
            new_campaigns = set()
            total_spend = 0
            count = 0
            
            # Process each row
            for _, row in df_std.iterrows():
                try:
                    # Skip empty rows
                    if pd.isna(row['campaign_name']) or pd.isna(row['spend_amount']):
                        continue
                    
                    # Parse data
                    reporting_date = self._parse_date_safe(row['reporting_date'])
                    if not reporting_date:
                        logger.warning(f"Could not parse date: {row['reporting_date']}")
                        continue
                    
                    meta_campaign_name = str(row['campaign_name']).strip()
                    spend_amount = self._parse_float(row['spend_amount'])
                    
                    if not spend_amount or spend_amount <= 0:
                        continue
                    
                    # Optional fields
                    ad_level = str(row.get('ad_level')) if pd.notna(row.get('ad_level')) else None
                    is_new = self._parse_boolean(row.get('is_new')) if 'is_new' in row else False
                    
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
            
            logger.info(f"Successfully processed {count} ad spend records, total spend: £{total_spend:,.2f}")
            
            return {
                'records_processed': count,
                'new_campaigns': list(new_campaigns),
                'total_spend': total_spend,
                'file_type': 'Excel',
                'sheet_used': ad_sheet
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
                            
                            if flg_name and meta_name and not flg_name.startswith('?'):
                                table_found = True
                                
                                # Clean up the names
                                flg_name = flg_name.replace('?', '').strip()
                                
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
                        flg_name = flg_name.replace('?', '').strip()
                        
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
                '%Y/%m/%d'
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
            formats = [
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%m/%d/%Y',
                '%d-%m-%Y',
                '%Y/%m/%d',
                '%d.%m.%Y',
                '%Y.%m.%d'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(value.strip(), fmt)
                    return dt.date()
                except:
                    continue
        
        return None