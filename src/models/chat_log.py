from . import db
from datetime import datetime

class ChatLog(db.Model):
    __tablename__ = 'chat_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    character_id = db.Column(db.String(50), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    scripture_mode = db.Column(db.Boolean, default=False)
    scripture_source = db.Column(db.String(50), default='all')
    ip_address = db.Column(db.String(45), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    response_source = db.Column(db.String(20), default='anthropic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'character_id': self.character_id,
            'user_message': self.user_message,
            'bot_response': self.bot_response,
            'scripture_mode': self.scripture_mode,
            'scripture_source': self.scripture_source,
            'country': self.country,
            'city': self.city,
            'response_source': self.response_source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
