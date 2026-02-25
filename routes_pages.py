from flask import Blueprint, render_template, redirect, url_for

pages_bp = Blueprint("pages", __name__)

@pages_bp.get("/")
def home():
    return redirect(url_for("pages.chat_page"))

@pages_bp.get("/chat")
def chat_page():
    return render_template("chat.html")

@pages_bp.get("/briefing")
def briefing_page():
    return render_template("briefing.html")

@pages_bp.get("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")