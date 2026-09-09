from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import and_

from extensions import db
from models import Trek, Booking

user_bp = Blueprint("user", __name__)


@user_bp.route("/")
@login_required
def dashboard():
    search = request.args.get("search", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    location = request.args.get("location", "").strip()

    total_treks = Trek.query.count()

    booked_treks = Booking.query.filter_by(user_id=current_user.id).count()

    query = Trek.query.filter(Trek.available_slots > 0)

    if search:
        query = query.filter(Trek.name.ilike(f"%{search}%"))

    if difficulty:
        query = query.filter(Trek.difficulty == difficulty)

    if location:
        query = query.filter(Trek.location.ilike(f"%{location}%"))

    treks = query.all()
    available_treks = len(treks)

    return render_template(
        "user_dashboard.html",
        total_treks=total_treks,
        booked_treks=booked_treks,
        available_treks=available_treks,
        treks=treks,
        search=search,
        difficulty=difficulty,
        location=location
    )


@user_bp.route("/treks")
@login_required
def treks():
    treks = Trek.query.all()
    return render_template("user_treks.html", treks=treks)


@user_bp.route("/book/<int:trek_id>")
@login_required
def book_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    existing = Booking.query.filter_by(
        user_id=current_user.id,
        trek_id=trek.id
    ).first()

    if existing:
        flash("You have already booked this trek.")
        return redirect(url_for("user.dashboard"))

    if trek.available_slots <= 0:
        flash("No slots available.")
        return redirect(url_for("user.dashboard"))

    booking = Booking(
        user_id=current_user.id,
        trek_id=trek.id,
        status="Booked"
    )

    trek.available_slots -= 1

    db.session.add(booking)
    db.session.commit()

    flash("Booking successful!")
    return redirect(url_for("user.dashboard"))


@user_bp.route("/history")
@login_required
def history():
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template("history.html", bookings=bookings)


@user_bp.route("/cancel/<int:booking_id>")
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id:
        flash("Access denied")
        return redirect(url_for("user.dashboard"))

    booking.trek.available_slots += 1
    db.session.delete(booking)
    db.session.commit()

    flash("Booking cancelled")
    return redirect(url_for("user.history"))