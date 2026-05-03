from flask import Blueprint, request, jsonify, session
import anthropic
import os
import json
from datetime import datetime

from src.models import db, ChatLog, UserLocation, User, Conversation
from src.utils import (
    get_client_ip, get_location_from_ip,
    get_character, update_conversation_topics
)

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

# Initialize Anthropic client
client = None
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

def init_anthropic_client():
    """Initialize Anthropic client with proper error handling"""
    global client
    if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != 'your_anthropic_api_key_here':
        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            print("[LOG] Anthropic client initialized")
        except Exception as e:
            print(f"[WARNING] Failed to initialize Anthropic client: {e}")
            client = None
    else:
        print("[WARNING] ANTHROPIC_API_KEY not set - using fallback responses")

# Defer initialization to avoid import-time errors
init_anthropic_client()

# Scripture references for characters
SCRIPTURE_REFERENCES = {
    "book_of_mormon": [
        ("1 Nephi 3:7", "I will go and do the things which the Lord hath commanded, for I know that the Lord giveth no commandments unto the children of men, save he shall prepare a way for them that they may accomplish the thing which he commandeth them."),
        ("2 Nephi 25:26", "And we talk of Christ, we rejoice in Christ, we preach of Christ, we prophesy of Christ, and we write according to our prophecies, that our children may know to what source they may look for a remission of their sins."),
        ("Alma 32:21", "Faith is not to have a perfect knowledge of things; therefore if ye have faith ye hope for things which are not seen, which are true."),
        ("Moroni 10:4-5", "And when ye shall receive these things, I would exhort you that ye would ask God, the Eternal Father, in the name of Christ, if these things are not true; and if ye shall ask with a sincere heart, with real intent, having faith in Christ, he will manifest the truth of it unto you, by the power of the Holy Ghost."),
        ("Mosiah 2:17", "When ye are in the service of your fellow beings ye are only in the service of your God."),
        ("Ether 12:27", "If men come unto me I will show unto them their weakness. I give unto men weakness that they may be humble; and my grace is sufficient for all men that humble themselves before me."),
        ("3 Nephi 11:10-11", "Behold, I am Jesus Christ, whom the prophets testified shall come into the world. I am the light and the life of the world."),
        ("Alma 7:11-12", "He shall go forth, suffering pains and afflictions and temptations of every kind; that the word might be fulfilled which saith he will take upon him the pains and the sicknesses of his people."),
    ],
    "old_testament": [
        ("Isaiah 53:5", "But he was wounded for our transgressions, he was bruised for our iniquities: the chastisement of our peace was upon him; and with his stripes we are healed."),
        ("Proverbs 3:5-6", "Trust in the Lord with all thine heart; and lean not unto thine own understanding. In all thy ways acknowledge him, and he shall direct thy paths."),
        ("Isaiah 40:31", "But they that wait upon the Lord shall renew their strength; they shall mount up with wings as eagles; they shall run, and not be weary; and they shall walk, and not faint."),
        ("Psalm 23:4", "Yea, though I walk through the valley of the shadow of death, I will fear no evil: for thou art with me; thy rod and thy staff they comfort me."),
        ("Jeremiah 29:11", "For I know the thoughts that I think toward you, saith the Lord, thoughts of peace, and not of evil, to give you an expected end."),
        ("Joshua 1:9", "Have not I commanded thee? Be strong and of a good courage; be not afraid, neither be thou dismayed: for the Lord thy God is with thee whithersoever thou goest."),
        ("Micah 6:8", "He hath shewed thee, O man, what is good; and what doth the Lord require of thee, but to do justly, and to love mercy, and to walk humbly with thy God?"),
    ],
    "new_testament": [
        ("John 3:16", "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life."),
        ("Matthew 11:28-30", "Come unto me, all ye that labour and are heavy laden, and I will give you rest. Take my yoke upon you, and learn of me; for I am meek and lowly in heart: and ye shall find rest unto your souls."),
        ("Philippians 4:13", "I can do all things through Christ which strengtheneth me."),
        ("Romans 8:28", "And we know that all things work together for good to them that love God, to them who are the called according to his purpose."),
        ("Hebrews 11:1", "Now faith is the substance of things hoped for, the evidence of things not seen."),
        ("James 1:5", "If any of you lack wisdom, let him ask of God, that giveth to all men liberally, and upbraideth not; and it shall be given him."),
        ("1 John 4:18", "There is no fear in love; but perfect love casteth out fear."),
        ("2 Timothy 1:7", "For God hath not given us the spirit of fear; but of power, and of love, and of a sound mind."),
    ]
}

