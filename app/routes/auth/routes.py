from . import auth_bp
from .services import LoginForm
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask import render_template, redirect, url_for, flash, jsonify, request, session, Response
from app.models.users import User
from app.models.events import Event
from app.models.attendee import Attendee
from app.models.registration import Registration
from app import login_manager
from datetime import datetime, date
from app.extensions import db
import io
import csv


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.where(User.username == username) \
                         .where(User.status == 'active') \
                         .first()
        # print(user)     
        if user and check_password_hash(user.password, password):
            login_user(user)
            session.permanent = True  # Make the session permanent to use PERMANENT_SESSION_LIFETIME
            return redirect(url_for('auth.dashboard'))
        flash('Invalid username or password and inactive account', 'danger')
    return render_template('login.html', form=form)


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

#dashboard route is protected with login_required decorator
@auth_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@auth_bp.route('/update-settings', methods=['POST','GET'])
@login_required
def update_settings():
    user = User.query.first_or_404(current_user.id)
    if request.method == 'POST':
       user.name = request.form['name']
       password = request.form['old-password']

       if user and check_password_hash(user.password, password):
            user.password = generate_password_hash(request.form['new-password'])

       db.session.commit()
       return redirect(url_for('auth.update_settings'))
    # print(current_user.id)
    return render_template('staffs/update-settings.html', user=user)

# dashboard data
@auth_bp.route('/dashboard/data')
@login_required
def dashboard_data():
    today = date.today()
    total_events = Event.query.count()
    total_attendees = Attendee.query.count()
    total_registrations = Registration.query.count()
    upcoming_events = Event.query.filter(Event.date >= today).count()
    todays_events = Event.query.filter(Event.date == today).count()

    return jsonify({
        'message': 'Data loaded',
        'success': True,
        'data': {
            'total_events': total_events,
            'total_attendees': total_attendees,
            'total_registrations': total_registrations,
            'upcoming_events': upcoming_events,
            'todays_events': todays_events
        }
    }), 200


@auth_bp.route('/reports')
@login_required
def reports():
    today = date.today()
    metrics = {
        'total_events': Event.query.count(),
        'total_attendees': Attendee.query.count(),
        'total_registrations': Registration.query.count(),
        'upcoming_events': Event.query.filter(Event.date >= today).count(),
        'todays_events': Event.query.filter(Event.date == today).count()
    }
    events = Event.query.order_by(Event.date.desc()).limit(20).all()
    return render_template('reports.html', metrics=metrics, events=events)


@auth_bp.route('/reports/export')
@login_required
def export_report():
    today = date.today()
    total_events = Event.query.count()
    total_attendees = Attendee.query.count()
    total_registrations = Registration.query.count()
    upcoming_events = Event.query.filter(Event.date >= today).count()
    todays_events = Event.query.filter(Event.date == today).count()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Report Type', 'Value'])
    writer.writerow(['Total Events', total_events])
    writer.writerow(['Total Attendees', total_attendees])
    writer.writerow(['Total Registrations', total_registrations])
    writer.writerow(['Upcoming Events', upcoming_events])
    writer.writerow(['Today\'s Events', todays_events])
    writer.writerow([])
    writer.writerow(['Event ID', 'Event Name', 'Date', 'Location', 'Attendee Count'])
    for event in Event.query.order_by(Event.date.asc()).all():
        writer.writerow([event.id, event.name, event.date.isoformat(), event.location, len(event.registrations)])
    writer.writerow([])
    writer.writerow(['Registration ID', 'Event ID', 'Event Name', 'Attendee Name', 'Attendee Email', 'Registered At'])
    for registration in Registration.query.order_by(Registration.id.asc()).limit(500).all():
        writer.writerow([
            registration.id,
            registration.event_id,
            registration.event.name if registration.event else '',
            registration.attendee.name if registration.attendee else '',
            registration.attendee.email if registration.attendee else '',
            registration.created_at.isoformat() if registration.created_at else ''
        ])

    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=attendance-report.csv'
    return response


# load user callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(str(user_id))
    except Exception:
        return None