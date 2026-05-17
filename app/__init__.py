from flask import Flask, jsonify, render_template
from app.extensions import db, login_manager, jwt
from flask_login import login_required
from config import Config
import sys


sys.dont_write_bytecode = True

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)
    from app.routes.auth import auth_bp
    from app.routes.events import events_bp
    from app.routes.staff import staff_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp, url_prefix='/events') 
    app.register_blueprint(staff_bp, url_prefix='/staffs')
    app.register_blueprint(api_bp, url_prefix='/api')


    @app.route('/')
    @login_required
    def index():
        return render_template('dashboard.html')
        # return jsonify({'message': 'Welcome to the CP Event Management API!'})

    # ensure a default admin user exists (demo only)
    @app.before_request
    def ensure_default_user():
        from app.models.users import User
        with app.app_context():
            db.create_all()
            User.create_default_admin()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=10001)
