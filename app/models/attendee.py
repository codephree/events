from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from uuid import uuid4


    
class Attendee(db.Model):
    __tablename__ = 'attendees'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    attendee_id = db.Column(db.String(255), unique=True, nullable=False) 
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    

    def __repr__(self):
        return f"<Attendee {self.name} ({self.email})>"