from flask import render_template, request, url_for, redirect, jsonify
from app.models.attendee import Attendee
from app.models.events import Event
from app.models.registration import Registration
from app.models.users import User
from . import events_bp
from app.extensions import db
import datetime
import csv
import io
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user

@events_bp.route('/', methods=['GET'])
@login_required
def list_events():
    page = request.args.get('page', 1, type=int)
    per_page = 5

    events_query = Event.query\
                        .join(User, Event.created_by == User.id) \
                        .order_by(Event.date.asc())

    events_pagination = events_query.paginate(page=page, per_page=per_page, error_out=False)
    events = events_pagination.items  
    current_time = datetime.datetime.now()

    return render_template('events/index.html', events=events, pagination=events_pagination, current_time=current_time)
  

@events_bp.route('/<string:event_id>', methods=['GET'])
@login_required
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('events/detail.html', event=event)

@events_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_event():
    if request.method == 'POST':
        # Handle form submission to create a new event
        # (This is just a placeholder, you would need to implement the actual logic)
        name = request.form['name']
        date = datetime.datetime.strptime(request.form['date'], '%Y-%m-%dT%H:%M')  # Adjusted to match datetime-local input format
        location = request.form['location']
        description = request.form.get('description', '').strip()
        # print(name, date, location, description)
        # Create the new event (you would need to implement the actual event creation logic)
        event = Event(name=name, date=date, location=location, description=description, created_by=current_user.id)
        db.session.add(event)
        db.session.commit()
        return redirect(url_for('events.list_events'))
    return render_template('events/create.html')

@events_bp.route('/import-attendees', methods=['POST'])
@login_required
def import_attendees():
    try:
        event_id = request.form.get('event_id') or request.json.get('event_id')
        event = Event.query.get_or_404(event_id)
        
        attendees_list = [] 
        
        # Handle CSV file upload
        if 'csv_file' in request.files:
            file = request.files['csv_file']
            if file and file.filename.endswith('.csv'):
                stream = io.StringIO(file.stream.read().decode('utf-8'))
                reader = csv.DictReader(stream)
                for row in reader:
                    attendees_list.append({
                        'name': row.get('name', ''),
                        'email': row.get('email', ''),
                        'attendee_id': row.get('attendee_id', '') if row.get('attendee_id', '') else generate_attendee_id()
                    })
        
        # Handle manual JSON input
        elif request.is_json:
            attendees_list = request.json.get('attendees', [])
        
        if not attendees_list:
            return jsonify({'success': False, 'message': 'No attendees provided'}), 400
        
        # Add attendees to event
        imported_count = 0
        for attendee_data in attendees_list:
            email = attendee_data.get('email', '').strip()
            name = attendee_data.get('name', email).strip()
            attendee_id = attendee_data.get('attendee_id', '').strip() if attendee_data.get('attendee_id', '').strip() else generate_attendee_id()
            
            if not email:
                continue
            
            # Find or create attendee
            attendee = Attendee.query.filter_by(email=email).first()
            if not attendee:
                attendee = Attendee(name=name or email, email=email, attendee_id=attendee_id)
                db.session.add(attendee)
                db.session.flush()
            
            # Check if already registered
            existing_registration = Registration.query.filter_by(
                event_id=event_id, 
                attendee_id=attendee.id
            ).first()
            
            if not existing_registration:
                registration = Registration(event_id=event_id, attendee_id=attendee.id, created_by=current_user.id)
                db.session.add(registration)
                imported_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Successfully imported {imported_count} attendee(s)'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@events_bp.route('/<string:event_id>/update', methods=['POST'])
@login_required
def update_event(event_id):
    event = Event.query.get_or_404(event_id)
    data = request.get_json(silent=True) or request.form
    name = data.get('name', '').strip()
    date_value = data.get('date', '').strip()
    location = data.get('location', '').strip()

    if not name or not date_value or not location:
        return jsonify({'success': False, 'message': 'Name, date, and location are required.'}), 400

    try:
        event.name = name
        event.date = datetime.datetime.strptime(date_value, '%Y-%m-%dT%H:%M')  # Adjusted to match datetime-local input format
        event.location = location
        db.session.commit()
        return jsonify({'success': True, 'message': 'Event updated successfully.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@events_bp.route('/<string:event_id>/attendees', methods=['GET', 'POST'])
@login_required
def attendees_for_event(event_id):
    event = Event.query.get_or_404(event_id)

    if request.method == 'GET':
        attendees = [
            {
                'registration_id': registration.id,
                'attendee_id': registration.attendee.id,
                'name': registration.attendee.name,
                'email': registration.attendee.email,
                'attendee_id': registration.attendee.attendee_id
            }
            for registration in event.registrations
        ]
        return jsonify({'success': True, 'event_name': event.name, 'attendees': attendees})

    data = request.get_json(silent=True) or request.form
    email = data.get('email', '').strip()
    name = data.get('name', '').strip() or email
    attendee_id = data.get('attendee_id', '').strip() if data.get('attendee_id', '').strip() else generate_attendee_id()

    if not email:
        return jsonify({'success': False, 'message': 'Attendee email is required.'}), 400

    try:
        attendee = Attendee.query.filter_by(email=email).first()
        if not attendee:
            attendee = Attendee(name=name, email=email, attendee_id=attendee_id)
            db.session.add(attendee)
            db.session.flush()

        existing_registration = Registration.query.filter_by(event_id=event.id, attendee_id=attendee.id).first()
        if existing_registration:
            return jsonify({'success': False, 'message': 'Attendee is already registered for this event.'}), 400

        registration = Registration(event_id=event.id, attendee_id=attendee.id, created_by=current_user.id)
        db.session.add(registration)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Attendee added successfully.',
            'attendee': {
                'registration_id': registration.id,
                'attendee_id': attendee.id,
                'name': attendee.name,
                'email': attendee.email,
                'attendee_id': attendee.attendee_id
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@events_bp.route('/<string:event_id>/attendees/remove', methods=['POST'])
@login_required
def remove_event_attendee(event_id):
    event = Event.query.get_or_404(event_id)
    data = request.get_json(silent=True) or request.form
    registration_id = data.get('registration_id')

    if not registration_id:
        return jsonify({'success': False, 'message': 'Registration ID is required.'}), 400

    registration = Registration.query.filter_by(id=registration_id, event_id=event.id).first()
    if not registration:
        return jsonify({'success': False, 'message': 'Registration not found.'}), 404

    try:
        db.session.delete(registration)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Attendee removed successfully.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
def generate_attendee_id():
    return 'A' + datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')

