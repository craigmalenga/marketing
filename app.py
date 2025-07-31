"""
Marketing Analytics Platform
Main Flask Application
Version: 1.0
Last Updated: 31 July 2025
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.utils import secure_filename
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)

# Import models after db initialization to avoid circular imports
with app.app_context():
    from models import (
        Campaign, Product, StatusMapping, Application,
        FLGData, AdSpend, FLGMetaMapping
    )
    
    # Import routes after models
    from routes import upload_bp, reports_bp, mappings_bp
    
    # Register blueprints
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(mappings_bp, url_prefix='/api/mappings')

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    """File upload page"""
    return render_template('upload.html')

@app.route('/credit-performance')
def credit_performance():
    """Credit performance report page"""
    return render_template('credit_performance.html')

@app.route('/marketing-campaign')
def marketing_campaign():
    """Marketing campaign report page"""
    return render_template('marketing_campaign.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
        logger.error(f"Database health check failed: {e}")
    
    return jsonify({
        'status': 'ok' if db_status == 'healthy' else 'error',
        'timestamp': datetime.utcnow().isoformat(),
        'database': db_status,
        'version': '1.0'
    })

@app.route('/api/upload-history')
def upload_history():
    """Get history of file uploads"""
    try:
        # For now, return mock data - will implement with database later
        history = [
            {
                'id': 1,
                'filename': 'applications_week_28.xlsx',
                'type': 'applications',
                'uploaded_at': '2025-07-24T10:30:00',
                'status': 'processed',
                'records': 268
            },
            {
                'id': 2,
                'filename': 'flg_data_week_28.xlsx',
                'type': 'flg_data',
                'uploaded_at': '2025-07-24T10:31:00',
                'status': 'processed',
                'records': 1250
            },
            {
                'id': 3,
                'filename': 'ad_spend_week_28.xlsx',
                'type': 'ad_spend',
                'uploaded_at': '2025-07-24T10:32:00',
                'status': 'processed',
                'records': 45
            }
        ]
        return jsonify({'success': True, 'data': history})
    except Exception as e:
        logger.error(f"Error fetching upload history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

@app.cli.command()
def init_db():
    """Initialize the database"""
    db.create_all()
    logger.info("Database initialized successfully")
    
    # Create default status mappings
    default_statuses = StatusMapping.get_default_mappings()
    
    for status_data in default_statuses:
        status = StatusMapping.query.filter_by(status_name=status_data['status_name']).first()
        if not status:
            status = StatusMapping(**status_data)
            db.session.add(status)
    
    db.session.commit()
    logger.info("Default status mappings created")

@app.cli.command()
def seed_test_data():
    """Seed database with test data"""
    # Add some test products
    products = [
        {'name': 'Sofa - Aldis', 'category': 'Sofa'},
        {'name': 'Sofa - Kyle', 'category': 'Sofa'},
        {'name': 'Sofa - Hamilton', 'category': 'Sofa'},
        {'name': 'Sofa - Lawson', 'category': 'Sofa'},
        {'name': 'Rattan', 'category': 'Furniture'},
        {'name': 'Bed', 'category': 'Furniture'},
        {'name': 'Cooker', 'category': 'Appliances'},
        {'name': 'Fridge freezer', 'category': 'Appliances'},
        {'name': 'TV', 'category': 'Electronics'},
        {'name': 'Console', 'category': 'Electronics'},
        {'name': 'Laptop', 'category': 'Electronics'},
        {'name': 'Washer dryer', 'category': 'Appliances'},
        {'name': 'Vacuum', 'category': 'Appliances'},
        {'name': 'Hot tub', 'category': 'Leisure'},
        {'name': 'BBQ', 'category': 'Outdoor'}
    ]
    
    for product_data in products:
        product = Product.query.filter_by(name=product_data['name']).first()
        if not product:
            product = Product(**product_data)
            db.session.add(product)
    
    db.session.commit()
    logger.info("Test data seeded successfully")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        logger.info("Marketing Analytics Platform started")
        logger.info(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
        logger.info(f"Export folder: {app.config['EXPORT_FOLDER']}")
    
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])