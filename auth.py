# ================= IMPORT KEAMANAN PASSWORD =================
# Digunakan untuk hashing password dan verifikasi password saat login
from werkzeug.security import generate_password_hash, check_password_hash

# Mengambil koneksi database
from database import get_connection

# ================= IMPORT FIREBASE =================
# Firebase Admin SDK untuk login Google
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

# ================= INIT FIREBASE =================
# Inisialisasi Firebase hanya sekali agar tidak error double init
if not firebase_admin._apps:
    # Memuat credential Firebase dari file JSON
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)

# ================= REGISTER USER =================
def register_user(username, email, password):
    # Membuka koneksi database
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Cek apakah email sudah terdaftar
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        conn.close()
        return "email_exists"

    # Cek apakah username sudah terdaftar
    cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
    if cursor.fetchone():
        conn.close()
        return "username_exists"

    # Hash password sebelum disimpan ke database
    password_hash = generate_password_hash(password)

    # Simpan user baru dengan role user
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, role) VALUES (%s,%s,%s,'user')",
        (username, email, password_hash)
    )
    conn.commit()  # Simpan perubahan
    conn.close()   # Tutup koneksi
    return "success"

# ================= REGISTER ADMIN =================
def register_admin(username, email, password, admin_secret):
    # Kunci rahasia untuk mencegah pembuatan admin sembarangan
    ADMIN_SECRET_KEY = "ADMIN_GYM_2025"

    # Validasi admin secret
    if admin_secret != ADMIN_SECRET_KEY:
        return "invalid_secret"

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Cek email admin
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        conn.close()
        return "email_exists"

    # Cek username admin
    cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
    if cursor.fetchone():
        conn.close()
        return "username_exists"

    # Hash password admin
    password_hash = generate_password_hash(password)

    # Simpan akun admin ke database
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, role) VALUES (%s,%s,%s,'admin')",
        (username, email, password_hash)
    )
    conn.commit()
    conn.close()
    return "success"

# ================= AUTH USER =================
def authenticate_user(username, password):
    # Ambil data user berdasarkan username
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id, password_hash, role FROM users WHERE username=%s",
        (username,)
    )
    user = cursor.fetchone()
    conn.close()

    # Jika user tidak ditemukan
    if not user:
        return None

    # Jika password tidak cocok
    if not check_password_hash(user["password_hash"], password):
        return None

    # Login berhasil, kembalikan data user
    return {
        "id": user["id"],
        "role": user["role"]
    }

# ================= AUTH ADMIN (STRICT) =================
def authenticate_admin(username, password):
    # Gunakan autentikasi user biasa
    user = authenticate_user(username, password)

    # Jika login gagal
    if not user:
        return None

    # Pastikan role adalah admin
    if user["role"] != "admin":
        return None

    # Login admin berhasil
    return user  # dict {id, role}

# ================= RESET PASSWORD =================
def reset_password(email):
    conn = get_connection()
    cursor = conn.cursor()

    # Cek apakah email ada di database
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    if not cursor.fetchone():
        conn.close()
        return False

    # Password default baru (untuk demo)
    new_password = "NewPass123"
    password_hash = generate_password_hash(new_password)

    # Update password user
    cursor.execute(
        "UPDATE users SET password_hash=%s WHERE email=%s",
        (password_hash, email)
    )
    conn.commit()
    conn.close()
    return True

# ================= FIREBASE LOGIN =================
def verify_firebase_token(id_token):
    # Verifikasi token Google dari Firebase
    decoded = firebase_auth.verify_id_token(id_token)

    # Ambil data user dari token Firebase
    firebase_uid = decoded["uid"]
    email = decoded.get("email")
    username = decoded.get("name") or email.split("@")[0]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Cegah konflik dengan akun manual (email sama tapi bukan Firebase)
    cursor.execute(
        "SELECT id FROM users WHERE email=%s AND firebase_uid IS NULL",
        (email,)
    )
    if cursor.fetchone():
        conn.close()
        raise Exception("EMAIL_ALREADY_EXISTS")

    # Cek apakah user Firebase sudah ada
    cursor.execute(
        "SELECT id FROM users WHERE firebase_uid=%s",
        (firebase_uid,)
    )
    user = cursor.fetchone()

    # Jika user sudah ada, langsung login
    if user:
        conn.close()
        return user["id"]

    # Jika belum ada, buat user baru dari Firebase
    cursor.execute(
        "INSERT INTO users (firebase_uid, email, username, role) VALUES (%s,%s,%s,'user')",
        (firebase_uid, email, username)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    return user_id
