from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from auth import (
    register_user,
    authenticate_user,
    authenticate_admin,
    reset_password,
    verify_firebase_token,
    register_admin
)

from database import (
    init_db,
    is_admin,
    save_feedback,
    get_latest_feedback,
    get_feedback_summary
)

from functools import wraps
from chatbot import get_chatbot_response
import json

app = Flask(__name__)
app.secret_key = "secret123"

# ================= ADMIN DECORATOR =================
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "admin":
            flash("Akses admin diperlukan", "error")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated


# ================= INIT DB =================
init_db()

# ================= LOAD WORKOUT =================
def load_workouts():
    with open("workouts.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ================= ROUTES =================
@app.route("/")
def index():
    feedbacks = get_latest_feedback(5)  # ambil 5 terbaru
    return render_template(
        "index.html",
        feedbacks=feedbacks
    )


@app.route("/home")
def home():
    if "user_id" not in session:
        flash("You must log in first!", "error")
        return redirect(url_for("login"))
    return render_template("home.html")

# ================= LOGIN USER =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = authenticate_user(
            request.form.get("username"),
            request.form.get("password")
        )

        if user:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("home"))

        flash("Username atau password salah", "error")

    return render_template("login.html")

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request harus JSON"
        }), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username dan password wajib diisi"
        }), 400

    # ✅ CEK USER
    user = authenticate_user(username, password)
    if user:
        session.clear()
        session["user_id"] = user["id"]
        session["role"] = "user"

        return jsonify({
            "success": True,
            "role": "user"
        }), 200

    # ✅ CEK ADMIN
    admin = authenticate_admin(username, password)
    if admin:
        session.clear()
        session["user_id"] = admin["id"]
        session["role"] = "admin"

        return jsonify({
            "success": True,
            "role": "admin"
        }), 200

    return jsonify({
        "success": False,
        "message": "Username atau password salah"
    }), 401

# ================= LOGIN ADMIN =================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        admin = authenticate_admin(username, password)
        if admin:
            session.clear()
            session["user_id"] = admin["id"]
            session["role"] = "admin"
            return redirect(url_for("admin_dashboard"))

        flash("Login admin gagal", "error")

    return render_template("admin/login.html")
@app.route("/api/admin/login", methods=["POST"])
def api_admin_login():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request harus JSON"
        }), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username dan password wajib diisi"
        }), 400

    admin = authenticate_admin(username, password)

    if not admin:
        return jsonify({
            "success": False,
            "message": "Login admin gagal"
        }), 401

    session.clear()
    session["user_id"] = admin["id"]
    session["role"] = "admin"

    return jsonify({
        "success": True,
        "role": "admin"
    }), 200



@app.route("/api/admin/signup", methods=["POST"])
def api_admin_signup():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request harus JSON"
        }), 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    admin_secret = data.get("admin_secret")

    if not all([username, email, password, admin_secret]):
        return jsonify({
            "success": False,
            "message": "Semua field wajib diisi"
        }), 400

    result = register_admin(
        username,
        email,
        password,
        admin_secret
    )

    if result == "success":
        return jsonify({
            "success": True,
            "message": "Admin berhasil dibuat"
        }), 201

    if result == "invalid_secret":
        return jsonify({
            "success": False,
            "message": "Admin secret salah"
        }), 403

    return jsonify({
        "success": False,
        "message": "Username atau email sudah terdaftar"
    }), 409


# ================= ADMIN DASHBOARD =================
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    return render_template(
        "admin/dashboard.html",
        feedbacks=get_latest_feedback(50),
        summary=get_feedback_summary()
    )

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("Logout admin berhasil", "success")
    return redirect(url_for("admin_login"))

# ================= LOGIN GOOGLE =================
@app.route("/login/firebase", methods=["POST"])
def login_firebase():
    print("🔥 /login/firebase HIT")
    data = request.get_json(force=True)
    id_token = data.get("idToken")

    try:
        user_id = verify_firebase_token(id_token)

        session.clear()
        session["user_id"] = user_id  # INTEGER

        return jsonify({"success": True})

    except Exception as e:
        print("Firebase login error:", e)
        return jsonify({
            "success": False,
            "error": "Login Google gagal"
        }), 401


