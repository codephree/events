from . import staff_bp
from flask import request,jsonify, render_template, redirect, url_for
from app.models.users import User
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash
from app.extensions import db

@staff_bp.route('/')
@login_required
def staff_dashboard():
    users = User.query \
              .where(User.id != current_user.id) \
              .all()
    return render_template('staffs/index.html',users=users)

@staff_bp.route('/create', methods=['GET','POST'])
@login_required
def create_user():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']

        user = User(name=name, username=username, role='Event Manager', password=generate_password_hash('password'))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('staff.staff_dashboard'))
    return render_template('staffs/create.html')


@staff_bp.route('/<id>', methods=['GET'])
@login_required
def get_user(id):
    user = User.query.filter_by(id=id).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    return jsonify({
        'success': True,
        'user': {
            # 'id': user.id,
            'name': user.name,
            'username': user.username,
            'role': user.role,
            'status': user.status
        }
    })

@staff_bp.route('/<id>/update', methods=['POST'])
@login_required
def update_user(id):
    user = User.query.filter_by(id=id).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    data = request.get_json(silent=True) or request.form
    name = data.get('name', '').strip()
    username = data.get('username', '').strip()
    status = data.get('status', '').strip()

    if not name or not username or not status:
        return jsonify({'success': False, 'message': 'Name, username, and status are required.'}), 400

    duplicate = User.query.filter(User.username == username, User.id != user.id).first()
    if duplicate:
        return jsonify({'success': False, 'message': 'That username is already taken.'}), 400

    try:
        user.name = name
        user.username = username
        user.status = status
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'User updated successfully.',
            'user': {
                # 'id': user.id,
                'name': user.name,
                'username': user.username,
                'role': user.role,
                'status': user.status
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@staff_bp.route('/<id>/remove', methods=['POST'])
@login_required
def remove_user(id):
    if request.method == 'POST':
        payload = request.get_json(silent=True) or request.form
        user_id = payload.get('user')
        user = User.query.where(User.id == id).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            return jsonify({'message': 'User Deleted Successful','success': True}), 200
        else:
            return jsonify({ 'message': 'User Not Found', 'success': False }), 404
    return jsonify({ 'message': 'Page not found', 'success': False }), 405
   