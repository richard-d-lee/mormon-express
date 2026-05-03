"""
Recommendation Engine for Mormon Express
Analyzes conversation history to suggest relevant characters for daily chats
"""

import json
from datetime import datetime, date
from .characters import CHARACTERS, get_character_topics

# Topic keywords that might appear in conversations
TOPIC_KEYWORDS = {
    "faith": ["faith", "believe", "believing", "trust", "trusting", "hope", "confidence"],
    "repentance": ["repent", "repentance", "sin", "sins", "sorry", "forgive", "mistake", "mistakes", "wrong"],
    "forgiveness": ["forgive", "forgiveness", "forgiving", "forgave", "grudge", "anger", "hurt"],
    "trials": ["trial", "trials", "hard", "difficult", "struggle", "struggling", "suffering", "pain", "challenge"],
    "family": ["family", "mother", "father", "parent", "parents", "child", "children", "son", "daughter", "brother", "sister", "spouse", "husband", "wife", "marriage"],
    "prayer": ["pray", "prayer", "prayers", "praying", "ask god", "talk to god"],
    "scripture study": ["scripture", "scriptures", "read", "reading", "study", "studying", "bible", "book of mormon"],
    "testimony": ["testimony", "know", "believe", "witness", "spiritual", "spirit"],
    "service": ["serve", "service", "serving", "help", "helping", "others", "neighbor"],
    "missionary work": ["missionary", "mission", "share", "sharing", "gospel", "teach", "teaching"],
    "conversion": ["convert", "converted", "conversion", "change", "changed", "transform", "transformation"],
    "doubt": ["doubt", "doubts", "doubting", "question", "questions", "uncertain", "unsure", "confused"],
    "courage": ["courage", "brave", "bravery", "courageous", "bold", "boldness", "fear", "afraid"],
    "leadership": ["lead", "leader", "leading", "leadership", "guide", "directing", "responsible"],
    "humility": ["humble", "humility", "meek", "meekness", "pride", "prideful", "ego"],
    "patience": ["patience", "patient", "waiting", "wait", "endure", "endurance", "persevere"],
    "love": ["love", "loving", "compassion", "caring", "care", "kindness", "kind"],
    "obedience": ["obey", "obedience", "obedient", "commandments", "follow", "following"],
    "temple": ["temple", "ordinance", "ordinances", "endowment", "sealing", "eternal"],
    "priesthood": ["priesthood", "keys", "authority", "blessing", "blessings", "ordain"],
    "Holy Ghost": ["spirit", "holy ghost", "inspiration", "inspired", "revelation", "guidance"],
    "atonement": ["atonement", "atone", "redeem", "redemption", "savior", "jesus", "christ", "cross"],
    "covenants": ["covenant", "covenants", "promise", "promises", "baptism", "sacrament"],
    "resurrection": ["resurrection", "resurrect", "risen", "rise", "death", "die", "dying", "afterlife", "eternal life"],
    "suffering": ["suffer", "suffering", "pain", "painful", "hurt", "hurting", "grief", "grieve", "grieving", "loss", "lost"],
    "prophecy": ["prophecy", "prophesy", "prophet", "prophets", "vision", "visions", "future"],
    "motherhood": ["mother", "motherhood", "mom", "mama", "nurture", "nurturing", "children"],
    "gratitude": ["grateful", "gratitude", "thankful", "thanks", "thanksgiving", "appreciate", "appreciation"],
    "work": ["work", "working", "labor", "laboring", "diligent", "effort", "strive"],
    "integrity": ["integrity", "honest", "honesty", "truthful", "truth", "character", "moral"]
}

def extract_topics_from_messages(messages_json):
    """Extract likely discussion topics from conversation messages"""
    try:
        messages = json.loads(messages_json) if isinstance(messages_json, str) else messages_json
    except:
        return []

    found_topics = set()
    all_text = " ".join([
        msg.get("content", "").lower()
        for msg in messages
        if msg.get("sender") == "user"
    ])

    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword in all_text:
                found_topics.add(topic)
                break

    return list(found_topics)


def get_recommendation_for_user(user_conversations, last_character=None):
    """
    Generate a character recommendation based on conversation history

    Args:
        user_conversations: List of Conversation objects
        last_character: The last character the user talked to (to avoid repeating)

    Returns:
        dict with recommended_character and reason
    """
    if not user_conversations:
        # New user - recommend Nephi as a great starting point
        return {
            "character": "nephi",
            "reason": "Nephi is a wonderful place to start. His faith and optimism will inspire your journey through the scriptures."
        }

    # Collect all topics discussed across conversations
    all_topics = []
    characters_talked_to = set()

    for conv in user_conversations:
        characters_talked_to.add(conv.character_id)
        if conv.topics_discussed:
            try:
                topics = json.loads(conv.topics_discussed)
                all_topics.extend(topics)
            except:
                pass
        # Also extract from messages
        all_topics.extend(extract_topics_from_messages(conv.messages))

    # Count topic frequency
    topic_counts = {}
    for topic in all_topics:
        topic_counts[topic] = topic_counts.get(topic, 0) + 1

    # Find characters that match top topics but haven't been talked to recently
    character_topics = get_character_topics()
    character_scores = {}

    for topic, count in topic_counts.items():
        if topic in character_topics:
            for char_id in character_topics[topic]:
                if char_id not in character_scores:
                    character_scores[char_id] = 0
                character_scores[char_id] += count

    # Sort by score
    sorted_chars = sorted(character_scores.items(), key=lambda x: x[1], reverse=True)

    # Prefer characters not recently talked to
    for char_id, score in sorted_chars:
        if char_id != last_character and char_id not in list(characters_talked_to)[-3:]:
            char = CHARACTERS.get(char_id)
            if char:
                # Generate a reason based on matching topics
                matching_topics = [t for t in char.get("topics", []) if t in topic_counts]
                if matching_topics:
                    reason = f"Based on your recent conversations about {matching_topics[0]}, {char['name']} has wisdom to share from their experience with {', '.join(matching_topics[:2])}."
                else:
                    reason = f"{char['name']} offers a unique perspective that could enrich your spiritual journey."
                return {
                    "character": char_id,
                    "reason": reason
                }

    # If all high-scoring characters have been talked to recently, suggest a new one
    untried = [c for c in CHARACTERS.keys() if c not in characters_talked_to]
    if untried:
        char = CHARACTERS.get(untried[0])
        return {
            "character": untried[0],
            "reason": f"You haven't yet spoken with {char['name']}. Their story of {char.get('description', 'faith')} might offer fresh insights for your journey."
        }

    # Fallback: recommend someone based on most discussed topic
    if sorted_chars:
        char_id = sorted_chars[0][0]
        char = CHARACTERS.get(char_id)
        return {
            "character": char_id,
            "reason": f"Your conversations suggest you'd benefit from more time with {char['name']}, who deeply understands the topics you've been exploring."
        }

    # Ultimate fallback
    return {
        "character": "nephi",
        "reason": "Nephi's faith and determination make him a wonderful companion for any stage of your spiritual journey."
    }


def update_conversation_topics(conversation, user_message):
    """Update the topics discussed in a conversation based on a new message"""
    existing_topics = []
    try:
        existing_topics = json.loads(conversation.topics_discussed) if conversation.topics_discussed else []
    except:
        existing_topics = []

    # Extract topics from the new message
    message_lower = user_message.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if topic not in existing_topics:
            for keyword in keywords:
                if keyword in message_lower:
                    existing_topics.append(topic)
                    break

    conversation.topics_discussed = json.dumps(existing_topics[:20])  # Limit to 20 topics
    return existing_topics
