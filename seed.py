"""
Script pour remplir la base de données avec des données de test
Exécution : python seed.py
"""

from faker import Faker
from app import create_app, db, bcrypt
from app.models import User, MaidProfile, ClientProfile, ContactRequest, Message, Review
import random
from datetime import datetime, timedelta

# Initialisation
fake = Faker('fr_FR')  # Données en français
app = create_app()

# Villes marocaines populaires
CITIES = [
    'Casablanca', 'Rabat', 'Marrakech', 'Fès', 'Tanger', 
    'Agadir', 'Meknès', 'Oujda', 'Kenitra', 'Tétouan',
    'Safi', 'Mohammedia', 'El Jadida', 'Nador', 'Khouribga'
]

# Compétences courantes
SKILLS_LIST = [
    'Ménage', 'Cuisine', 'Garde d\'enfants', 'Repassage', 
    'Courses', 'Aide aux devoirs', 'Soins aux personnes âgées',
    'Nettoyage approfondi', 'Organisation', 'Préparation de repas'
]

# Langues
LANGUAGES_LIST = [
    'Arabe', 'Français', 'Anglais', 'Espagnol', 'Amazigh'
]

def create_admin():
    """Crée un compte administrateur"""
    admin = User.query.filter_by(email='admin@maidconnect.com').first()
    if not admin:
        admin = User(
            email='admin@maidconnect.com',
            password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            role='admin',
            is_verified=True,
            is_active=True
        )
        db.session.add(admin)
        print("✅ Admin créé : admin@maidconnect.com / admin123")
    return admin

def create_clients(num=15):
    """Crée des clients de test"""
    clients = []
    
    for _ in range(num):
        email = fake.unique.email()
        user = User(
            email=email,
            password=bcrypt.generate_password_hash('client123').decode('utf-8'),
            role='client',
            is_verified=True,
            is_active=True,
            created_at=fake.date_time_between(start_date='-6m', end_date='now')
        )
        db.session.add(user)
        db.session.flush()
        
        # Profil client
        profile = ClientProfile(
            user_id=user.id,
            full_name=fake.name(),
            phone=fake.phone_number(),
            address=fake.address(),
            created_at=user.created_at
        )
        db.session.add(profile)
        clients.append(user)
    
    print(f"✅ {num} clients créés")
    return clients

def create_maids(num=25):
    """Crée des aides ménagères de test avec photos de profil"""
    maids = []
    
    for _ in range(num):
        gender = random.choice(['M', 'F'])
        first_name = fake.first_name_female() if gender == 'F' else fake.first_name_male()
        last_name = fake.last_name()
        full_name = f"{first_name} {last_name}"
        
        email = fake.unique.email()
        user = User(
            email=email,
            password=bcrypt.generate_password_hash('maid123').decode('utf-8'),
            role='maid',
            is_verified=random.choice([True, True, True, False]),  # 75% vérifié
            is_active=True,
            created_at=fake.date_time_between(start_date='-1y', end_date='now')
        )
        db.session.add(user)
        db.session.flush()
        
        # Générer des compétences aléatoires
        num_skills = random.randint(2, 5)
        skills = random.sample(SKILLS_LIST, num_skills)
        
        # Générer des langues aléatoires
        num_languages = random.randint(1, 3)
        languages = random.sample(LANGUAGES_LIST, num_languages)
        
        # Photo de profil (utilise UI Avatars pour générer des avatars)
        profile_picture = f"https://ui-avatars.com/api/?name={first_name}+{last_name}&size=300&background=random&color=fff"
        
        # Profil maid
        profile = MaidProfile(
            user_id=user.id,
            full_name=full_name,
            phone=fake.phone_number(),
            city=random.choice(CITIES),
            hourly_rate=round(random.uniform(30, 150), 2),
            languages=', '.join(languages),
            experience=fake.paragraph(nb_sentences=random.randint(2, 5)),
            skills=', '.join(skills),
            is_available=random.choice([True, True, True, False]),  # 75% disponible
            rating=round(random.uniform(3.5, 5.0), 1),
            created_at=user.created_at,
            profile_picture=profile_picture
        )
        db.session.add(profile)
        maids.append(user)
    
    print(f"✅ {num} aides ménagères créées")
    return maids

