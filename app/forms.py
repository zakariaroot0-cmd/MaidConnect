from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, FloatField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User
from flask_wtf.file import FileField, FileAllowed


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmer le mot de passe', 
                                     validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Je suis', choices=[
        ('client', 'Client - Je cherche une aide ménagère'),
        ('maid', 'Aide ménagère - Je propose mes services')
    ], validators=[DataRequired()])
    submit = SubmitField('S\'inscrire')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Cet email est déjà utilisé.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Se connecter')

class MaidProfileForm(FlaskForm):
    full_name = StringField('Nom complet', validators=[DataRequired()])
    phone = StringField('Téléphone', validators=[DataRequired()])
    city = StringField('Ville', validators=[DataRequired()])
    hourly_rate = FloatField('Tarif horaire (DH)', validators=[DataRequired()])
    languages = StringField('Langues parlées (ex: Français, Arabe)', validators=[DataRequired()])
    experience = TextAreaField('Expérience professionnelle')
    skills = TextAreaField('Compétences (cuisine, ménage, garde d\'enfants...)')
    submit = SubmitField('Compléter mon profil')

class ContactRequestForm(FlaskForm):
    message = TextAreaField('Message (optionnel)', validators=[Length(max=500)])
    submit = SubmitField('Envoyer la demande')

class MessageForm(FlaskForm):
    content = TextAreaField('Votre message', validators=[DataRequired(), Length(min=1, max=1000)])
    submit = SubmitField('Envoyer')

class ReviewForm(FlaskForm):
    rating = SelectField('Note', choices=[(5, '★★★★★ (5)'), (4, '★★★★☆ (4)'), 
                                          (3, '★★★☆☆ (3)'), (2, '★★☆☆☆ (2)'), 
                                          (1, '★☆☆☆☆ (1)')], validators=[DataRequired()])
    comment = TextAreaField('Commentaire (optionnel)')
    submit = SubmitField('Donner mon avis')

class AdminVerifyMaidForm(FlaskForm):
    is_verified = SelectField('Statut de vérification', 
                             choices=[('pending', 'En attente'), 
                                     ('verified', 'Vérifié ✅'), 
                                     ('rejected', 'Rejeté ❌')])
    admin_notes = TextAreaField('Notes internes')
    submit = SubmitField('Mettre à jour')

class MaidProfileForm(FlaskForm):
    full_name = StringField('Nom complet', validators=[DataRequired()])
    phone = StringField('Téléphone', validators=[DataRequired()])
    city = StringField('Ville', validators=[DataRequired()])
    hourly_rate = FloatField('Tarif horaire (DH)', validators=[DataRequired()])
    languages = StringField('Langues parlées (ex: Français, Arabe)', validators=[DataRequired()])
    experience = TextAreaField('Expérience professionnelle')
    skills = TextAreaField('Compétences (cuisine, ménage, garde d\'enfants...)')
    profile_picture = FileField('Photo de profil', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images uniquement!')])
    submit = SubmitField('Compléter mon profil')

class AdminUserForm(FlaskForm):
    is_active = BooleanField('Compte actif')
    role = SelectField('Rôle', choices=[('client', 'Client'), 
                                        ('maid', 'Aide ménagère'),
                                        ('admin', 'Administrateur')])
    submit = SubmitField('Mettre à jour')
class AdvancedSearchForm(FlaskForm):
    city = StringField('Ville')
    min_rate = FloatField('Tarif minimum')
    max_rate = FloatField('Tarif maximum')
    languages = StringField('Langues')
    min_rating = FloatField('Note minimum')
    skills = StringField('Compétences')
    availability = SelectField('Disponibilité', choices=[
        ('', 'Toutes'),
        ('weekdays', 'En semaine'),
        ('weekends', 'Week-end'),
        ('mornings', 'Matin'),
        ('afternoons', 'Après-midi')
    ])
    verified_only = BooleanField('Profils vérifiés uniquement')
    has_reviews = BooleanField('Avec avis uniquement')
    submit = SubmitField('Rechercher')