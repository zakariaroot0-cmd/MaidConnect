import os
import secrets
import csv
from io import StringIO
from PIL import Image
from flask import render_template, redirect, url_for, flash, request, current_app, make_response
from flask_login import login_user, logout_user, current_user, login_required
from sqlalchemy import func
from app import db, bcrypt
from app.models import User, MaidProfile, ClientProfile, Favorite, ContactRequest, Message, Review, Notification
from app.forms import (RegistrationForm, LoginForm, MaidProfileForm, 
                       ContactRequestForm, MessageForm, ReviewForm,
                       AdminVerifyMaidForm, AdminUserForm, RequestResetForm, ResetPasswordForm)
from app.utils import send_reset_email, verify_reset_token

def init_routes(app):
    
    def save_picture(form_picture):
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_picture.filename)
        picture_fn = random_hex + f_ext
        picture_path = os.path.join(current_app.root_path, 'static/uploads', picture_fn)
        
        output_size = (300, 300)
        i = Image.open(form_picture)
        i.thumbnail(output_size)
        i.save(picture_path)
        
        return picture_fn
    
    # ========== ROUTES PUBLIQUES ==========
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        try:
            if current_user.is_authenticated:
                return redirect(url_for('dashboard'))
            
            form = RegistrationForm()
            if form.validate_on_submit():
                hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                user = User(email=form.email.data, password=hashed_password, role=form.role.data)
                db.session.add(user)
                db.session.commit()
                
                login_user(user)
                flash('Inscription réussie ! Complétez votre profil.', 'success')
                
                if user.role == 'maid':
                    return redirect(url_for('complete_maid_profile'))
                elif user.role == 'client':
                    return redirect(url_for('complete_client_profile'))
                else:
                    return redirect(url_for('dashboard'))
            
            return render_template('register.html', form=form)
        except Exception as e:
            db.session.rollback()
            flash('Une erreur est survenue lors de l\'inscription.', 'danger')
            app.logger.error(f"Erreur d'inscription: {str(e)}")
            return redirect(url_for('register'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                flash(f'Bienvenue {user.email} !', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Email ou mot de passe incorrect.', 'danger')
        
        return render_template('login.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Vous êtes déconnecté.', 'info')
        return redirect(url_for('index'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif current_user.role == 'maid':
            return redirect(url_for('maid_dashboard'))
        else:
            return redirect(url_for('client_dashboard'))
    
    # ========== RÉINITIALISATION MOT DE PASSE ==========
    @app.route('/reset-password', methods=['GET', 'POST'])
    def request_reset():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = RequestResetForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user:
                send_reset_email(user)
            flash('Un email de réinitialisation a été envoyé si ce compte existe.', 'info')
            return redirect(url_for('login'))
        
        return render_template('auth/request_reset.html', form=form)
    
    @app.route('/reset-password/<token>', methods=['GET', 'POST'])
    def reset_password(token):
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        email = verify_reset_token(token)
        if not email:
            flash('Le lien est invalide ou a expiré.', 'danger')
            return redirect(url_for('request_reset'))
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Utilisateur introuvable.', 'danger')
            return redirect(url_for('request_reset'))
        
        form = ResetPasswordForm()
        if form.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user.password = hashed_password
            db.session.commit()
            flash('Votre mot de passe a été réinitialisé ! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('login'))
        
        return render_template('auth/reset_password.html', form=form)
    
    # ========== COMPLÉTION DE PROFIL ==========
    @app.route('/complete-maid-profile', methods=['GET', 'POST'])
    @login_required
    def complete_maid_profile():
        if current_user.role != 'maid':
            return redirect(url_for('dashboard'))
        if current_user.maid_profile:
            return redirect(url_for('dashboard'))
        
        form = MaidProfileForm()
        if form.validate_on_submit():
            profile = MaidProfile(
                user_id=current_user.id,
                full_name=form.full_name.data,
                phone=form.phone.data,
                city=form.city.data,
                hourly_rate=form.hourly_rate.data,
                languages=form.languages.data,
                experience=form.experience.data,
                skills=form.skills.data
            )
            
            if form.profile_picture.data:
                picture_file = save_picture(form.profile_picture.data)
                profile.profile_picture = picture_file
            
            db.session.add(profile)
            db.session.commit()
            flash('Profil complété avec succès ! En attente de vérification par l\'admin.', 'success')
            return redirect(url_for('dashboard'))
        
        return render_template('maid/complete_profile.html', form=form)
    
    @app.route('/complete-client-profile')
    @login_required
    def complete_client_profile():
        if current_user.client_profile:
            return redirect(url_for('dashboard'))
        
        profile = ClientProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
        flash('Profil client créé !', 'success')
        return redirect(url_for('dashboard'))
    
    # ========== RECHERCHE ET PROFILS ==========
    @app.route('/maids')
    def browse_maids():
        city = request.args.get('city', '')
        min_rate = request.args.get('min_rate', type=float)
        max_rate = request.args.get('max_rate', type=float)
        languages = request.args.get('languages', '')
        
        query = MaidProfile.query.filter_by(is_available=True)
        
        if city:
            query = query.filter(MaidProfile.city.ilike(f'%{city}%'))
        if min_rate:
            query = query.filter(MaidProfile.hourly_rate >= min_rate)
        if max_rate:
            query = query.filter(MaidProfile.hourly_rate <= max_rate)
        if languages:
            query = query.filter(MaidProfile.languages.ilike(f'%{languages}%'))
        
        maids = query.limit(20).all()
        cities = db.session.query(MaidProfile.city).distinct().all()
        
        return render_template('browse_maids.html', maids=maids, cities=cities)
    
    @app.route('/maid/<int:maid_id>')
    def maid_profile(maid_id):
        """Profil public d'une aide ménagère"""
        maid_profile = MaidProfile.query.get_or_404(maid_id)
        user = User.query.get(maid_profile.user_id)
        
        # Vérifier si c'est dans les favoris du client connecté
        is_favorite = False
        if current_user.is_authenticated and current_user.role == 'client':
            favorite = Favorite.query.filter_by(
                client_id=current_user.id, 
                maid_id=user.id
            ).first()
            is_favorite = favorite is not None
        
        # FORCE l'utilisation du bon template
        return render_template('public_maid_profile.html', 
                            maid=maid_profile, 
                            user=user,
                            is_favorite=is_favorite)
    @app.route('/favorite/<int:maid_id>', methods=['POST'])
    @login_required
    def toggle_favorite(maid_id):
        if current_user.role != 'client':
            flash('Seuls les clients peuvent ajouter des favoris.', 'danger')
            return redirect(url_for('browse_maids'))
        
        favorite = Favorite.query.filter_by(
            client_id=current_user.id, 
            maid_id=maid_id
        ).first()
        
        if favorite:
            db.session.delete(favorite)
            flash('Retiré des favoris.', 'info')
        else:
            favorite = Favorite(client_id=current_user.id, maid_id=maid_id)
            db.session.add(favorite)
            flash('Ajouté aux favoris !', 'success')
        
        db.session.commit()
        return redirect(url_for('maid_profile', maid_id=maid_id))
    
    # ========== DASHBOARDS ==========
    @app.route('/client/dashboard')
    @login_required
    def client_dashboard():
        if current_user.role != 'client':
            return redirect(url_for('dashboard'))
        
        if not current_user.client_profile:
            return redirect(url_for('complete_client_profile'))
        
        favorites = Favorite.query.filter_by(client_id=current_user.id).all()
        favorite_maids = []
        for fav in favorites:
            maid_user = User.query.get(fav.maid_id)
            if maid_user and maid_user.maid_profile:
                favorite_maids.append(maid_user.maid_profile)
        
        requests = ContactRequest.query.filter_by(client_id=current_user.id).order_by(
            ContactRequest.created_at.desc()
        ).limit(10).all()
        
        return render_template('client/dashboard.html', 
                             favorite_maids=favorite_maids,
                             requests=requests)
    
    @app.route('/maid/dashboard')
    @login_required
    def maid_dashboard():
        if current_user.role != 'maid':
            return redirect(url_for('dashboard'))
        
        if not current_user.maid_profile:
            return redirect(url_for('complete_maid_profile'))
        
        requests = ContactRequest.query.filter_by(maid_id=current_user.id).order_by(
            ContactRequest.created_at.desc()
        ).limit(10).all()
        
        return render_template('maid/dashboard.html', 
                             profile=current_user.maid_profile,
                             requests=requests)
    
    # ========== MESSAGERIE ET CONTACT ==========
    @app.route('/contact/<int:maid_id>', methods=['GET', 'POST'])
    @login_required
    def contact_maid(maid_id):
        if current_user.role != 'client':
            flash('Seuls les clients peuvent contacter les aides ménagères.', 'danger')
            return redirect(url_for('browse_maids'))
        
        maid_user = User.query.get_or_404(maid_id)
        if maid_user.role != 'maid':
            flash('Utilisateur invalide.', 'danger')
            return redirect(url_for('browse_maids'))
        
        existing_request = ContactRequest.query.filter_by(
            client_id=current_user.id,
            maid_id=maid_id,
            status='pending'
        ).first()
        
        if existing_request:
            flash('Vous avez déjà une demande en cours avec cette aide.', 'info')
            return redirect(url_for('view_request', request_id=existing_request.id))
        
        form = ContactRequestForm()
        if form.validate_on_submit():
            contact_request = ContactRequest(
                client_id=current_user.id,
                maid_id=maid_id,
                message=form.message.data
            )
            db.session.add(contact_request)
            db.session.commit()
            
            flash('Demande envoyée avec succès !', 'success')
            return redirect(url_for('view_request', request_id=contact_request.id))
        
        return render_template('contact_request.html', 
                             form=form, 
                             maid=maid_user.maid_profile)
    
    @app.route('/request/<int:request_id>')
    @login_required
    def view_request(request_id):
        contact_request = ContactRequest.query.get_or_404(request_id)
        
        if current_user.id not in [contact_request.client_id, contact_request.maid_id] and current_user.role != 'admin':
            flash('Accès non autorisé.', 'danger')
            return redirect(url_for('dashboard'))
        
        messages = Message.query.filter_by(request_id=request_id).order_by(
            Message.created_at.asc()
        ).all()
        
        form = MessageForm()
        
        return render_template('view_request.html', 
                             request=contact_request,
                             messages=messages,
                             form=form)
    
    @app.route('/request/<int:request_id>/message', methods=['POST'])
    @login_required
    def send_message(request_id):
        contact_request = ContactRequest.query.get_or_404(request_id)
        
        if current_user.id not in [contact_request.client_id, contact_request.maid_id]:
            flash('Accès non autorisé.', 'danger')
            return redirect(url_for('dashboard'))
        
        if contact_request.status != 'accepted':
            flash('La conversation n\'est pas active.', 'warning')
            return redirect(url_for('view_request', request_id=request_id))
        
        form = MessageForm()
        if form.validate_on_submit():
            receiver_id = contact_request.maid_id if current_user.id == contact_request.client_id else contact_request.client_id
            
            message = Message(
                sender_id=current_user.id,
                receiver_id=receiver_id,
                request_id=request_id,
                content=form.content.data
            )
            db.session.add(message)
            db.session.commit()
            
            flash('Message envoyé.', 'success')
        
        return redirect(url_for('view_request', request_id=request_id))
    
    @app.route('/request/<int:request_id>/respond', methods=['POST'])
    @login_required
    def respond_request(request_id):
        contact_request = ContactRequest.query.get_or_404(request_id)
        
        if current_user.id != contact_request.maid_id:
            flash('Action non autorisée.', 'danger')
            return redirect(url_for('dashboard'))
        
        action = request.form.get('action')
        if action == 'accept':
            contact_request.status = 'accepted'
            flash('Demande acceptée. Vous pouvez maintenant communiquer.', 'success')
        elif action == 'reject':
            contact_request.status = 'rejected'
            flash('Demande refusée.', 'info')
        
        db.session.commit()
        return redirect(url_for('view_request', request_id=request_id))
    
    @app.route('/request/<int:request_id>/complete', methods=['POST'])
    @login_required
    def complete_request(request_id):
        contact_request = ContactRequest.query.get_or_404(request_id)
        
        if current_user.id != contact_request.client_id:
            flash('Action non autorisée.', 'danger')
            return redirect(url_for('dashboard'))
        
        if contact_request.status == 'accepted':
            contact_request.status = 'completed'
            db.session.commit()
            flash('Prestation marquée comme terminée. Vous pouvez laisser un avis.', 'success')
            return redirect(url_for('leave_review', request_id=request_id))
        
        return redirect(url_for('view_request', request_id=request_id))
    
    @app.route('/request/<int:request_id>/review', methods=['GET', 'POST'])
    @login_required
    def leave_review(request_id):
        contact_request = ContactRequest.query.get_or_404(request_id)
        
        if current_user.id != contact_request.client_id:
            flash('Action non autorisée.', 'danger')
            return redirect(url_for('dashboard'))
        
        if contact_request.status != 'completed':
            flash('Vous ne pouvez laisser un avis que sur une prestation terminée.', 'warning')
            return redirect(url_for('view_request', request_id=request_id))
        
        existing_review = Review.query.filter_by(request_id=request_id).first()
        if existing_review:
            flash('Vous avez déjà laissé un avis pour cette prestation.', 'info')
            return redirect(url_for('view_request', request_id=request_id))
        
        form = ReviewForm()
        if form.validate_on_submit():
            review = Review(
                request_id=request_id,
                rating=int(form.rating.data),
                comment=form.comment.data
            )
            db.session.add(review)
            
            maid_profile = contact_request.maid.maid_profile
            if maid_profile:
                all_reviews = Review.query.join(ContactRequest).filter(
                    ContactRequest.maid_id == contact_request.maid_id,
                    Review.is_visible == True
                ).all()
                
                total_rating = sum(r.rating for r in all_reviews) + review.rating
                maid_profile.rating = total_rating / (len(all_reviews) + 1)
            
            db.session.commit()
            flash('Merci pour votre avis !', 'success')
            return redirect(url_for('view_request', request_id=request_id))
        
        return render_template('leave_review.html', form=form, request=contact_request)
    
    @app.route('/messages')
    @login_required
    def messages():
        if current_user.role == 'client':
            requests = ContactRequest.query.filter_by(
                client_id=current_user.id
            ).filter(
                ContactRequest.status.in_(['accepted', 'completed'])
            ).order_by(ContactRequest.updated_at.desc()).all()
        else:
            requests = ContactRequest.query.filter_by(
                maid_id=current_user.id
            ).filter(
                ContactRequest.status.in_(['accepted', 'completed'])
            ).order_by(ContactRequest.updated_at.desc()).all()
        
        return render_template('messages.html', requests=requests)
    
    # ========== NOTIFICATIONS ==========
    @app.route('/notifications')
    @login_required
    def notifications():
        page = request.args.get('page', 1, type=int)
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
            Notification.created_at.desc()
        ).paginate(page=page, per_page=20)
        
        return render_template('notifications.html', notifications=notifications)
    
    @app.route('/notifications/count')
    @login_required
    def notification_count():
        count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        return {'count': count}
    
    # ========== ROUTES ADMIN ==========
    @app.route('/admin/dashboard')
    @login_required
    def admin_dashboard():
        if current_user.role != 'admin':
            flash('Accès réservé aux administrateurs.', 'danger')
            return redirect(url_for('dashboard'))
        
        total_users = User.query.count()
        total_maids = User.query.filter_by(role='maid').count()
        total_clients = User.query.filter_by(role='client').count()
        pending_verifications = MaidProfile.query.join(User).filter(User.is_verified == False).count()
        active_requests = ContactRequest.query.filter_by(status='accepted').count()
        completed_requests = ContactRequest.query.filter_by(status='completed').count()
        total_reviews = Review.query.count()
        avg_rating = db.session.query(func.avg(Review.rating)).scalar() or 0
        
        monthly_users = db.session.query(
            func.strftime('%Y-%m', User.created_at).label('month'),
            func.count(User.id).label('count')
        ).group_by('month').order_by('month').limit(12).all()
        
        months = [m[0] for m in monthly_users] if monthly_users else []
        counts = [m[1] for m in monthly_users] if monthly_users else []
        
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        recent_requests = ContactRequest.query.order_by(ContactRequest.created_at.desc()).limit(5).all()
        
        return render_template('admin/dashboard.html',
                             total_users=total_users,
                             total_maids=total_maids,
                             total_clients=total_clients,
                             pending_verifications=pending_verifications,
                             active_requests=active_requests,
                             completed_requests=completed_requests,
                             total_reviews=total_reviews,
                             avg_rating=avg_rating,
                             months=months,
                             counts=counts,
                             recent_users=recent_users,
                             recent_requests=recent_requests)
    
    @app.route('/admin/users')
    @login_required
    def admin_users():
        if current_user.role != 'admin':
            return redirect(url_for('dashboard'))
        
        page = request.args.get('page', 1, type=int)
        role_filter = request.args.get('role', '')
        search = request.args.get('search', '')
        
        query = User.query
        
        if role_filter:
            query = query.filter_by(role=role_filter)
        if search:
            query = query.filter(User.email.ilike(f'%{search}%'))
        
        users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
        
        return render_template('admin/users.html', users=users)
    
    @app.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
    @login_required
    def admin_user_detail(user_id):
        if current_user.role != 'admin':
            return redirect(url_for('dashboard'))
        
        user = User.query.get_or_404(user_id)
        form = AdminUserForm(obj=user)
        
        if form.validate_on_submit():
            user.is_active = form.is_active.data
            user.role = form.role.data
            db.session.commit()
            flash('Utilisateur mis à jour.', 'success')
            return redirect(url_for('admin_users'))
        
        return render_template('admin/user_detail.html', user=user, form=form)
    
    @app.route('/admin/maids')
    @login_required
    def admin_maids():
        if current_user.role != 'admin':
            return redirect(url_for('dashboard'))
        
        page = request.args.get('page', 1, type=int)
        verification_status = request.args.get('status', '')
        
        query = MaidProfile.query.join(User)
        
        if verification_status == 'pending':
            query = query.filter(User.is_verified == False)
        elif verification_status == 'verified':
            query = query.filter(User.is_verified == True)
        
        maids = query.order_by(MaidProfile.created_at.desc()).paginate(page=page, per_page=20)
        
        return render_template('admin/maids.html', maids=maids)
    
    @app.route('/admin/maid/<int:maid_id>', methods=['GET', 'POST'])
    @login_required
    def admin_maid_detail(maid_id):
        if current_user.role != 'admin':
            return redirect(url_for('dashboard'))
        
        maid_profile = MaidProfile.query.get_or_404(maid_id)
        user = maid_profile.user
        
        form = AdminVerifyMaidForm(obj=maid_profile)
        if request.method == 'GET':
            form.is_verified.data = 'verified' if user.is_verified else 'pending'
        
        if form.validate_on_submit():
            user.is_verified = (form.is_verified.data == 'verified')
            maid_profile.admin_notes = form.admin_notes.data
            db.session.commit()
            flash('Profil mis à jour.', 'success')
            return redirect(url_for('admin_maids'))
        
        completed_requests = ContactRequest.query.filter_by(maid_id=user.id, status='completed').count()
        reviews = Review.query.join(ContactRequest).filter(ContactRequest.maid_id == user.id).order_by(Review.created_at.desc()).limit(10).all()
        
        return render_template('admin/maid_detail.html',
                             maid=maid_profile,
                             user=user,
                             form=form,
                             completed_requests=completed_requests,
                             reviews=reviews)
    
    @app.route('/admin/requests')
    @login_required
    def admin_requests():
        if current_user.role != 'admin':
            return redirect(url_for('dashboard'))
        
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', '')
        
        query = ContactRequest.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        requests = query.order_by(ContactRequest.created_at.desc()).paginate(page=page, per_page=15)
        
        pending_count = ContactRequest.query.filter_by(status='pending').count()
        accepted_count = ContactRequest.query.filter_by(status='accepted').count()
        completed_count = ContactRequest.query.filter_by(status='completed').count()
        
        return render_template('admin/requests.html', 
                             requests=requests,
                             pending_count=pending_count,
                             accepted_count=accepted_count,
                             completed_count=completed_count)
    
    @app.route('/admin/reviews')
    @login_required
    def admin_reviews():
        if current_user.role != 'admin':
            return redirect(url_for('dashboard'))
        
        page = request.args.get('page', 1, type=int)
        reviews = Review.query.order_by(Review.created_at.desc()).paginate(page=page, per_page=10)
        
        avg_rating = db.session.query(func.avg(Review.rating)).scalar() or 0
        visible_count = Review.query.filter_by(is_visible=True).count()
        
        return render_template('admin/reviews.html', 
                             reviews=reviews,
                             avg_rating=avg_rating,
                             visible_count=visible_count)
    
    @app.route('/admin/review/<int:review_id>/toggle', methods=['POST'])
    @login_required
    def admin_toggle_review(review_id):
        if current_user.role != 'admin':
            return redirect(url_for('dashboard'))
        
        review = Review.query.get_or_404(review_id)
        review.is_visible = not review.is_visible
        db.session.commit()
        
        flash(f'Avis {"affiché" if review.is_visible else "masqué"}.', 'success')
        return redirect(url_for('admin_reviews'))
    
    @app.route('/admin/export/users')
    @login_required
    def export_users():
        if current_user.role != 'admin':
            return redirect(url_for('dashboard'))
        
        users = User.query.all()
        
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['ID', 'Email', 'Rôle', 'Vérifié', 'Date inscription'])
        
        for user in users:
            cw.writerow([
                user.id,
                user.email,
                user.role,
                'Oui' if user.is_verified else 'Non',
                user.created_at.strftime('%d/%m/%Y')
            ])
        
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=users_export.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    
    # ========== API ==========
    @app.route('/api/maids')
    def api_maids():
        city = request.args.get('city')
        query = MaidProfile.query.filter_by(is_available=True)
        
        if city:
            query = query.filter(MaidProfile.city.ilike(f'%{city}%'))
        
        maids = query.limit(50).all()
        
        return {
            'maids': [{
                'id': m.id,
                'name': m.full_name,
                'city': m.city,
                'rate': m.hourly_rate,
                'rating': m.rating,
                'verified': m.user.is_verified
            } for m in maids]
        }