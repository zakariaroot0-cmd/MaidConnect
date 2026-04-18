import os
from dotenv import load_dotenv
load_dotenv()
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-prod'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(os.getcwd(), 'instance', 'maidconnect.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max

     # Email config
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'anass.pronto@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'jymcppngrjrdlaus'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'anass.pronto@gmail.com'
       # Token expiration (30 minutes)
    RESET_TOKEN_EXPIRATION = 1800