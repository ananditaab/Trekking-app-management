from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        name = request.form["name"]
        age = int(request.form["age"])
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        role = request.form.get("role", "user")

        if User.query.filter_by(email=email).first():
            flash("Email already exists.")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(phone=phone).first():
            flash("Phone number already exists.")
            return redirect(url_for("auth.register"))

        user = User(
            name=name,
            age=age,
            email=email,
            phone=phone,
            password=generate_password_hash(password),
            role=role,
            status="approved" if role == "user" else "pending"
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration Successful!")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        elif current_user.role == "staff":
            return redirect(url_for("staff.dashboard"))
        return redirect(url_for("user.dashboard"))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if user.status == "blacklisted":
                flash("Your account has been blacklisted.")
                return redirect(url_for("auth.login"))

            if user.role == "staff" and user.status != "approved":
                flash("Your staff account is waiting for admin approval.")
                return redirect(url_for("auth.login"))

            login_user(user)
            flash("Login Successful")

            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            elif user.role == "staff":
                return redirect(url_for("staff.dashboard"))
            return redirect(url_for("user.dashboard"))

        flash("Invalid Email or Password")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged Out Successfully")
    return redirect(url_for("auth.login"))