from app import app, db
from models import User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

with app.app_context():
    user = User.query.filter_by(username='demo').first()
    if not user:
        hashed_pw = bcrypt.generate_password_hash('demo').decode('utf-8')
        new_user = User(username='demo', password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        print("Usuario demo creado exitosamente.")
    else:
        print("El usuario demo ya existe.")
