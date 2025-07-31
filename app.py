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

# Configure upload folder
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

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
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'applications'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'flg'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'ad_spend'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'mappings'), exist_ok=True)

# Import models after db initialization to avoid circular imports
with app.app_context():
    from models import (
        Campaign, Product, StatusMapping, Application,
        FLGData, AdSpend, FLGMetaMapping
    )
    
    # Import routes after models
    from routes import upload_bp, reports_bp, mappings_bp
    
    # Register blueprints WITHOUT the /api prefix since routes already include it
    app.register_blueprint(upload_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(mappings_bp)

# Define main routes
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/credit-performance')
def credit_performance():
    """Credit performance report page"""
    return render_template('credit_performance.html')

@app.route('/marketing-campaign')
def marketing_campaign():
    """Marketing campaign report page"""
    return render_template('marketing_campaign.html')

@app.route('/admin')
def admin_page():
    """Admin page for database initialization"""
    return render_template('admin.html')

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
        'timestamp': datetime.now().isoformat(),
        'database': db_status,
        'version': '1.0'
    })

@app.route('/api/init-database', methods=['POST'])
def init_database_endpoint():
    """Initialize database tables via API endpoint"""
    try:
        # Create all tables
        db.create_all()
        
        # Create default status mappings
        from models import StatusMapping, Product
        
        # Check if already initialized
        if StatusMapping.query.count() > 0:
            return jsonify({
                'success': True,
                'message': 'Database already initialized',
                'status_mappings_created': 0,
                'products_created': 0
            })
        
        default_statuses = StatusMapping.get_default_mappings()
        created_statuses = 0
        
        for status_data in default_statuses:
            status = StatusMapping.query.filter_by(status_name=status_data['status_name']).first()
            if not status:
                status = StatusMapping(**status_data)
                db.session.add(status)
                created_statuses += 1
        
        # Create default products
        default_products = [
            {'name': 'Sofa - Aldis', 'category': 'Sofa'},
            {'name': 'Sofa - Kyle', 'category': 'Sofa'},
            {'name': 'Sofa - Hamilton', 'category': 'Sofa'},
            {'name': 'Sofa - Lawson', 'category': 'Sofa'},
            {'name': 'Sofa - Lucy', 'category': 'Sofa'},
            {'name': 'Sofa - Roma', 'category': 'Sofa'},
            {'name': 'Sofa - other', 'category': 'Sofa'},
            {'name': 'Rattan', 'category': 'Furniture'},
            {'name': 'Bed', 'category': 'Furniture'},
            {'name': 'Dining set', 'category': 'Furniture'},
            {'name': 'Cooker', 'category': 'Appliances'},
            {'name': 'Fridge freezer', 'category': 'Appliances'},
            {'name': 'Washer dryer', 'category': 'Appliances'},
            {'name': 'Dish washer', 'category': 'Appliances'},
            {'name': 'Microwave', 'category': 'Appliances'},
            {'name': 'TV', 'category': 'Electronics'},
            {'name': 'Console', 'category': 'Electronics'},
            {'name': 'Laptop', 'category': 'Electronics'},
            {'name': 'Vacuum', 'category': 'Appliances'},
            {'name': 'Hot tub', 'category': 'Leisure'},
            {'name': 'BBQ', 'category': 'Outdoor'},
            {'name': 'Air fryer', 'category': 'Appliances'},
            {'name': 'Ninja products', 'category': 'Appliances'},
            {'name': 'Kitchen Bundle', 'category': 'Appliances'},
            {'name': 'Other', 'category': 'Other'}
        ]
        
        created_products = 0
        for product_data in default_products:
            product = Product.query.filter_by(name=product_data['name']).first()
            if not product:
                product = Product(**product_data)
                db.session.add(product)
                created_products += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Database initialized successfully',
            'tables_created': True,
            'status_mappings_created': created_statuses,
            'products_created': created_products
        })
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload-history')
def upload_history():
    """Get history of file uploads"""
    try:
        # Get real upload history from database
        from models import Application, FLGData, AdSpend
        from sqlalchemy import func
        
        history = []
        
        # Get latest application upload
        latest_app = db.session.query(
            func.max(Application.created_at).label('latest'),
            func.count(Application.id).label('count')
        ).first()
        
        if latest_app.latest:
            history.append({
                'id': 1,
                'filename': 'Applications data',
                'type': 'applications',
                'uploaded_at': latest_app.latest.isoformat(),
                'status': 'processed',
                'records': latest_app.count
            })
        
        # Get latest FLG upload
        latest_flg = db.session.query(
            func.max(FLGData.created_at).label('latest'),
            func.count(FLGData.id).label('count')
        ).first()
        
        if latest_flg.latest:
            history.append({
                'id': 2,
                'filename': 'FLG data',
                'type': 'flg_data',
                'uploaded_at': latest_flg.latest.isoformat(),
                'status': 'processed',
                'records': latest_flg.count
            })
        
        # Get latest ad spend upload
        latest_ad = db.session.query(
            func.max(AdSpend.created_at).label('latest'),
            func.count(AdSpend.id).label('count')
        ).first()
        
        if latest_ad.latest:
            history.append({
                'id': 3,
                'filename': 'Ad spend data',
                'type': 'ad_spend', 
                'uploaded_at': latest_ad.latest.isoformat(),
                'status': 'processed',
                'records': latest_ad.count
            })
        
        return jsonify({'success': True, 'data': history})
        
    except Exception as e:
        logger.error(f"Error fetching upload history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.error(f"404 error: {request.url}")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {str(error)}", exc_info=True)
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

@app.cli.command()
def init_db():
    """Initialize the database"""
    db.create_all()
    logger.info("Database initialized successfully")
    
    # Create default status mappings
    from models import StatusMapping
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
    from models import Product
    
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