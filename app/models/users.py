from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from uuid import uuid4


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    # id = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(80), nullable=True)
    status = db.Column(db.String(80), default='active')

    def __repr__(self):
        return f"<User {self.username}>"

    @classmethod
    def create_default_admin(cls):
        if cls.query.count() == 0:
            admin = cls(name='superadmin', username='admin', password=generate_password_hash('password'))
            db.session.add(admin)
            db.session.commit()