def create_requests(clients, maids, num=40):
    """Crée des demandes de contact"""
    statuses = ['pending', 'accepted', 'rejected', 'completed']
    weights = [0.2, 0.3, 0.1, 0.4]  # Probabilités pour chaque statut
    
    requests = []
    
    for _ in range(num):
        client = random.choice(clients)
        maid = random.choice(maids)
        
        # Éviter les doublons client-maid
        existing = ContactRequest.query.filter_by(
            client_id=client.id, 
            maid_id=maid.id
        ).first()
        
        if existing:
            continue
        
        status = random.choices(statuses, weights=weights)[0]
        created_at = fake.date_time_between(
            start_date=max(client.created_at, maid.created_at),
            end_date='now'
        )
        
        contact_request = ContactRequest(
            client_id=client.id,
            maid_id=maid.id,
            message=fake.paragraph(nb_sentences=random.randint(1, 3)) if random.random() > 0.3 else None,
            status=status,
            created_at=created_at,
            updated_at=created_at + timedelta(days=random.randint(0, 5))
        )
        db.session.add(contact_request)
        db.session.flush()
        requests.append(contact_request)
        
        # Ajouter des messages pour les demandes acceptées
        if status in ['accepted', 'completed']:
            num_messages = random.randint(2, 8)
            for i in range(num_messages):
                sender_id = client.id if i % 2 == 0 else maid.id
                receiver_id = maid.id if i % 2 == 0 else client.id
                
                message = Message(
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    request_id=contact_request.id,
                    content=fake.paragraph(nb_sentences=random.randint(1, 2)),
                    is_read=random.choice([True, False]),
                    created_at=created_at + timedelta(hours=random.randint(1, 48))
                )
                db.session.add(message)
        
        # Ajouter des avis pour les demandes terminées
        if status == 'completed' and random.random() > 0.3:
            review = Review(
                request_id=contact_request.id,
                rating=random.randint(3, 5),
                comment=fake.paragraph(nb_sentences=random.randint(1, 3)) if random.random() > 0.2 else None,
                is_visible=True,
                created_at=created_at + timedelta(days=random.randint(1, 7))
            )
            db.session.add(review)
            
            # Mettre à jour la note de la maid
            maid_profile = MaidProfile.query.filter_by(user_id=maid.id).first()
            if maid_profile:
                all_reviews = Review.query.join(ContactRequest).filter(
                    ContactRequest.maid_id == maid.id,
                    Review.is_visible == True
                ).all()
                if all_reviews:
                    avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews)
                    maid_profile.rating = round(avg_rating, 1)
    
    print(f"✅ {len(requests)} demandes créées")
    return requests

def create_favorites(clients, maids):
    """Crée des favoris"""
    count = 0
    for client in clients:
        num_favorites = random.randint(0, 5)
        favorite_maids = random.sample(maids, min(num_favorites, len(maids)))
        
        for maid in favorite_maids:
            from app.models import Favorite
            existing = Favorite.query.filter_by(
                client_id=client.id,
                maid_id=maid.id
            ).first()
            
            if not existing:
                favorite = Favorite(
                    client_id=client.id,
                    maid_id=maid.id,
                    created_at=fake.date_time_between(start_date=client.created_at, end_date='now')
                )
                db.session.add(favorite)
                count += 1
    
    print(f"✅ {count} favoris créés")

def main():
    """Fonction principale"""
    with app.app_context():
        print("\n" + "="*50)
        print("🌱 DÉMARRAGE DU SEEDING DE LA BASE DE DONNÉES")
        print("="*50 + "\n")
        
        # Supprimer toutes les données existantes
        print("🗑️  Suppression des données existantes...")
        db.drop_all()
        db.create_all()
        print("✅ Base de données réinitialisée\n")
        
        # Créer les données
        print("📝 Création des données de test...")
        admin = create_admin()
        clients = create_clients(20)
        maids = create_maids(30)
        
        print("\n📋 Création des demandes et messages...")
        requests = create_requests(clients, maids, 60)
        
        print("\n❤️  Création des favoris...")
        create_favorites(clients, maids)
        
        # Statistiques finales
        print("\n" + "="*50)
        print("📊 STATISTIQUES FINALES")
        print("="*50)
        print(f"👑 Admins : 1")
        print(f"👤 Clients : {len(clients)}")
        print(f"🧹 Aides ménagères : {len(maids)}")
        print(f"📋 Demandes : {len(requests)}")
        print(f"💬 Messages : {Message.query.count()}")
        print(f"⭐ Avis : {Review.query.count()}")
        print("="*50)
        
        print("\n🔑 COMPTES DE TEST :")
        print("="*50)
        print("👑 Admin : admin@maidconnect.com / admin123")
        print("👤 Client : client@demo.com / client123 (ou n'importe quel email client)")
        print("🧹 Maid : maid@demo.com / maid123 (ou n'importe quel email maid)")
        print("="*50)
        
        print("\n✅ SEEDING TERMINÉ AVEC SUCCÈS !")
        print("🚀 Lance 'python run.py' pour démarrer l'application\n")

if __name__ == '__main__':
    main()