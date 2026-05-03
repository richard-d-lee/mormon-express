from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User, Conversation, DailyRecommendation
from .chat_log import ChatLog
from .user_location import UserLocation
