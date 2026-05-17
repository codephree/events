from uuid import uuid4
from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(255), nullable=False)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationship to User
    creator = db.relationship('User', backref='events_created')

    def __repr__(self):
        return f"<Event {self.name} on {self.date}>"