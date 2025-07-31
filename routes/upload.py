"""
File upload routes
"""

import os
import logging
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
from services.data_processor import DataProcessor

logger = logging.getLogger(__name__)

upload_bp = Blueprint('upload', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@upload_bp.route('/applications', methods=['POST'])
def upload_applications():
    """Handle applications (affordability check) file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"applications_{timestamp}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process file
        processor = DataProcessor()
        result = processor.process_applications_file(filepath)
        
        # Clean up file after processing
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Applications file processed successfully',
            'records_processed': result.get('records_processed', 0),
            'passed_count': result.get('passed_count', 0),
            'failed_count': result.get('failed_count', 0)
        })
        
    except Exception as e:
        logger.error(f"Error processing applications file: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@upload_bp.route('/flg-data', methods=['POST'])
def upload_flg_data():
    """Handle FLG data file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"flg_data_{timestamp}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process file
        processor = DataProcessor()
        result = processor.process_flg_data_file(filepath)
        
        # Clean up file after processing
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': 'FLG data file processed successfully',
            'records_processed': result.get('records_processed', 0),
            'new_products': result.get('new_products', []),
            'unmapped_sources': result.get('unmapped_sources', [])
        })
        
    except Exception as e:
        logger.error(f"Error processing FLG data file: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@upload_bp.route('/ad-spend', methods=['POST'])
def upload_ad_spend():
    """Handle ad spend file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ad_spend_{timestamp}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process file
        processor = DataProcessor()
        result = processor.process_ad_spend_file(filepath)
        
        # Clean up file after processing
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Ad spend file processed successfully',
            'records_processed': result.get('records_processed', 0),
            'new_campaigns': result.get('new_campaigns', []),
            'total_spend': result.get('total_spend', 0)
        })
        
    except Exception as e:
        logger.error(f"Error processing ad spend file: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@upload_bp.route('/flg-meta-mapping', methods=['POST'])
def upload_flg_meta_mapping():
    """Handle FLG to Meta name mapping file upload (Word document)"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"flg_meta_mapping_{timestamp}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process file
        processor = DataProcessor()
        result = processor.process_mapping_file(filepath)
        
        # Clean up file after processing
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': 'FLG to Meta mapping file processed successfully',
            'mappings_created': result.get('mappings_created', 0),
            'mappings_updated': result.get('mappings_updated', 0)
        })
        
    except Exception as e:
        logger.error(f"Error processing mapping file: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@upload_bp.route('/check-status', methods=['GET'])
def check_upload_status():
    """Check the status of data uploads"""
    try:
        from app import db
        from models import Application, FLGData, AdSpend
        
        # Get latest upload timestamps
        latest_application = Application.query.order_by(Application.created_at.desc()).first()
        latest_flg = FLGData.query.order_by(FLGData.created_at.desc()).first()
        latest_ad_spend = AdSpend.query.order_by(AdSpend.created_at.desc()).first()
        
        status = {
            'applications': {
                'last_upload': latest_application.created_at.isoformat() if latest_application else None,
                'total_records': Application.query.count()
            },
            'flg_data': {
                'last_upload': latest_flg.created_at.isoformat() if latest_flg else None,
                'total_records': FLGData.query.count()
            },
            'ad_spend': {
                'last_upload': latest_ad_spend.created_at.isoformat() if latest_ad_spend else None,
                'total_records': AdSpend.query.count()
            }
        }
        
        return jsonify({'success': True, 'status': status})
        
    except Exception as e:
        logger.error(f"Error checking upload status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500