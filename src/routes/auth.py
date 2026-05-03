from flask import Blueprint, request, jsonify, session
from datetime import datetime, date
from src.models import db, User, Conversation, DailyRecommendation
from src.utils import get_recommendation_for_user

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required'}), 400

    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    if '@' not in email:
        return jsonify({'error': 'Invalid email address'}), 400

    # Check if user exists
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        if existing_user.username == username:
            return jsonify({'error': 'Username already taken'}), 409
        else:
            return jsonify({'error': 'Email already registered'}), 409

    try:
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        print(f"[LOG] New user registered: {username}")

        return jsonify({
            'message': 'Registration successful',
            'user': user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Registration failed: {e}")
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login an existing user"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    identifier = data.get('username', '').strip()  # Can be username or email
    password = data.get('password', '')

    if not identifier or not password:
        return jsonify({'error': 'Username/email and password are required'}), 400

    # Find user by username or email
    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier.lower())
    ).first()

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Update last login and check if it's a new day
    today = date.today()
    is_new_day = user.last_active_date != today

    user.last_login = datetime.utcnow()
    user.last_active_date = today

    # Generate daily recommendation if it's a new day
    recommendation = None
    if is_new_day:
        # Get user's conversations for recommendation
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
        recommendation = rec_data

    db.session.commit()

    session['user_id'] = user.id
    print(f"[LOG] User logged in: {user.username}")

    response_data = {
        'message': 'Login successful',
        'user': user.to_dict(),
        'is_new_day': is_new_day
    }

    if recommendation:
        response_data['recommendation'] = recommendation

    return jsonify(response_data), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout the current user"""
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/check-auth', methods=['GET'])
def check_auth():
    """Check if user is authenticated and get recommendation if new day"""
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'authenticated': False}), 200

    user = User.query.get(user_id)

    if not user:
        session.pop('user_id', None)
        return jsonify({'authenticated': False}), 200

    # Check if it's a new day
    today = date.today()
    is_new_day = user.last_active_date != today

    recommendation = None
    if is_new_day:
        user.last_active_date = today

        # Get or create daily recommendation
        existing_rec = DailyRecommendation.query.filter_by(
            user_id=user.id,
            date=today
        ).first()

        if existing_rec:
            recommendation = {
                'character': existing_rec.recommended_character,
                'reason': existing_rec.reason
            }
        else:
            conversations = Conversation.query.filter_by(user_id=user.id).all()
            last_conv = Conversation.query.filter_by(user_id=user.id).order_by(
                Conversation.updated_at.desc()
            ).first()
            last_char = last_conv.character_id if last_conv else None

            rec_data = get_recommendation_for_user(conversations, last_char)

            daily_rec = DailyRecommendation(
                user_id=user.id,
                date=today,
                recommended_character=rec_data['character'],
                reason=rec_data['reason']
            )
            db.session.add(daily_rec)
            recommendation = rec_data

        db.session.commit()

    response_data = {
        'authenticated': True,
        'user': user.to_dict(),
        'is_new_day': is_new_day
    }

    if recommendation:
        response_data['recommendation'] = recommendation

    return jsonify(response_data), 200
