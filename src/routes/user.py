from flask import Blueprint, request, jsonify, session
import json
from datetime import datetime, date

from src.models import db, User, Conversation, DailyRecommendation
from src.utils import get_character, get_recommendation_for_user

user_bp = Blueprint('user', __name__, url_prefix='/api/user')


def require_auth(f):
    """Decorator to require authentication"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        user = User.query.get(user_id)
        if not user:
            session.pop('user_id', None)
            return jsonify({'error': 'User not found'}), 401
        return f(user, *args, **kwargs)
    return decorated


@user_bp.route('/conversations', methods=['GET'])
@require_auth
def get_conversations(user):
    """Get all conversations for the authenticated user"""
    conversations = Conversation.query.filter_by(user_id=user.id).order_by(
        Conversation.updated_at.desc()
    ).all()

    result = []
    for conv in conversations:
        character = get_character(conv.character_id)
        result.append({
            'id': conv.id,
            'character_id': conv.character_id,
            'character_name': character['name'] if character else conv.character_id,
            'character_title': character['title'] if character else '',
            'character_section': character['section'] if character else '',
            'message_count': conv.message_count,
            'updated_at': conv.updated_at.isoformat() if conv.updated_at else None
        })

    return jsonify({'conversations': result}), 200


@user_bp.route('/conversation/<character_id>', methods=['GET'])
@require_auth
def get_conversation(user, character_id):
    """Get a specific conversation with a character"""
    character = get_character(character_id)
    if not character:
        return jsonify({'error': 'Character not found'}), 404

    conversation = Conversation.query.filter_by(
        user_id=user.id,
        character_id=character_id
    ).first()

    if not conversation:
        return jsonify({
            'character_id': character_id,
            'messages': [],
            'initial_message': character['initial_message']
        }), 200

    try:
        messages = json.loads(conversation.messages)
    except:
        messages = []

    return jsonify({
        'character_id': character_id,
        'messages': messages,
        'message_count': conversation.message_count,
        'initial_message': character['initial_message'],
        'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None
    }), 200


@user_bp.route('/conversation/<character_id>', methods=['DELETE'])
@require_auth
def delete_conversation(user, character_id):
    """Delete a conversation with a character"""
    conversation = Conversation.query.filter_by(
        user_id=user.id,
        character_id=character_id
    ).first()

    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404

    try:
        db.session.delete(conversation)
        db.session.commit()
        return jsonify({'message': 'Conversation deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete conversation'}), 500


@user_bp.route('/recommendation', methods=['GET'])
@require_auth
def get_daily_recommendation(user):
    """Get today's character recommendation"""
    today = date.today()

    # Check for existing recommendation
    existing_rec = DailyRecommendation.query.filter_by(
        user_id=user.id,
        date=today
    ).first()

    if existing_rec:
        character = get_character(existing_rec.recommended_character)
        return jsonify({
            'character_id': existing_rec.recommended_character,
            'character_name': character['name'] if character else existing_rec.recommended_character,
            'reason': existing_rec.reason,
            'was_followed': existing_rec.was_followed
        }), 200

    # Generate new recommendation
    conversations = Conversation.query.filter_by(user_id=user.id).all()
    last_conv = Conversation.query.filter_by(user_id=user.id).order_by(
        Conversation.updated_at.desc()
    ).first()
    last_char = last_conv.character_id if last_conv else None

    rec_data = get_recommendation_for_user(conversations, last_char)

    # Save recommendation
    daily_rec = DailyRecommendation(
        user_id=user.id,
        date=today,
        recommended_character=rec_data['character'],
        reason=rec_data['reason']
    )
    db.session.add(daily_rec)
    db.session.commit()

    character = get_character(rec_data['character'])
    return jsonify({
        'character_id': rec_data['character'],
        'character_name': character['name'] if character else rec_data['character'],
        'reason': rec_data['reason'],
        'was_followed': False
    }), 200


@user_bp.route('/recommendation/follow', methods=['POST'])
@require_auth
def follow_recommendation(user):
    """Mark that the user followed today's recommendation"""
    today = date.today()

    rec = DailyRecommendation.query.filter_by(
        user_id=user.id,
        date=today
    ).first()

    if rec:
        rec.was_followed = True
        db.session.commit()

    return jsonify({'message': 'Recommendation marked as followed'}), 200


@user_bp.route('/stats', methods=['GET'])
@require_auth
def get_user_stats(user):
    """Get statistics about the user's conversations"""
    conversations = Conversation.query.filter_by(user_id=user.id).all()

    total_messages = sum(conv.message_count for conv in conversations)
    characters_talked_to = len(conversations)

    # Get topics from all conversations
    all_topics = []
    for conv in conversations:
        try:
            topics = json.loads(conv.topics_discussed) if conv.topics_discussed else []
            all_topics.extend(topics)
        except:
            pass

    # Count topic frequency
    topic_counts = {}
    for topic in all_topics:
        topic_counts[topic] = topic_counts.get(topic, 0) + 1

    top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Get section breakdown
    section_counts = {'book_of_mormon': 0, 'old_testament': 0, 'new_testament': 0}
    for conv in conversations:
        character = get_character(conv.character_id)
        if character:
            section_counts[character['section']] = section_counts.get(character['section'], 0) + conv.message_count

    return jsonify({
        'total_messages': total_messages,
        'characters_talked_to': characters_talked_to,
        'top_topics': top_topics,
        'section_breakdown': section_counts,
        'member_since': user.created_at.isoformat() if user.created_at else None
    }), 200


@user_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile(user):
    """Get user profile information"""
    return jsonify({
        'user': user.to_dict()
    }), 200


@user_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile(user):
    """Update user profile"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Update email if provided
    if 'email' in data:
        new_email = data['email'].strip().lower()
        if new_email and '@' in new_email:
            # Check if email is already taken
            existing = User.query.filter(
                User.email == new_email,
                User.id != user.id
            ).first()
            if existing:
                return jsonify({'error': 'Email already in use'}), 409
            user.email = new_email

    # Update password if provided
    if 'new_password' in data:
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')

        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401

        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters'}), 400

        user.set_password(new_password)

    try:
        db.session.commit()
        return jsonify({
            'message': 'Profile updated',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile'}), 500
