from app import app
from entities.models import db

with app.app_context():
    db.create_all()
