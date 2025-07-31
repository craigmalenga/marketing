"""
Upload routes for handling file uploads - FIXED VERSION
routes/upload.py
"""

from flask import Blueprint, request, jsonify, render_template, current_app, session
from werkzeug.utils import secure_filename
import os
import logging
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db

# Import models
from models import Application, FLGData, AdSpend, FLGMetaMapping

logger = logging.getLogger(__name__)

upload_bp = Blueprint('upload', __name__)

# Create a module-level DataProcessor instance
data_processor = None

def get_data_processor():
    """Get or create DataProcessor instance"""
    global data_processor
    if data_processor is None:
        from services.data_processor import DataProcessor
        data_processor = DataProcessor()
    return data_processor

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    'applications': {'csv', 'xlsx', 'xls'},
    'flg': {'csv', 'xlsx', 'xls'},
    'ad_spend': {'xlsx', 'xls'},
    'mapping': {'docx', 'doc', 'xlsx', 'xls'}
}

def allowed_file(filename, file_type):
    """Check if file extension is allowed for the file type"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS.get(file_type, set())

@upload_bp.route('/upload')
def upload_page():
    """Render upload page"""
    return render_template('upload.html')

@upload_bp.route('/api/upload/applications', methods=['POST'])
def upload_applications():
    """Handle applications data upload (CSV or Excel)"""
    try:
        logger.info("Starting applications file upload")
        
        if 'file' not in request.files:
            logger.error("No file in request")
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.error("Empty filename")
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename, 'applications'):
            logger.error(f"Invalid file type: {file.filename}")
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload CSV or Excel file'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        # Ensure upload directory exists
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'data/uploads')
        upload_dir = os.path.join(upload_folder, 'applications')
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, filename)
        logger.info(f"Saving file to: {filepath}")
        file.save(filepath)
        
        logger.info(f"Processing applications file: {filename}")
        
        # Process file
        processor = get_data_processor()
        result = processor.process_applications_file(filepath)
        
        # Log upload
        log_upload('applications', filename, result)
        
        return jsonify({
            'success': True,
            'message': f"Successfully processed {result['records_processed']} applications",
            'records_processed': result['records_processed'],
            'details': result,
            'passed_count': result.get('passed_count', 0),
            'failed_count': result.get('failed_count', 0),
            'file_type': result.get('file_type', 'Unknown')
        })
        
    except Exception as e:
        logger.error(f"Error uploading applications file: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@upload_bp.route('/api/upload/flg-data', methods=['POST'])
def upload_flg_data():
    """Handle FLG data upload (CSV or Excel)"""
    try:
        logger.info("Starting FLG data file upload")
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename, 'flg'):
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload CSV or Excel file'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'data/uploads')
        upload_dir = os.path.join(upload_folder, 'flg')
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        logger.info(f"Processing FLG data file: {filename}")
        
        # Process file
        processor = get_data_processor()
        result = processor.process_flg_data_file(filepath)
        
        # Log upload
        log_upload('flg_data', filename, result)
        
        # Build detailed message
        message_parts = [f"Successfully processed {result['records_processed']} FLG records"]
        
        if result.get('new_products'):
            message_parts.append(f"Added {len(result['new_products'])} new products")
        
        if result.get('unmapped_sources'):
            message_parts.append(f"Found {len(result['unmapped_sources'])} unmapped marketing sources")
        
        return jsonify({
            'success': True,
            'message': '. '.join(message_parts),
            'records_processed': result['records_processed'],
            'details': result,
            'new_products': result.get('new_products', []),
            'unmapped_sources': result.get('unmapped_sources', []),
            'file_type': result.get('file_type', 'Unknown')
        })
        
    except Exception as e:
        logger.error(f"Error uploading FLG data file: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@upload_bp.route('/api/upload/ad-spend', methods=['POST'])
def upload_ad_spend():
    """Handle ad spend data upload"""
    try:
        logger.info("Starting ad spend file upload")
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename, 'ad_spend'):
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload Excel file'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'data/uploads')
        upload_dir = os.path.join(upload_folder, 'ad_spend')
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        logger.info(f"Processing ad spend file: {filename}")
        
        # Process file
        processor = get_data_processor()
        result = processor.process_ad_spend_file(filepath)
        
        # Log upload
        log_upload('ad_spend', filename, result)
        
        # Build detailed message
        message_parts = [f"Successfully processed {result['records_processed']} ad spend records"]
        
        if result.get('total_spend'):
            message_parts.append(f"Total spend: £{result['total_spend']:,.2f}")
        
        if result.get('new_campaigns'):
            message_parts.append(f"Added {len(result['new_campaigns'])} new campaigns")
        
        return jsonify({
            'success': True,
            'message': '. '.join(message_parts),
            'records_processed': result['records_processed'],
            'details': result,
            'new_campaigns': result.get('new_campaigns', []),
            'total_spend': result.get('total_spend', 0),
            'sheet_used': result.get('sheet_used', 'Unknown'),
            'file_type': result.get('file_type', 'Unknown')
        })
        
    except Exception as e:
        logger.error(f"Error uploading ad spend file: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@upload_bp.route('/api/upload/flg-meta-mapping', methods=['POST'])
def upload_flg_meta_mapping():
    """Handle FLG to Meta name mapping upload"""
    try:
        logger.info("Starting mapping file upload")
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename, 'mapping'):
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload Word or Excel file'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'data/uploads')
        upload_dir = os.path.join(upload_folder, 'mappings')
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        logger.info(f"Processing mapping file: {filename}")
        
        # Process file
        processor = get_data_processor()
        result = processor.process_mapping_file(filepath)
        
        # Log upload
        log_upload('mapping', filename, result)
        
        # Build detailed message
        message_parts = []
        if result['mappings_created'] > 0:
            message_parts.append(f"Created {result['mappings_created']} new mappings")
        if result['mappings_updated'] > 0:
            message_parts.append(f"Updated {result['mappings_updated']} existing mappings")
        
        if not message_parts:
            message_parts.append("No new mappings found")
        
        return jsonify({
            'success': True,
            'message': '. '.join(message_parts),
            'records_processed': result['mappings_created'] + result['mappings_updated'],
            'details': result,
            'file_type': result.get('file_type', 'Unknown')
        })
        
    except Exception as e:
        logger.error(f"Error uploading mapping file: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@upload_bp.route('/api/upload/check-status')
def check_upload_status():
    """Check the current upload status and data availability"""
    try:
        # Get counts from database
        applications_count = Application.query.count()
        flg_count = FLGData.query.count()
        ad_spend_count = AdSpend.query.count()
        mapping_count = FLGMetaMapping.query.count()
        
        # Get latest upload dates
        latest_app = db.session.query(func.max(Application.created_at)).scalar()
        latest_flg = db.session.query(func.max(FLGData.created_at)).scalar()
        latest_ad = db.session.query(func.max(AdSpend.created_at)).scalar()
        
        # Get upload history from session or database
        recent_uploads = get_recent_uploads()
        
        return jsonify({
            'success': True,
            'status': {
                'applications': {
                    'total_records': applications_count,
                    'last_upload': latest_app.isoformat() if latest_app else None
                },
                'flg_data': {
                    'total_records': flg_count,
                    'last_upload': latest_flg.isoformat() if latest_flg else None
                },
                'ad_spend': {
                    'total_records': ad_spend_count,
                    'last_upload': latest_ad.isoformat() if latest_ad else None
                },
                'mappings': {
                    'total_records': mapping_count
                }
            },
            'data_counts': {
                'applications': applications_count,
                'flg_data': flg_count,
                'ad_spend': ad_spend_count,
                'mappings': mapping_count
            },
            'latest_uploads': {
                'applications': latest_app.isoformat() if latest_app else None,
                'flg_data': latest_flg.isoformat() if latest_flg else None,
                'ad_spend': latest_ad.isoformat() if latest_ad else None
            },
            'recent_uploads': recent_uploads
        })
        
    except Exception as e:
        logger.error(f"Error checking upload status: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

def log_upload(upload_type, filename, result):
    """Log upload to session"""
    if 'upload_history' not in session:
        session['upload_history'] = []
    
    upload_entry = {
        'type': upload_type,
        'filename': filename,
        'timestamp': datetime.now().isoformat(),
        'records': result.get('records_processed', 0),
        'status': 'success' if result.get('records_processed', 0) > 0 else 'warning',
        'details': {
            'file_type': result.get('file_type', 'Unknown'),
            'passed_count': result.get('passed_count'),
            'failed_count': result.get('failed_count'),
            'new_products': result.get('new_products', []),
            'total_spend': result.get('total_spend'),
            'mappings_created': result.get('mappings_created'),
            'mappings_updated': result.get('mappings_updated')
        }
    }
    
    session['upload_history'].insert(0, upload_entry)
    session['upload_history'] = session['upload_history'][:10]  # Keep last 10
    session.modified = True

def get_recent_uploads():
    """Get recent upload history"""
    history = session.get('upload_history', [])
    
    # Format for display
    formatted_history = []
    for entry in history:
        timestamp = datetime.fromisoformat(entry['timestamp'])
        formatted_entry = {
            'type': entry['type'],
            'filename': entry['filename'],
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'relative_time': get_relative_time(timestamp),
            'records': entry['records'],
            'status': entry['status'],
            'details': entry.get('details', {})
        }
        formatted_history.append(formatted_entry)
    
    return formatted_history

def get_relative_time(timestamp):
    """Get relative time string (e.g., '2 hours ago')"""
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"