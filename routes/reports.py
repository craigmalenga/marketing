"""
Report generation routes
"""

import logging
from flask import Blueprint, request, jsonify, send_file
from datetime import datetime, timedelta
from services.report_generator import ReportGenerator
import os

logger = logging.getLogger(__name__)

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/credit-performance', methods=['GET'])
def get_credit_performance():
    """Generate credit performance by product report"""
    try:
        # Get filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        product_category = request.args.get('product_category')
        
        # Parse dates
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            # Default to last 30 days
            start_date = datetime.now() - timedelta(days=30)
            
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date = datetime.now()
        
        # Generate report
        generator = ReportGenerator()
        report_data = generator.generate_credit_performance_report(
            start_date=start_date,
            end_date=end_date,
            product_category=product_category
        )
        
        return jsonify({
            'success': True,
            'data': report_data,
            'filters': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'product_category': product_category
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating credit performance report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/marketing-campaign', methods=['GET'])
def get_marketing_campaign():
    """Generate marketing campaign performance report"""
    try:
        # Get filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        campaign_name = request.args.get('campaign_name')
        ad_level = request.args.get('ad_level')
        
        # Parse dates
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_date = datetime.now() - timedelta(days=30)
            
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date = datetime.now()
        
        # Generate report
        generator = ReportGenerator()
        report_data = generator.generate_marketing_campaign_report(
            start_date=start_date,
            end_date=end_date,
            campaign_name=campaign_name,
            ad_level=ad_level
        )
        
        return jsonify({
            'success': True,
            'data': report_data,
            'filters': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'campaign_name': campaign_name,
                'ad_level': ad_level
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating marketing campaign report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/export/credit-performance', methods=['POST'])
def export_credit_performance():
    """Export credit performance report to Excel"""
    try:
        # Get filter parameters from request body
        data = request.get_json()
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d') if data.get('start_date') else datetime.now() - timedelta(days=30)
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d') if data.get('end_date') else datetime.now()
        product_category = data.get('product_category')
        
        # Generate report
        generator = ReportGenerator()
        filepath = generator.export_credit_performance_report(
            start_date=start_date,
            end_date=end_date,
            product_category=product_category
        )
        
        return send_file(
            filepath,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'credit_performance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        
    except Exception as e:
        logger.error(f"Error exporting credit performance report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/export/marketing-campaign', methods=['POST'])
def export_marketing_campaign():
    """Export marketing campaign report to Excel"""
    try:
        # Get filter parameters from request body
        data = request.get_json()
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d') if data.get('start_date') else datetime.now() - timedelta(days=30)
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d') if data.get('end_date') else datetime.now()
        campaign_name = data.get('campaign_name')
        ad_level = data.get('ad_level')
        
        # Generate report
        generator = ReportGenerator()
        filepath = generator.export_marketing_campaign_report(
            start_date=start_date,
            end_date=end_date,
            campaign_name=campaign_name,
            ad_level=ad_level
        )
        
        return send_file(
            filepath,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'marketing_campaign_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        
    except Exception as e:
        logger.error(f"Error exporting marketing campaign report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/summary', methods=['GET'])
def get_summary():
    """Get summary statistics for dashboard"""
    try:
        generator = ReportGenerator()
        summary = generator.get_summary_statistics()
        
        return jsonify({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        logger.error(f"Error generating summary statistics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/available-filters', methods=['GET'])
def get_available_filters():
    """Get available filter options"""
    try:
        from app import db
        from models import Product, Campaign, AdSpend
        
        # Get unique products
        products = db.session.query(Product.name, Product.category).distinct().all()
        product_categories = list(set([p.category for p in products if p.category]))
        
        # Get unique campaigns
        campaigns = db.session.query(Campaign.name).distinct().all()
        campaign_names = [c.name for c in campaigns]
        
        # Get unique ad levels
        ad_levels = db.session.query(AdSpend.ad_level).distinct().filter(AdSpend.ad_level.isnot(None)).all()
        ad_level_names = [a.ad_level for a in ad_levels]
        
        return jsonify({
            'success': True,
            'filters': {
                'product_categories': sorted(product_categories),
                'products': sorted([p.name for p in products]),
                'campaigns': sorted(campaign_names),
                'ad_levels': sorted(ad_level_names)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting available filters: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500