def get_fallback_response(character_id):
    """Generate a fallback response if API fails"""
    character = get_character(character_id)
    if not character:
        return "I am here to help you on your spiritual journey. Please share what's on your heart."

    fallbacks = {
        "nephi": "My friend, I have learned through many trials that the Lord prepares a way for those who trust in Him. Though I cannot fully answer now, know that God loves you and has a purpose for your struggles. As I once said, 'I will go and do the things which the Lord hath commanded.'",
        "alma_younger": "I understand struggle, for I once walked in darkness before finding the light of Christ. Whatever you're facing, know that the Atonement of Jesus Christ is real and can transform you, as it transformed me. Cry unto God for mercy, and He will hear you.",
        "moroni_captain": "Stand firm in your cause, whatever righteous battle you face. Remember the Title of Liberty - we fight for God, our religion, our freedom, and our families. Take courage and do not shrink from defending what is right.",
        "default": "I am here to offer what wisdom I can. Though my connection is limited at this moment, know that God is always available to you through prayer. Seek Him with real intent, and He will answer."
    }

    return fallbacks.get(character_id, fallbacks["default"])


def get_scripture_for_section(section):
    """Get a random scripture reference for the character's section"""
    import random
    scriptures = SCRIPTURE_REFERENCES.get(section, SCRIPTURE_REFERENCES["book_of_mormon"])
    ref, text = random.choice(scriptures)
    return f'\n\n"{text}" - {ref}'


