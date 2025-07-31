"""
Marketing Analytics Platform
Main Flask Application
Version: 1.8
Last Updated: 31 July 2025
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.utils import secure_filename
from sqlalchemy import func, text, inspect
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# CRITICAL FIX: Handle Railway Postgres URL properly with better error handling
database_url = os.environ.get('DATABASE_URL')

# Log the database URL status BEFORE any modifications
if database_url:
    print(f"DATABASE_URL found: {database_url[:30]}...")
else:
    print("CRITICAL WARNING: DATABASE_URL environment variable not found!")

# Ensure we have a database URL
if not database_url:
    # Check for alternative environment variable names
    database_url = os.environ.get('RAILWAY_DATABASE_URL') or os.environ.get('POSTGRES_URL')
    if database_url:
        print(f"Found alternative database URL: {database_url[:30]}...")
    else:
        # CRITICAL: Exit if no database URL in production
        if os.environ.get('RAILWAY_ENVIRONMENT') == 'production':
            raise RuntimeError("CRITICAL ERROR: No DATABASE_URL found in production environment! Check Railway environment variables.")
        else:
            # Only use SQLite in development
            database_url = 'sqlite:///local.db'
            print("WARNING: Using local SQLite for development only")

# Fix postgres:// to postgresql:// for SQLAlchemy
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
    print("Converted postgres:// to postgresql://")

# Set the database URL
app.config['SQLALCHEMY_DATABASE_URI'] = database_url

# Log final database configuration
if 'postgresql' in database_url:
    # Extract just the database host for logging (hide credentials)
    if '@' in database_url:
        db_host = database_url.split('@')[1].split('/')[0]
        print(f"Using PostgreSQL database at: {db_host}")
    else:
        print("Using PostgreSQL database")
elif 'sqlite' in database_url:
    print("WARNING: Using SQLite database - data will not persist in production!")

# Configure upload folder
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True  # Enable SQL query logging

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log database connection info
logger.info(f"Database URI configured: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")

# Test database connection immediately
try:
    with app.app_context():
        # Test the connection
        result = db.session.execute(text('SELECT 1')).scalar()
        if result == 1:
            logger.info("✓ Database connection test successful")
        else:
            logger.error("✗ Database connection test failed - unexpected result")
except Exception as e:
    logger.error(f"✗ CRITICAL: Database connection test failed: {e}")
    if os.environ.get('RAILWAY_ENVIRONMENT') == 'production':
        raise RuntimeError(f"Cannot start app - database connection failed: {e}")

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

@app.route('/product-category-analysis')
def product_category_analysis():
    """Product category analysis page"""
    return render_template('product_category_analysis.html')

@app.route('/admin')
def admin_page():
    """Admin page for database initialization"""
    return render_template('admin.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        result = db.session.execute(text('SELECT 1')).scalar()
        db_status = 'healthy' if result == 1 else 'unhealthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
        logger.error(f"Database health check failed: {e}")
    
    return jsonify({
        'status': 'ok' if db_status == 'healthy' else 'error',
        'timestamp': datetime.now().isoformat(),
        'database': db_status,
        'version': '1.8'
    })

@app.route('/api/debug/db-info')
def debug_db_info():
    """Check which database we're connected to and current data"""
    try:
        # Get database URL (hide credentials)
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        if '@' in db_url:
            parts = db_url.split('@')
            db_info = parts[0].split('://')[0] + '://***@' + parts[1]
        else:
            db_info = db_url
        
        # Test connection and get database info
        if 'postgresql' in db_url:
            result = db.session.execute(text('SELECT current_database(), version()')).fetchone()
            current_db = result[0] if result else None
            db_version = result[1][:50] if result else None
        else:
            current_db = 'SQLite'
            db_version = 'SQLite version'
        
        # Check if tables exist
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        # Get counts for each table
        counts = {}
        tables = ['ad_spend', 'campaigns', 'flg_data', 'applications', 'products', 'status_mappings']
        
        for table in tables:
            if table in existing_tables:
                try:
                    count = db.session.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar()
                    counts[table] = count
                except Exception as e:
                    counts[table] = f'error: {str(e)}'
            else:
                counts[table] = 'table not found'
        
        # Get ad spend details if table exists
        ad_spend_details = None
        if 'ad_spend' in existing_tables and counts.get('ad_spend', 0) > 0:
            try:
                total_spend = db.session.execute(text('SELECT SUM(spend_amount) FROM ad_spend')).scalar() or 0
                recent_records = db.session.execute(
                    text('SELECT reporting_end_date, meta_campaign_name, spend_amount FROM ad_spend ORDER BY created_at DESC LIMIT 5')
                ).fetchall()
                
                ad_spend_details = {
                    'total_spend': float(total_spend),
                    'recent_records': [
                        {
                            'date': str(r[0]) if r[0] else None,
                            'campaign': r[1],
                            'amount': float(r[2]) if r[2] else 0
                        } for r in recent_records
                    ]
                }
            except Exception as e:
                ad_spend_details = {'error': str(e)}
        
        # Check environment variables
        env_vars = {
            'DATABASE_URL': 'SET' if os.environ.get('DATABASE_URL') else 'NOT SET',
            'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT', 'NOT SET'),
            'RAILWAY_DATABASE_URL': 'SET' if os.environ.get('RAILWAY_DATABASE_URL') else 'NOT SET',
            'POSTGRES_URL': 'SET' if os.environ.get('POSTGRES_URL') else 'NOT SET',
        }
        
        return jsonify({
            'success': True,
            'database_url': db_info,
            'current_database': current_db,
            'postgres_version': db_version,
            'existing_tables': existing_tables,
            'table_counts': counts,
            'ad_spend_details': ad_spend_details,
            'environment': os.environ.get('RAILWAY_ENVIRONMENT', 'local'),
            'environment_variables': env_vars,
            'connection_test': 'PASSED' if current_db else 'FAILED'
        })
        
    except Exception as e:
        logger.error(f"Error in db info endpoint: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'database_url': app.config['SQLALCHEMY_DATABASE_URI'][:30] + '...'
        }), 500

