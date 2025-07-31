"""
Data processing service for handling file uploads
"""

import pandas as pd
import logging
from datetime import datetime
from app import db
from models import (
    Application, FLGData, AdSpend, Product, Campaign,
    StatusMapping, FLGMetaMapping
)
import os

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
                if 'DateTime' in str(row.values):
                    header_row = idx
                    break
            
            if header_row is None:
                logger.warning("Could not find header row in applications sheet")
                return 0
            
            # Set correct column names
            df.columns = df.iloc[header_row]
            df = df[header_row + 1:].reset_index(drop=True)
            
            # Process each row
            count = 0
            for _, row in df.iterrows():
                # Skip empty rows
                if pd.isna(row.get('Lead ID')):
                    continue
                
                # Check if application already exists
                lead_id = str(row.get('Lead ID'))
                existing = Application.query.filter_by(lead_id=lead_id).first()
                
                if existing:
                    # Update existing record
                    app = existing
                else:
                    # Create new record
                    app = Application()
                
                # Set fields
                app.lead_id = lead_id
                app.datetime = Application.parse_excel_datetime(row.get('DateTime'))
                app.status = row.get('Status')
                app.user = row.get('User')
                app.lead_datetime = Application.parse_excel_datetime(row.get('LeadDateTime'))
                app.lead_name = row.get('LeadName')
                app.lead_postcode = row.get('LeadPostcode')
                app.lead_introducer = row.get('LeadIntroducer')
                app.lead_partner = row.get('LeadPartner')
                app.lead_cost = self._parse_float(row.get('LeadCost'))
                app.lead_value = self._parse_float(row.get('LeadValue'))
                app.current_status = row.get('CurrentStatus')
                app.affordability_result = affordability_result
                
                if not existing:
                    db.session.add(app)
                
                count += 1
            
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
                if 'Reference' in str(row.values):
                    header_row = idx
                    break
            
            if header_row is None:
                raise ValueError("Could not find header row in FLG data file")
            
            # Set correct column names
            df.columns = df.iloc[header_row]
            df = df[header_row + 1:].reset_index(drop=True)
            
            # Track new products and unmapped sources
            new_products = set()
            unmapped_sources = set()
            
            # Process each row
            count = 0
            for _, row in df.iterrows():
                # Skip empty rows
                if pd.isna(row.get('Reference')):
                    continue
                
                # Check if FLG data already exists
                reference = str(row.get('Reference'))
                existing = FLGData.query.filter_by(reference=reference).first()
                
                if existing:
                    flg = existing
                else:
                    flg = FLGData()
                
                # Set fields
                flg.reference = reference
                flg.received_datetime = FLGData.parse_excel_datetime(row.get('ReceivedDateTime'))
                flg.status = row.get('Status')
                flg.marketing_source = row.get('MarketingSource')
                flg.data5_value = self._parse_float(row.get('Data5'))
                flg.data6_payment_type = row.get('Data6')
                flg.data7_value = self._parse_float(row.get('Data7'))
                flg.data8_value = self._parse_float(row.get('Data8'))
                flg.data10_value = self._parse_float(row.get('Data10'))
                flg.data29_product_description = row.get('Data29')
                
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
            # Read Excel file
            df = pd.read_excel(filepath)
            
            # Find the header row (looking for date-related column)
            header_row = None
            for idx, row in df.iterrows():
                row_str = str(row.values)
                if any(term in row_str.lower() for term in ['date', 'reporting', 'end']):
                    header_row = idx
                    break
            
            if header_row is None:
                # Try first row as header
                header_row = 0
            
            # Set correct column names
            df.columns = df.iloc[header_row]
            df = df[header_row + 1:].reset_index(drop=True)
            
            # Identify columns
            date_col = None
            campaign_col = None
            ad_level_col = None
            spend_col = None
            
            for col in df.columns:
                col_lower = str(col).lower()
                if 'date' in col_lower:
                    date_col = col
                elif 'campaign' in col_lower and 'name' in col_lower:
                    campaign_col = col
                elif 'ad' in col_lower and 'level' in col_lower:
                    ad_level_col = col
                elif 'spend' in col_lower or 'amount' in col_lower or 'cost' in col_lower:
                    spend_col = col
            
            if not all([date_col, campaign_col, spend_col]):
                raise ValueError("Could not identify required columns in ad spend file")
            
            # Track new campaigns
            new_campaigns = set()
            total_spend = 0
            
            # Process each row
            count = 0
            for _, row in df.iterrows():
                # Skip empty rows
                if pd.isna(row.get(campaign_col)):
                    continue
                
                # Parse data
                reporting_date = AdSpend.parse_excel_date(row.get(date_col))
                if not reporting_date:
                    continue
                
                meta_campaign_name = str(row.get(campaign_col))
                ad_level = str(row.get(ad_level_col)) if ad_level_col and not pd.isna(row.get(ad_level_col)) else None
                spend_amount = self._parse_float(row.get(spend_col))
                
                if not spend_amount or spend_amount == 0:
                    continue
                
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
                    campaign=campaign
                )
                
                db.session.add(ad_spend)
                total_spend += spend_amount
                count += 1
            
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
            
            if file_ext in ['.docx', '.doc']:
                # Process Word document
                import docx
                doc = docx.Document(filepath)
                
                mappings_created = 0
                mappings_updated = 0
                
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
                    flg_name = str(row.iloc[0]).strip() if not pd.isna(row.iloc[0]) else None
                    meta_name = str(row.iloc[1]).strip() if len(row) > 1 and not pd.isna(row.iloc[1]) else None
                    
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
            return float(value)
        except:
            return None