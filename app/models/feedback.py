from uuid import uuid4

from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    event_id = db.Column(db.String(36), db.ForeignKey('events.id'), nullable=False)
    attendee_id = db.Column(db.String(36), db.ForeignKey('attendees.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    event = db.relationship('Event', backref=db.backref('feedback', lazy=True))
    attendee = db.relationship('Attendee', backref=db.backref('feedback', lazy=True))

    def __repr__(self):
        return f"<Feedback Attendee {self.attendee_id} for Event {self.event_id} - Rating: {self.rating}>"