from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_

from extensions import db
from models import Trek, User, Booking

admin_bp = Blueprint("admin", __name__)
from datetime import datetime


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))

        if current_user.role != "admin":
            flash("Admin access required.")
            return redirect(url_for("main.index"))

        return func(*args, **kwargs)

    return wrapper


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role="user").count()
    total_staff = User.query.filter_by(role="staff").count()
    total_bookings = Booking.query.count()
    treks = Trek.query.all()

    return render_template(
        "admin_dashboard.html",
        total_treks=total_treks,
        total_users=total_users,
        total_staff=total_staff,
        total_bookings=total_bookings,
        treks=treks
    )


@admin_bp.route("/manage-users")
@login_required
@admin_required
def manage_users():
    search = request.args.get("search", "").strip()

    users_query = User.query.filter_by(role="user")

    if search:
        users_query = users_query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.phone.ilike(f"%{search}%"),
                User.id.cast(db.String).ilike(f"%{search}%")
            )
        )

    users = users_query.all()

    return render_template("manage_users.html", users=users, search=search)


@admin_bp.route("/blacklist-user/<int:user_id>")
@login_required
@admin_required
def blacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    user.status = "blacklisted"
    db.session.commit()
    flash("User blacklisted successfully.")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/manage-staff")
@login_required
@admin_required
def manage_staff():
    search = request.args.get("search", "").strip()

    staff_query = User.query.filter_by(role="staff")

    if search:
        staff_query = staff_query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.phone.ilike(f"%{search}%"),
                User.id.cast(db.String).ilike(f"%{search}%")
            )
        )

    staff_members = staff_query.all()

    return render_template(
        "manage_staff.html",
        staff_members=staff_members,
        search=search
    )


@admin_bp.route("/approve-staff/<int:user_id>")
@login_required
@admin_required
def approve_staff(user_id):
    staff = User.query.get_or_404(user_id)
    staff.status = "approved"
    db.session.commit()
    flash("Staff approved successfully.")
    return redirect(url_for("admin.manage_staff"))


@admin_bp.route("/blacklist-staff/<int:user_id>")
@login_required
@admin_required
def blacklist_staff(user_id):
    staff = User.query.get_or_404(user_id)
    staff.status = "blacklisted"
    db.session.commit()
    flash("Staff blacklisted successfully.")
    return redirect(url_for("admin.manage_staff"))


@admin_bp.route("/manage-treks")
@login_required
@admin_required
def manage_treks():
    search = request.args.get("search", "").strip()

    treks_query = Trek.query

    if search:
        treks_query = treks_query.filter(
            or_(
                Trek.name.ilike(f"%{search}%"),
                Trek.location.ilike(f"%{search}%"),
                Trek.status.ilike(f"%{search}%"),
                Trek.id.cast(db.String).ilike(f"%{search}%")
            )
        )

    treks = treks_query.all()
    staff_members = User.query.filter_by(role="staff", status="approved").all()

    return render_template(
        "manage_treks.html",
        treks=treks,
        staff_members=staff_members,
        search=search
    )

@admin_bp.route("/add-trek", methods=["GET", "POST"])
@login_required
@admin_required
def add_trek():
    if request.method == "POST":
        name = request.form["name"]
        location = request.form["location"]
        difficulty = request.form["difficulty"]
        duration = int(request.form["duration"])
        total_slots = int(request.form["total_slots"])
        start_date = datetime.strptime(request.form["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(request.form["end_date"], "%Y-%m-%d").date()
        description = request.form["description"]
        status = request.form["status"]

        trek = Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            duration=duration,
            total_slots=total_slots,
            available_slots=total_slots,
            start_date=start_date,
            end_date=end_date,
            description=description,
            status=status
        )

        db.session.add(trek)
        db.session.commit()

        flash("New trek added successfully.")
        return redirect(url_for("admin.dashboard"))

    return render_template("add_trek.html")

@admin_bp.route("/assign-staff/<int:trek_id>", methods=["POST"])
@login_required
@admin_required
def assign_staff(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    staff_id = request.form.get("staff_id")

    if staff_id:
        trek.assigned_staff_id = int(staff_id)
        db.session.commit()
        flash("Staff assigned successfully.")

    return redirect(url_for("admin.manage_treks"))


@admin_bp.route("/edit-trek/<int:trek_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if request.method == "POST":
        trek.name = request.form["name"]
        trek.location = request.form["location"]
        trek.difficulty = request.form["difficulty"]
        trek.duration = int(request.form["duration"])
        trek.total_slots = int(request.form["total_slots"])
        trek.available_slots = int(request.form["available_slots"])
        trek.status = request.form["status"]
        trek.description = request.form["description"]

        db.session.commit()
        flash("Trek updated successfully.")
        return redirect(url_for("admin.manage_treks"))

    return render_template("update_trek.html", trek=trek)


@admin_bp.route("/delete-trek/<int:trek_id>")
@login_required
@admin_required
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    db.session.delete(trek)
    db.session.commit()
    flash("Trek deleted successfully.")
    return redirect(url_for("admin.manage_treks"))