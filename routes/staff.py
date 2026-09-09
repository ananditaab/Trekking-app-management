from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from extensions import db
from models import Trek, Booking

staff_bp = Blueprint("staff", __name__)


def staff_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))

        if current_user.role != "staff":
            flash("Staff access required.")
            return redirect(url_for("main.index"))

        return func(*args, **kwargs)

    return wrapper


@staff_bp.route("/")
@login_required
@staff_required
def dashboard():
    treks = Trek.query.filter_by(assigned_staff_id=current_user.id).all()

    assigned_treks = len(treks)

    participants = Booking.query.join(Trek).filter(
        Trek.assigned_staff_id == current_user.id
    ).count()

    completed = Trek.query.filter_by(
        assigned_staff_id=current_user.id,
        status="completed"
    ).count()

    return render_template(
        "staff_dashboard.html",
        assigned_treks=assigned_treks,
        participants=participants,
        completed=completed,
        treks=treks
    )


@staff_bp.route("/participants")
@login_required
@staff_required
def participants():
    bookings = Booking.query.join(Trek).filter(
        Trek.assigned_staff_id == current_user.id
    ).all()

    return render_template("participants.html", bookings=bookings)


@staff_bp.route("/update/<int:trek_id>", methods=["GET", "POST"])
@login_required
@staff_required
def update_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff_id != current_user.id:
        flash("You are not assigned to this trek.")
        return redirect(url_for("staff.dashboard"))

    if request.method == "POST":
        trek.status = request.form["status"]
        db.session.commit()
        flash("Trek updated successfully.")
        return redirect(url_for("staff.dashboard"))

    return render_template("update_trek.html", trek=trek)


@staff_bp.route("/complete/<int:trek_id>")
@login_required
@staff_required
def complete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff_id != current_user.id:
        flash("You cannot complete this trek.")
        return redirect(url_for("staff.dashboard"))

    trek.status = "completed"
    db.session.commit()

    flash("Trek completed successfully.")
    return redirect(url_for("staff.dashboard"))