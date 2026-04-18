cat > README.md << 'EOF'
# 🧹 MaidConnect

Plateforme de mise en relation entre employeurs et aides ménagères.

## 🚀 Fonctionnalités

- 👥 **3 types d'utilisateurs** : Admin, Client, Aide ménagère
- 🔍 **Recherche avancée** : Ville, tarif, langues, disponibilité
- 💬 **Messagerie interne** sécurisée
- ⭐ **Système de notation et avis**
- ✅ **Vérification d'identité** par les administrateurs
- 📸 **Upload de photos de profil**
- 🌙 **Mode sombre/clair**

## 🛠️ Technologies

- **Backend** : Flask (Python) + SQLAlchemy
- **Base de données** : SQLite (dev) / PostgreSQL (prod)
- **Frontend** : Tailwind CSS + Alpine.js
- **Auth** : Flask-Login + bcrypt

## 📦 Installation

```bash
# Cloner le dépôt
git clone https://github.com/TON_USERNAME/MaidConnect.git
cd MaidConnect

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sur Windows

# Installer les dépendances
pip install -r requirements.txt

# Créer les dossiers
mkdir -p instance app/static/uploads

# Lancer l'application
python run.py