@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    message = data.get('message', '').strip()
    character_id = data.get('character_id', 'nephi')
    scripture_mode = data.get('scripture_mode', False)
    scripture_source = data.get('scripture_source', 'all')
    conversation_history = data.get('conversation_history', [])

    if not message:
        return jsonify({'error': 'Message is required'}), 400

    character = get_character(character_id)
    if not character:
        return jsonify({'error': 'Invalid character'}), 400

    # Get user info if authenticated
    user_id = session.get('user_id')

    # Build system prompt
    system_prompt = character['system_prompt']

    if scripture_mode:
        scripture_instruction = "\n\nIMPORTANT: Include relevant scripture references in your responses. "
        if scripture_source == 'book_of_mormon':
            scripture_instruction += "Focus on Book of Mormon scriptures."
        elif scripture_source == 'bible':
            scripture_instruction += "Focus on Bible scriptures (Old and New Testament)."
        elif scripture_source == 'all':
            scripture_instruction += "Draw from the Bible, Book of Mormon, Doctrine and Covenants, and Pearl of Great Price as appropriate."
        system_prompt += scripture_instruction

    # Build messages for API
    messages = []

    # Add conversation history (limit to last 20 messages)
    for hist_msg in conversation_history[-20:]:
        role = "user" if hist_msg.get('sender') == 'user' else "assistant"
        messages.append({
            "role": role,
            "content": hist_msg.get('content', '')
        })

    # Add current message
    messages.append({
        "role": "user",
        "content": message
    })

    # Try to get response from Anthropic
    response_text = None
    response_source = 'anthropic'

    if client:
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                system=system_prompt,
                messages=messages
            )
            response_text = response.content[0].text

            # Add scripture if in scripture mode and not already included
            if scripture_mode and not any(ref in response_text for ref in ['Nephi', 'Alma', 'Moroni', 'Matthew', 'John', 'Isaiah', 'Psalm']):
                response_text += get_scripture_for_section(character['section'])

        except Exception as e:
            print(f"[ERROR] Anthropic API error: {e}")
            response_text = get_fallback_response(character_id)
            response_source = 'fallback'
            if scripture_mode:
                response_text += get_scripture_for_section(character['section'])
    else:
        response_text = get_fallback_response(character_id)
        response_source = 'fallback'
        if scripture_mode:
            response_text += get_scripture_for_section(character['section'])

    # Log the chat
    try:
        ip_address = get_client_ip(request)
        location = get_location_from_ip(ip_address)

        chat_log = ChatLog(
            user_id=user_id,
            character_id=character_id,
            user_message=message[:5000],  # Limit message length
            bot_response=response_text[:10000],  # Limit response length
            scripture_mode=scripture_mode,
            scripture_source=scripture_source,
            ip_address=ip_address,
            country=location.get('country'),
            region=location.get('region'),
            city=location.get('city'),
            latitude=location.get('lat'),
            longitude=location.get('lon'),
            response_source=response_source
        )
        db.session.add(chat_log)

        # Update user location tracking
        ip_hash = UserLocation.hash_ip(ip_address)
        user_location = UserLocation.query.filter_by(ip_hash=ip_hash).first()

        if user_location:
            user_location.last_seen = datetime.utcnow()
            user_location.visit_count += 1
        else:
            user_location = UserLocation(
                ip_hash=ip_hash,
                country=location.get('country'),
                region=location.get('region'),
                city=location.get('city'),
                latitude=round(location.get('lat', 0), 2),
                longitude=round(location.get('lon', 0), 2)
            )
            db.session.add(user_location)

        # Update conversation if user is authenticated
        if user_id:
            conversation = Conversation.query.filter_by(
                user_id=user_id,
                character_id=character_id
            ).first()

            if conversation:
                # Update existing conversation
                try:
                    msgs = json.loads(conversation.messages)
                except:
                    msgs = []

                msgs.append({'sender': 'user', 'content': message, 'timestamp': datetime.utcnow().isoformat()})
                msgs.append({'sender': 'character', 'content': response_text, 'timestamp': datetime.utcnow().isoformat()})

                # Keep only last 100 messages
                conversation.messages = json.dumps(msgs[-100:])
                conversation.message_count = len(msgs)
                conversation.updated_at = datetime.utcnow()

                # Update topics
                update_conversation_topics(conversation, message)
            else:
                # Create new conversation
                msgs = [
                    {'sender': 'user', 'content': message, 'timestamp': datetime.utcnow().isoformat()},
                    {'sender': 'character', 'content': response_text, 'timestamp': datetime.utcnow().isoformat()}
                ]
                conversation = Conversation(
                    user_id=user_id,
                    character_id=character_id,
                    messages=json.dumps(msgs),
                    message_count=2,
                    topics_discussed='[]'
                )
                update_conversation_topics(conversation, message)
                db.session.add(conversation)

        db.session.commit()

    except Exception as e:
        print(f"[ERROR] Failed to log chat: {e}")
        db.session.rollback()

    return jsonify({
        'response': response_text,
        'character_id': character_id,
        'character_name': character['name'],
        'source': response_source
    }), 200


@chatbot_bp.route('/characters', methods=['GET'])
def get_characters():
    """Get all available characters organized by section"""
    from src.utils import get_all_sections
    return jsonify(get_all_sections()), 200


@chatbot_bp.route('/character/<character_id>', methods=['GET'])
def get_character_info(character_id):
    """Get information about a specific character"""
    character = get_character(character_id)
    if not character:
        return jsonify({'error': 'Character not found'}), 404

    # Don't expose the full system prompt
    safe_character = {
        'id': character['id'],
        'name': character['name'],
        'section': character['section'],
        'title': character['title'],
        'era': character['era'],
        'image': character['image'],
        'color': character['color'],
        'description': character['description'],
        'initial_message': character['initial_message'],
        'topics': character.get('topics', [])
    }

    return jsonify(safe_character), 200
