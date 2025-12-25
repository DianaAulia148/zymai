# Library untuk koneksi dan operasi database MySQL
import mysql.connector


# ================= KONFIGURASI DATABASE =================
# Berisi informasi koneksi ke database MySQL
DB_CONFIG = {
    "host": "localhost",              # Alamat server database
    "user": "root",                   # Username MySQL
    "password": "",                   # Password MySQL
    "database": "capstonewebgym",     # Nama database
    "port": 3306                      # Port default MySQL
}


# Fungsi untuk membuat dan mengembalikan koneksi database
def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


# ================= INIT DB =================
def init_db():
    """
    Fungsi untuk inisialisasi database.
    Membuat tabel users dan feedback jika belum ada.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # ===== TABEL USERS =====
    # Menyimpan data akun user dan admin
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,     -- ID user
            username VARCHAR(100),                 -- Username
            email VARCHAR(100) UNIQUE NOT NULL,    -- Email (unik)
            password_hash TEXT NULL,               -- Password hash (login manual)
            firebase_uid VARCHAR(128) UNIQUE,      -- UID Firebase (login Google)
            role ENUM('user','admin') DEFAULT 'user', -- Role user
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Waktu registrasi
        )
    """)

    # ===== TABEL FEEDBACK =====
    # Menyimpan feedback/ulasan dari user
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INT AUTO_INCREMENT PRIMARY KEY,     -- ID feedback
            user_id INT NOT NULL,                  -- ID user pemberi feedback
            name VARCHAR(100),                     -- Nama pengirim
            email VARCHAR(100),                    -- Email pengirim
            message TEXT,                          -- Isi feedback
            rating INT CHECK (rating BETWEEN 1 AND 5), -- Rating 1–5
            sentiment VARCHAR(20),                 -- Sentimen (Positive/Neutral/Negative)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Waktu input
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Simpan perubahan dan tutup koneksi
    conn.commit()
    conn.close()


# ================= CEK ADMIN =================
def is_admin(user_id):
    """
    Mengecek apakah user dengan user_id tertentu adalah admin
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT role FROM users WHERE id=%s",
        (user_id,)
    )
    user = cursor.fetchone()
    conn.close()

    # Mengembalikan True jika role = admin
    return user and user["role"] == "admin"


# ================= USER =================
def get_user_by_username(username):
    """
    Mengambil data user berdasarkan username
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, role FROM users WHERE username=%s",
        (username,)
    )
    user = cursor.fetchone()
    conn.close()
    return user


def set_admin(user_id):
    """
    Mengubah role user menjadi admin
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET role='admin' WHERE id=%s",
        (user_id,)
    )
    conn.commit()
    conn.close()


def get_user_id(username):
    """
    Mengambil ID user berdasarkan username
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM users WHERE username=%s",
        (username,)
    )
    result = cursor.fetchone()
    conn.close()

    # Mengembalikan ID user jika ada
    return result[0] if result else None


def get_user_by_firebase_uid(firebase_uid):
    """
    Mengambil ID user berdasarkan Firebase UID
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM users WHERE firebase_uid=%s",
        (firebase_uid,)
    )
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None


def create_firebase_user(firebase_uid, email, username):
    """
    Membuat user baru dari login Firebase (Google)
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO users (firebase_uid, email, username)
        VALUES (%s, %s, %s)
        """,
        (firebase_uid, email, username)
    )

    conn.commit()
    user_id = cursor.lastrowid  # Ambil ID user terakhir
    conn.close()
    return user_id


# ================= SENTIMENT =================
def classify_sentiment(rating):
    """
    Mengklasifikasikan sentimen berdasarkan rating
    """
    if rating >= 4:
        return "Positive"
    elif rating == 3:
        return "Neutral"
    else:
        return "Negative"


# ================= FEEDBACK =================
def save_feedback(user_id, name, email, message, rating):
    """
    Menyimpan feedback user ke database
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO feedback (user_id, name, email, message, rating, sentiment)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        user_id,
        name,
        email,
        message,
        rating,
        classify_sentiment(rating)  # Tentukan sentimen otomatis
    ))

    conn.commit()
    conn.close()


def get_latest_feedback(limit=20):
    """
    Mengambil feedback terbaru sesuai jumlah limit
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT name, email, message, rating, sentiment
        FROM feedback
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (limit,)
    )
    data = cursor.fetchall()
    conn.close()
    return data


def get_feedback_summary():
    """
    Mengambil ringkasan data feedback
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Total feedback
    cursor.execute("SELECT COUNT(*) AS total FROM feedback")
    total = cursor.fetchone()["total"]

    # Rata-rata rating
    cursor.execute("SELECT AVG(rating) AS avg_rating FROM feedback")
    avg_rating = cursor.fetchone()["avg_rating"] or 0

    # Jumlah rating 5
    cursor.execute("SELECT COUNT(*) AS r5 FROM feedback WHERE rating = 5")
    r5 = cursor.fetchone()["r5"]

    conn.close()

    return {
        "total_reviews": total,
        "avg_rating": round(avg_rating, 1),
        "r5": r5
    }