@app.route('/api/debug/test-insert')
def test_database_insert():
    """Test if we can insert data into the database"""
    try:
        # Test creating a campaign
        test_campaign = Campaign(
            name=f'Test Campaign {datetime.now().timestamp()}',
            meta_name='Test Meta Campaign'
        )
        db.session.add(test_campaign)
        db.session.flush()  # Get the ID
        
        # Test creating an ad spend record
        test_ad_spend = AdSpend(
            reporting_end_date=datetime.now().date(),
            meta_campaign_name=test_campaign.meta_name,
            spend_amount=123.45,
            campaign_id=test_campaign.id
        )
        db.session.add(test_ad_spend)
        
        # Commit the transaction
        db.session.commit()
        logger.info("Test insert: Successfully committed test data")
        
        # Verify it was saved
        saved_campaign = Campaign.query.filter_by(id=test_campaign.id).first()
        saved_ad_spend = AdSpend.query.filter_by(campaign_id=test_campaign.id).first()
        
        return jsonify({
            'success': True,
            'message': 'Test insert successful',
            'campaign_created': {
                'id': saved_campaign.id,
                'name': saved_campaign.name
            } if saved_campaign else None,
            'ad_spend_created': {
                'id': saved_ad_spend.id,
                'amount': saved_ad_spend.spend_amount
            } if saved_ad_spend else None,
            'database_type': 'PostgreSQL' if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Test insert failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@app.route('/api/init-database', methods=['POST'])
def init_database_endpoint():
    """Initialize database tables via API endpoint"""
    try:
        # Log current database
        db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        logger.info(f"Initializing database: {db_url[:50]}...")
        
        # Create all tables
        db.create_all()
        
        # Verify tables were created
        inspector = inspect(db.engine)
        created_tables = inspector.get_table_names()
        
        # Create default status mappings
        from models import StatusMapping, Product
        
        # Check if already initialized
        status_count = StatusMapping.query.count()
        if status_count > 0:
            return jsonify({
                'success': True,
                'message': 'Database already initialized',
                'tables': created_tables,
                'status_mappings_count': status_count
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
            'tables_created': created_tables,
            'status_mappings_created': created_statuses,
            'products_created': created_products,
            'database_type': 'PostgreSQL' if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite'
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

@app.route('/api/debug/database-check')
def debug_database_check():
    """Debug endpoint to check database contents"""
    try:
        from models import (
            Application, FLGData, AdSpend, Product, Campaign,
            StatusMapping, FLGMetaMapping
        )
        
        # Get counts
        counts = {
            'applications': Application.query.count(),
            'flg_data': FLGData.query.count(),
            'ad_spend': AdSpend.query.count(),
            'products': Product.query.count(),
            'campaigns': Campaign.query.count(),
            'status_mappings': StatusMapping.query.count(),
            'flg_meta_mappings': FLGMetaMapping.query.count()
        }
        
        # Get ad spend summary
        ad_spend_summary = None
        if counts['ad_spend'] > 0:
            total_spend = db.session.query(func.sum(AdSpend.spend_amount)).scalar() or 0
            ad_spend_summary = {
                'total_records': counts['ad_spend'],
                'total_spend': float(total_spend),
                'average_spend': float(total_spend) / counts['ad_spend'] if counts['ad_spend'] > 0 else 0
            }
        
        # Get sample data
        samples = {
            'applications': [a.to_dict() for a in Application.query.limit(5).all()],
            'flg_data': [f.to_dict() for f in FLGData.query.limit(5).all()],
            'ad_spend': [a.to_dict() for a in AdSpend.query.limit(5).all()],
            'products': [p.to_dict() for p in Product.query.limit(10).all()],
            'campaigns': [c.to_dict() for c in Campaign.query.limit(5).all()],
            'status_mappings': [s.to_dict() for s in StatusMapping.query.limit(5).all()],
            'flg_meta_mappings': [f.to_dict() for f in FLGMetaMapping.query.limit(5).all()]
        }
        
        # Get database info
        db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if '@' in db_url:
            db_url = db_url.split('@')[1]
        
        db_info = {
            'database_type': 'PostgreSQL' if 'postgresql' in db_url else 'SQLite',
            'database_location': db_url,
            'tables': list(db.metadata.tables.keys())
        }
        
        return jsonify({
            'success': True,
            'counts': counts,
            'ad_spend_summary': ad_spend_summary,
            'samples': samples,
            'database_info': db_info
        })
        
    except Exception as e:
        logger.error(f"Error in database check: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/debug/ad-spend-details')
def debug_ad_spend_details():
    """Debug endpoint to check ad spend details"""
    try:
        # Get ad spend by campaign
        campaign_spending = db.session.query(
            AdSpend.meta_campaign_name,
            func.count(AdSpend.id).label('record_count'),
            func.sum(AdSpend.spend_amount).label('total_spend'),
            func.min(AdSpend.reporting_end_date).label('earliest_date'),
            func.max(AdSpend.reporting_end_date).label('latest_date')
        ).group_by(AdSpend.meta_campaign_name).all()
        
        # Get recent ad spend records
        recent_records = AdSpend.query.order_by(AdSpend.created_at.desc()).limit(20).all()
        
        # Check if there are any campaigns without ad spend
        campaigns_without_spend = db.session.query(Campaign).outerjoin(
            AdSpend, Campaign.id == AdSpend.campaign_id
        ).filter(AdSpend.id.is_(None)).all()
        
        return jsonify({
            'success': True,
            'summary': {
                'total_records': AdSpend.query.count(),
                'total_spend': db.session.query(func.sum(AdSpend.spend_amount)).scalar() or 0,
                'unique_campaigns': db.session.query(func.count(distinct(AdSpend.meta_campaign_name))).scalar() or 0
            },
            'by_campaign': [
                {
                    'campaign': row.meta_campaign_name,
                    'records': row.record_count,
                    'total_spend': float(row.total_spend or 0),
                    'date_range': f"{row.earliest_date} to {row.latest_date}"
                } for row in campaign_spending
            ],
            'recent_records': [r.to_dict() for r in recent_records],
            'campaigns_without_spend': [c.to_dict() for c in campaigns_without_spend],
            'database_type': 'PostgreSQL' if 'postgresql' in app.config.get('SQLALCHEMY_DATABASE_URI', '') else 'SQLite'
        })
        
    except Exception as e:
        logger.error(f"Error in ad spend details: {e}", exc_info=True)
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
        # Verify database connection before starting
        try:
            db.session.execute(text('SELECT 1'))
            logger.info("✓ Final database connection check passed")
            
            # Show which database we're using
            db_type = 'PostgreSQL' if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite'
            logger.info(f"Starting app with {db_type} database")
            
            # Create tables if they don't exist
            db.create_all()
            logger.info("✓ Database tables ready")
            
        except Exception as e:
            logger.error(f"✗ Cannot start app - database error: {e}")
            raise
    
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])