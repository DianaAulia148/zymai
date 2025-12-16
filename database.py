import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "capstonewebgym",
    "port": 3306
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workout_preferences (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            goal VARCHAR(100),
            target_muscle VARCHAR(100),
            location VARCHAR(100),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()

def get_user_id(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def save_workout_preferences(user_id, goal, target_muscle, location):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO workout_preferences (user_id, goal, target_muscle, location) VALUES (%s,%s,%s,%s)",
        (user_id, goal, target_muscle, location)
    )
    conn.commit()
    conn.close()
def save_feedback(user_id, name, email, message, rating):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO feedback (user_id, name, email, message, rating)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, name, email, message, rating))

    conn.commit()
    conn.close()


def get_latest_feedback(limit=20):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT name, email, message, rating
        FROM feedback
        ORDER BY created_at DESC
        LIMIT %s
    """, (limit,))

    data = cursor.fetchall()
    conn.close()
    return data


def get_feedback_summary():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) total FROM feedback")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT AVG(rating) avg_rating FROM feedback")
    avg_rating = cursor.fetchone()["avg_rating"] or 0

    cursor.execute("SELECT COUNT(*) r5 FROM feedback WHERE rating = 5")
    r5 = cursor.fetchone()["r5"]

    conn.close()

    return {
        "total_reviews": total,
        "avg_rating": round(avg_rating, 1),
        "r5": r5
    }
