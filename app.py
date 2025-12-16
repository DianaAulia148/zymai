from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from auth import register_user, authenticate_user, reset_password, get_or_create_google_user
from database import (
    init_db,
    get_user_id,
    save_workout_preferences,
    save_feedback,
    get_latest_feedback,
    get_feedback_summary
)
from flask_dance.contrib.google import make_google_blueprint, google
from chatbot import get_chatbot_response
import json

app = Flask(__name__)
app.secret_key = "secret123"

# ================= INIT DB =================
init_db()

# ================= LOAD WORKOUT =================
def load_workouts():
    with open("workouts.json") as f:
        return json.load(f)

# ================= GOOGLE OAUTH =================
google_bp = make_google_blueprint(
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    scope=["profile", "email"]
)
app.register_blueprint(google_bp, url_prefix="/login")

# ================= ROUTES =================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home")
def home():
    if "user_id" not in session:
        flash("You must log in first!", "error")
        return redirect(url_for("login"))
    return render_template("home.html")

# ================= LOGIN MANUAL =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if authenticate_user(username, password):
            session["user_id"] = get_user_id(username)
            return redirect(url_for("home"))

        flash("Login gagal", "error")
    return render_template("login.html")

# ================= LOGIN GOOGLE =================
@app.route("/login/google")
def login_google():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Gagal mengambil data Google", "error")
        return redirect(url_for("login"))

    info = resp.json()
    google_id = info.get("id")
    email = info.get("email")
    username = info.get("name") or email.split("@")[0]

    if not google_id or not email:
        flash("Data Google tidak valid", "error")
        return redirect(url_for("login"))

    user_id = get_or_create_google_user(google_id, email, username)
    session["user_id"] = user_id

    return redirect(url_for("home"))

# ================= SIGNUP =================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        if register_user(
            request.form["username"],
            request.form["email"],
            request.form["password"]
        ):
            return redirect(url_for("login"))

        flash("Username atau Email sudah terdaftar", "error")
    return render_template("signup.html")

# ================= RESET PASSWORD =================
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        if reset_password(email):
            flash("Password reset berhasil. Password baru: NewPass123", "success")
            return redirect(url_for("login"))
        flash("Email tidak ditemukan", "error")

    return render_template("forgot_password.html")

# ================= WORKOUT =================
@app.route("/workout_suggestion", methods=["GET", "POST"])
def workout_suggestion():
    if "user_id" not in session:
        return redirect(url_for("login"))

    workouts = load_workouts()

    if request.method == "POST":
        goal = request.form.get("goal")
        target_muscle = request.form.get("target_muscle")
        location = request.form.get("location")

        if not all([goal, target_muscle, location]):
            flash("Semua field wajib diisi", "error")
            return redirect(url_for("workout_suggestion"))

        save_workout_preferences(session["user_id"], goal, target_muscle, location)

        try:
            workout_list = workouts[location][goal][target_muscle]
            return render_template(
                "workout_suggestion.html",
                workouts=workout_list,
                goal=goal,
                target_muscle=target_muscle,
                location=location
            )
        except KeyError:
            flash("Workout tidak ditemukan", "error")

    return render_template("workout_suggestion.html")

# ================= CHATBOT =================
@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

@app.route("/send_message", methods=["POST"])
def send_message():
    return jsonify({"response": get_chatbot_response(request.json["message"])})

# ================= FEEDBACK API =================
@app.route("/api/feedback", methods=["POST"])
def api_feedback():
    if "user_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.json
    save_feedback(
        session["user_id"],
        data["name"],
        data["email"],
        data["message"],
        data["rating"]
    )
    return jsonify({"message": "Feedback berhasil dikirim"})

@app.route("/api/feedback/latest")
def api_feedback_latest():
    return jsonify(get_latest_feedback())

@app.route("/api/feedback/summary")
def api_feedback_summary():
    return jsonify(get_feedback_summary())

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
