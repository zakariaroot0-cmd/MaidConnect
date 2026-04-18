from flask_mail import Message
from app import mail
from flask import render_template, current_app
from itsdangerous import URLSafeTimedSerializer
from flask import current_app, url_for
from flask_mail import Message
from app import mail

def generate_reset_token(email):
    """Génère un token de réinitialisation de mot de passe"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=1800):
    """Vérifie le token de réinitialisation"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        return email
    except:
        return None

def send_reset_email(user):
    """Envoie l'email de réinitialisation"""
    token = generate_reset_token(user.email)
    reset_url = url_for('reset_password', token=token, _external=True)
    
    msg = Message(
        'Réinitialisation de votre mot de passe - MaidConnect',
        recipients=[user.email],
        html=f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">🧹 MaidConnect</h1>
            </div>
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333;">Réinitialisation de mot de passe</h2>
                <p style="color: #666; line-height: 1.6;">Bonjour,</p>
                <p style="color: #666; line-height: 1.6;">Vous avez demandé la réinitialisation de votre mot de passe. Cliquez sur le bouton ci-dessous pour créer un nouveau mot de passe :</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">Réinitialiser mon mot de passe</a>
                </div>
                <p style="color: #666; line-height: 1.6;">Ce lien expirera dans 30 minutes.</p>
                <p style="color: #999; font-size: 12px; margin-top: 30px;">Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">Ou copiez ce lien : {reset_url}</p>
            </div>
        </div>
        '''
    )
    mail.send(msg)
    
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