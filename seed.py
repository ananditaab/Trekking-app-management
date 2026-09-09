from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from models import User

ADMIN_NAME = "Admin"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "12345"
ADMIN_PHONE = "9876543210"
ADMIN_AGE = 20


def seed_admin():
    admin = User.query.filter_by(email=ADMIN_EMAIL).first()

    if admin:
        print("Admin account already exists.")
        return

    admin = User(
        name=ADMIN_NAME,
        age=ADMIN_AGE,
        email=ADMIN_EMAIL,
        phone=ADMIN_PHONE,
        password=generate_password_hash(ADMIN_PASSWORD),
        role="admin",
        status="approved"
    )

    db.session.add(admin)
    db.session.commit()

    print("Admin account created successfully.")
    print(f"Email: {ADMIN_EMAIL}")
    print(f"Password: {ADMIN_PASSWORD}")


if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        db.create_all()
        seed_admin()