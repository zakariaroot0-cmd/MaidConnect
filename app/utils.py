from flask_mail import Message
from app import mail
from flask import render_template, current_app

def send_email(to, subject, template, **kwargs):
    msg = Message(
        subject,
        recipients=[to],
        html=render_template(template + '.html', **kwargs),
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    mail.send(msg)
def create_notification(user_id, title, message, type='info', icon='bell', link=None):
    """Crée une notification pour un utilisateur"""
    from app.models import Notification
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        icon=icon,
        link=link
    )
    db.session.add(notification)
    db.session.commit()
    return notification

def send_notification_email(user, notification_type, **kwargs):
    """Envoie un email de notification selon le type"""
    subjects = {
        'welcome': 'Bienvenue sur MaidConnect !',
        'request_received': 'Nouvelle demande de contact',
        'request_accepted': 'Votre demande a été acceptée !',
        'request_rejected': 'Mise à jour de votre demande',
        'new_message': 'Nouveau message reçu',
        'profile_verified': 'Votre profil a été vérifié !',
        'review_received': 'Vous avez reçu un nouvel avis'
    }
    
    templates = {
        'welcome': 'emails/welcome',
        'request_received': 'emails/request_received',
        'request_accepted': 'emails/request_accepted',
        'request_rejected': 'emails/request_rejected',
        'new_message': 'emails/new_message',
        'profile_verified': 'emails/profile_verified',
        'review_received': 'emails/review_received'
    }
    
    if notification_type in subjects:
        send_email(user.email, subjects[notification_type], templates[notification_type], user=user, **kwargs)