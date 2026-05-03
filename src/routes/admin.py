from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func

from src.models import db, ChatLog, UserLocation, User

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/logs', methods=['GET'])
def get_logs():
    """Get chat logs with optional filtering"""
    period = request.args.get('period', 'week')
    limit = request.args.get('limit', 100, type=int)
    character = request.args.get('character')

    query = ChatLog.query

    if period == 'week':
        cutoff = datetime.utcnow() - timedelta(days=7)
        query = query.filter(ChatLog.created_at >= cutoff)
    elif period == 'day':
        cutoff = datetime.utcnow() - timedelta(days=1)
        query = query.filter(ChatLog.created_at >= cutoff)

    if character:
        query = query.filter(ChatLog.character_id == character)

    logs = query.order_by(ChatLog.created_at.desc()).limit(limit).all()

    return jsonify({
        'logs': [log.to_dict() for log in logs],
        'count': len(logs)
    }), 200


@admin_bp.route('/logs/stats', methods=['GET'])
def get_stats():
    """Get chat statistics"""
    week_ago = datetime.utcnow() - timedelta(days=7)

    # Total chats this week
    total_chats = ChatLog.query.filter(ChatLog.created_at >= week_ago).count()

    # Scripture mode usage
    scripture_chats = ChatLog.query.filter(
        ChatLog.created_at >= week_ago,
        ChatLog.scripture_mode == True
    ).count()

    # Chats by character
    chats_by_character = db.session.query(
        ChatLog.character_id,
        func.count(ChatLog.id)
    ).filter(
        ChatLog.created_at >= week_ago
    ).group_by(ChatLog.character_id).all()

    # Chats by country
    chats_by_country = db.session.query(
        ChatLog.country,
        func.count(ChatLog.id)
    ).filter(
        ChatLog.created_at >= week_ago
    ).group_by(ChatLog.country).order_by(func.count(ChatLog.id).desc()).limit(10).all()

    # Response source breakdown
    source_breakdown = db.session.query(
        ChatLog.response_source,
        func.count(ChatLog.id)
    ).filter(
        ChatLog.created_at >= week_ago
    ).group_by(ChatLog.response_source).all()

    # User stats
    total_users = User.query.count()
    active_users = User.query.filter(User.last_login >= week_ago).count()

    return jsonify({
        'total_chats_week': total_chats,
        'scripture_mode_usage': scripture_chats,
        'chats_by_character': dict(chats_by_character),
        'chats_by_country': dict(chats_by_country),
        'response_sources': dict(source_breakdown),
        'total_users': total_users,
        'active_users_week': active_users
    }), 200


@admin_bp.route('/logs/cleanup', methods=['POST'])
def cleanup_logs():
    """Manually cleanup old logs"""
    try:
        cutoff = datetime.utcnow() - timedelta(days=7)
        deleted = ChatLog.query.filter(ChatLog.created_at < cutoff).delete()
        db.session.commit()
        return jsonify({
            'message': f'Deleted {deleted} old logs',
            'deleted_count': deleted
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/locations', methods=['GET'])
def get_locations():
    """Get user location data for mapping"""
    locations = UserLocation.query.all()

    return jsonify({
        'locations': [loc.to_dict() for loc in locations],
        'count': len(locations)
    }), 200


@admin_bp.route('/locations/stats', methods=['GET'])
def get_location_stats():
    """Get location statistics"""
    total_locations = UserLocation.query.count()
    total_visits = db.session.query(func.sum(UserLocation.visit_count)).scalar() or 0

    by_country = db.session.query(
        UserLocation.country,
        func.count(UserLocation.id),
        func.sum(UserLocation.visit_count)
    ).group_by(UserLocation.country).order_by(func.sum(UserLocation.visit_count).desc()).limit(20).all()

    countries = [
        {
            'country': country,
            'unique_visitors': count,
            'total_visits': visits or 0
        }
        for country, count, visits in by_country
    ]

    return jsonify({
        'total_unique_locations': total_locations,
        'total_visits': total_visits,
        'by_country': countries
    }), 200
