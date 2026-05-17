from datetime import date, datetime

from app.routes.api import api_bp
from flask import request, jsonify
from app.models.events import Event
from app.models.attendee import Attendee
from app.models.registration import Registration
from flask_jwt_extended  import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from app.extensions import db 
from app.models.users import User

@api_bp.route('/login', methods=['POST'])
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    # Verify username and password (e.g., against a database)
    user = User.query.where(User.username == username) \
                         .where(User.status == 'active') \
                         .first()
    # print(user.username)
    if not user or not check_password_hash(user.password, password):
        return jsonify({"msg": "Bad username or password"}), 401

    # Create a token for this user
    access_token = create_access_token(identity=username)
    return jsonify({"access_token": access_token, "name": user.name}), 200

@api_bp.route('/events', methods=['GET'])
@jwt_required()
def get_events():
    from app.models.events import Event
    events = Event.query.all()
    events_data = [
        {
            'id': event.id,
            'name': event.name,
            'date': event.date.isoformat(),
            'location': event.location,
            'description': event.description,
            'attendees_count': len(event.registrations)
        }
        for event in events
    ]
    return jsonify({'success': True, 'events': events_data})

#todays_events = Event.query.filter(Event.date == today).count()
@api_bp.route('/events/current', methods=['GET'])
@jwt_required()
def get_current_events():
    today = date.today()
    events = Event.query.filter(Event.date == today).all()
    events_data = [
        {
            'id': event.id,
            'name': event.name,
            'date': event.date.isoformat(),
            'location': event.location,
            'description': event.description,
            'attendees_count': len(event.registrations)
        }
        for event in events
    ]
    return jsonify({'success': True, 'events': events_data})



@api_bp.route('/events/<string:event_id>', methods=['GET'])
@jwt_required()
def get_event(event_id):
    from app.models.events import Event
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'success': False, 'message': 'Event not found.'}), 404
    event_data = {
        'id': event.id,
        'name': event.name,
        'date': event.date.isoformat(),
        'location': event.location,
        'description': event.description,
        'attendees_count': len(event.registrations)
    }
    return jsonify({'success': True, 'event': event_data})
    
@api_bp.route('/events/<string:event_id>/attendees', methods=['GET'])
@jwt_required()
def get_event_attendees(event_id):
    from app.models.events import Event
    event = Event.query.get(event_id)
    
    if not event:
        return jsonify({'success': False, 'message': 'Event not found.'}), 404
    
    attendees_data = [
        {
            'id': registration.attendee.id,
            'name': registration.attendee.name,
            'email': registration.attendee.email,
            'attendee_id': registration.attendee.attendee_id
        }
        for registration in event.registrations
    ]
    return jsonify({'success': True, 'event_name': event.name, 'attendees': attendees_data})    

@api_bp.route('/reports/summary', methods=['GET'])
@jwt_required()
def get_summary_report():
   
    from datetime import date

    today = date.today()
    total_events = Event.query.count()
    total_attendees = Attendee.query.count()
    total_registrations = Registration.query.count()
    upcoming_events = Event.query.filter(Event.date >= today).count()
    todays_events = Event.query.filter(Event.date == today).count() 

    return jsonify({
        'success': True,
        'summary': {
            'total_events': total_events,
            'total_attendees': total_attendees,
            'total_registrations': total_registrations,
            'upcoming_events': upcoming_events,
            'todays_events': todays_events
        }
    })

#mark attendee as checked in
@api_bp.route('/events/<string:event_id>/attendees/checkin', methods=['POST'])
@jwt_required()  # Only allow access tokens for this endpoint
def checkin_attendee(event_id):
    attendee_id = request.json.get('attendee_id', '').strip()
   
    if not attendee_id:
        return jsonify({'success': False, 'message': 'Attendee ID is required.'}), 400
    
    # Verify that the event exists and it is happening today
    event = Event.query.get(event_id)

    if not event:
        return jsonify({'success': False, 'message': 'Event not found.'}), 404
    
    if event.date.date() != date.today():
        return jsonify({'success': False, 'message': 'Check-in is only allowed on the day of the event.'}), 400
    
    registration = Registration.query.filter_by(event_id=event_id, attendee_id=attendee_id).first()
    if not registration:
        return jsonify({'success': False, 'message': 'Registration not found for this attendee and event.'}), 404

    registration.checked_in = True
    registration.checked_in_at = datetime.datetime.utcnow()
    registration.checked_in_by = get_jwt_identity()  # Store the username of the user who checked in the attendee

    db.session.commit()
    return jsonify({'success': True, 'message': 'Attendee checked in successfully.'})