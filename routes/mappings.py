"""
Mapping management routes - FIXED with /api prefix
routes/mappings.py
"""

import logging
from flask import Blueprint, request, jsonify
from app import db
from models import StatusMapping, FLGMetaMapping

logger = logging.getLogger(__name__)

mappings_bp = Blueprint('mappings', __name__)

@mappings_bp.route('/api/mappings/status', methods=['GET'])
def get_status_mappings():
    """Get all status mappings"""
    try:
        mappings = StatusMapping.query.order_by(StatusMapping.status_name).all()
        return jsonify({
            'success': True,
            'data': [m.to_dict() for m in mappings]
        })
    except Exception as e:
        logger.error(f"Error fetching status mappings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mappings_bp.route('/api/mappings/status', methods=['POST'])
def create_status_mapping():
    """Create a new status mapping"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('status_name'):
            return jsonify({'success': False, 'error': 'Status name is required'}), 400
        
        # Check if status already exists
        existing = StatusMapping.query.filter_by(status_name=data['status_name']).first()
        if existing:
            return jsonify({'success': False, 'error': 'Status already exists'}), 400
        
        # Create new mapping
        mapping = StatusMapping(
            status_name=data['status_name'],
            is_application_received=data.get('is_application_received', 0),
            is_application_processed=data.get('is_application_processed', 0),
            is_application_approved=data.get('is_application_approved', 0),
            is_future=data.get('is_future', 0)
        )
        
        db.session.add(mapping)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Status mapping created successfully',
            'data': mapping.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating status mapping: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mappings_bp.route('/api/mappings/status/<int:mapping_id>', methods=['PUT'])
def update_status_mapping(mapping_id):
    """Update a status mapping"""
    try:
        mapping = StatusMapping.query.get_or_404(mapping_id)
        data = request.get_json()
        
        # Update fields
        if 'status_name' in data:
            mapping.status_name = data['status_name']
        if 'is_application_received' in data:
            mapping.is_application_received = data['is_application_received']
        if 'is_application_processed' in data:
            mapping.is_application_processed = data['is_application_processed']
        if 'is_application_approved' in data:
            mapping.is_application_approved = data['is_application_approved']
        if 'is_future' in data:
            mapping.is_future = data['is_future']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Status mapping updated successfully',
            'data': mapping.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating status mapping: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mappings_bp.route('/api/mappings/status/<int:mapping_id>', methods=['DELETE'])
def delete_status_mapping(mapping_id):
    """Delete a status mapping"""
    try:
        mapping = StatusMapping.query.get_or_404(mapping_id)
        db.session.delete(mapping)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Status mapping deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting status mapping: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mappings_bp.route('/api/mappings/flg-meta', methods=['GET'])
def get_flg_meta_mappings():
    """Get all FLG to Meta name mappings"""
    try:
        mappings = FLGMetaMapping.query.order_by(FLGMetaMapping.flg_name).all()
        return jsonify({
            'success': True,
            'data': [m.to_dict() for m in mappings]
        })
    except Exception as e:
        logger.error(f"Error fetching FLG meta mappings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mappings_bp.route('/api/mappings/flg-meta', methods=['POST'])
def create_flg_meta_mapping():
    """Create a new FLG to Meta name mapping"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('flg_name') or not data.get('meta_name'):
            return jsonify({'success': False, 'error': 'Both FLG name and Meta name are required'}), 400
        
        # Check if FLG name already exists
        existing = FLGMetaMapping.query.filter_by(flg_name=data['flg_name']).first()
        if existing:
            return jsonify({'success': False, 'error': 'FLG name already mapped'}), 400
        
        # Create new mapping
        mapping = FLGMetaMapping(
            flg_name=data['flg_name'],
            meta_name=data['meta_name']
        )
        
        db.session.add(mapping)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'FLG to Meta mapping created successfully',
            'data': mapping.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating FLG meta mapping: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mappings_bp.route('/api/mappings/flg-meta/<int:mapping_id>', methods=['PUT'])
def update_flg_meta_mapping(mapping_id):
    """Update a FLG to Meta name mapping"""
    try:
        mapping = FLGMetaMapping.query.get_or_404(mapping_id)
        data = request.get_json()
        
        # Update fields
        if 'flg_name' in data:
            mapping.flg_name = data['flg_name']
        if 'meta_name' in data:
            mapping.meta_name = data['meta_name']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'FLG to Meta mapping updated successfully',
            'data': mapping.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating FLG meta mapping: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mappings_bp.route('/api/mappings/flg-meta/<int:mapping_id>', methods=['DELETE'])
def delete_flg_meta_mapping(mapping_id):
    """Delete a FLG to Meta name mapping"""
    try:
        mapping = FLGMetaMapping.query.get_or_404(mapping_id)
        db.session.delete(mapping)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'FLG to Meta mapping deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting FLG meta mapping: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mappings_bp.route('/api/mappings/status/initialize', methods=['POST'])
def initialize_status_mappings():
    """Initialize default status mappings"""
    try:
        # Get default mappings
        default_mappings = StatusMapping.get_default_mappings()
        
        created_count = 0
        for mapping_data in default_mappings:
            # Check if already exists
            existing = StatusMapping.query.filter_by(status_name=mapping_data['status_name']).first()
            if not existing:
                mapping = StatusMapping(**mapping_data)
                db.session.add(mapping)
                created_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Initialized {created_count} default status mappings'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing status mappings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500