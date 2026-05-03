from . import db
from datetime import datetime
import hashlib

class UserLocation(db.Model):
    __tablename__ = 'user_locations'

    id = db.Column(db.Integer, primary_key=True)
    ip_hash = db.Column(db.String(64), unique=True, nullable=False)
    country = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    visit_count = db.Column(db.Integer, default=1)

    @staticmethod
    def hash_ip(ip_address):
        return hashlib.sha256(ip_address.encode()).hexdigest()

    def to_dict(self):
        return {
            'id': self.id,
            'country': self.country,
            'region': self.region,
            'city': self.city,
            'latitude': round(self.latitude, 2) if self.latitude else None,
            'longitude': round(self.longitude, 2) if self.longitude else None,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'visit_count': self.visit_count
        }
