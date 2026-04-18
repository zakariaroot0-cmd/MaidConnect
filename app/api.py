from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import MaidProfile, User

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/maids')
def get_maids():
    """API publique pour récupérer la liste des maids"""
    city = request.args.get('city')
    min_rate = request.args.get('min_rate', type=float)
    max_rate = request.args.get('max_rate', type=float)
    
    query = MaidProfile.query.filter_by(is_available=True)
    
    if city:
        query = query.filter(MaidProfile.city.ilike(f'%{city}%'))
    if min_rate:
        query = query.filter(MaidProfile.hourly_rate >= min_rate)
    if max_rate:
        query = query.filter(MaidProfile.hourly_rate <= max_rate)
    
    maids = query.limit(50).all()
    
    return jsonify([{
        'id': m.id,
        'name': m.full_name,
        'city': m.city,
        'rate': m.hourly_rate,
        'rating': m.rating,
        'verified': m.user.is_verified,
        'picture': m.profile_picture
    } for m in maids])

@api.route('/notifications/unread')
@login_required
def unread_notifications():
    """API pour les notifications non lues"""
    from app.models import Notification
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).limit(5).all()
    
    return jsonify({
        'count': count,
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.type,
            'link': n.link,
            'created': n.created_at.isoformat()
        } for n in notifications]
    })