# ================= SIGNUP USER =================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        if request.form.get("password") != request.form.get("re_password"):
            flash("Password tidak sama", "error")
            return redirect(url_for("signup"))

        result = register_user(
            request.form.get("username"),
            request.form.get("email"),
            request.form.get("password")
        )

        if result == "success":
            flash("Registrasi berhasil. Silakan login.", "success")
            return redirect(url_for("login"))

        flash("Registrasi gagal", "error")

    return render_template("signup.html")

@app.route("/api/signup", methods=["POST"])
def api_signup():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request harus JSON"
        }), 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    re_password = data.get("re_password")

    if not username or not email or not password:
        return jsonify({
            "success": False,
            "message": "Data tidak lengkap"
        }), 400

    if password != re_password:
        return jsonify({
            "success": False,
            "message": "Password tidak sama"
        }), 400

    result = register_user(username, email, password)

    if result == "success":
        return jsonify({
            "success": True,
            "message": "Registrasi berhasil"
        }), 201

    return jsonify({
        "success": False,
        "message": "Username atau email sudah terdaftar"
    }), 409

# ================= SIGNUP ADMIN =================
@app.route("/admin/signup", methods=["GET", "POST"])
def admin_signup():
    if request.method == "POST":
        if request.form.get("password") != request.form.get("confirm_password"):
            flash("Password tidak sama", "error")
            return redirect(url_for("admin_signup"))

        result = register_admin(
            request.form.get("username"),
            request.form.get("email"),
            request.form.get("password"),
            request.form.get("admin_secret")
        )

        if result == "success":
            flash("Admin berhasil dibuat, silakan login", "success")
            return redirect(url_for("admin_login"))

        flash("Registrasi admin gagal", "error")

    return render_template("admin/signup.html")

# ================= RESET PASSWORD =================
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        if reset_password(request.form.get("email")):
            flash("Password reset berhasil", "success")
            return redirect(url_for("login"))

        flash("Email tidak ditemukan", "error")

    return render_template("forgot_password.html")

# ================= BMI CALCULATOR =================
@app.route("/bmi", methods=["GET", "POST"])
def bmi_calculator():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        data = request.get_json()

        height_cm = float(data.get("height"))
        weight_kg = float(data.get("weight"))

        height_m = height_cm / 100
        bmi = round(weight_kg / (height_m ** 2), 2)

        if bmi < 18.5:
            category = "Underweight"
            recommendation = [
                "Light strength training",
                "Bodyweight squat",
                "Push-up (knee)",
                "Resistance band workout"
            ]
        elif bmi < 25:
            category = "Normal"
            recommendation = [
                "Full body workout",
                "Jogging 20–30 menit",
                "Push-up & plank",
                "Squat & lunges"
            ]
        elif bmi < 30:
            category = "Overweight"
            recommendation = [
                "Low impact cardio",
                "Brisk walking",
                "Cycling",
                "Bodyweight circuit ringan"
            ]
        else:
            category = "Obese"
            recommendation = [
                "Walking rutin",
                "Stretching",
                "Low impact cardio",
                "Yoga atau mobility training"
            ]

        return jsonify({
            "success": True,
            "bmi": bmi,
            "category": category,
            "recommendation": recommendation
        })

    return render_template("bmi.html")


# ================= CHATBOT =================
@app.route("/chatbot")
def chatbot():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("chatbot.html")

@app.route("/send_message", methods=["POST"])
def send_message():
    return jsonify({
        "response": get_chatbot_response(request.get_json()["message"])
    })

# ================= FEEDBACK =================
@app.route("/api/feedback", methods=["POST"])
@login_required
def api_feedback():
    data = request.get_json()

    save_feedback(
        session["user_id"],
        data["name"],
        data["email"],
        data["message"],
        int(data["rating"])
    )

    return jsonify({"message": "Feedback berhasil dikirim"})


@app.route("/api/feedback/latest")
def api_latest_feedback():
    return jsonify(get_latest_feedback(10))


@app.route("/api/feedback/summary")
def api_feedback_summary():
    return jsonify(get_feedback_summary())


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ================= RUN =================
print("🔥 FLASK FILE AKTIF:", __file__)


if __name__ == "__main__":
    app.run(debug=True)
