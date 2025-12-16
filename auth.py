from werkzeug.security import generate_password_hash, check_password_hash
from database import get_connection

def register_user(username, email, password):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE username=%s OR email=%s",
            (username, email)
        )

        if cursor.fetchone():
            return False

        password_hash = generate_password_hash(password)

        cursor.execute(
            "INSERT INTO users (username,email,password_hash) VALUES (%s,%s,%s)",
            (username, email, password_hash)
        )

        conn.commit()
        return True

    except Exception as e:
        print("REGISTER ERROR:", e)
        return False

    finally:
        if conn:
            conn.close()

def authenticate_user(username, password):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password_hash FROM users WHERE username=%s",
            (username,)
        )
        user = cursor.fetchone()
        return user and check_password_hash(user[0], password)

    except Exception as e:
        print("LOGIN ERROR:", e)
        return False

    finally:
        if conn:
            conn.close()

def reset_password(email):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        if not cursor.fetchone():
            return False

        new_password = "NewPass123"
        password_hash = generate_password_hash(new_password)

        cursor.execute(
            "UPDATE users SET password_hash=%s WHERE email=%s",
            (password_hash, email)
        )

        conn.commit()
        return True

    except Exception as e:
        print("RESET ERROR:", e)
        return False

    finally:
        if conn:
            conn.close()
def get_or_create_google_user(google_id, email, username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, google_id FROM users WHERE email=%s",
        (email,)
    )
    user = cursor.fetchone()

    if user:
        user_id, existing_google_id = user

        if existing_google_id is None:
            cursor.execute(
                "UPDATE users SET google_id=%s WHERE id=%s",
                (google_id, user_id)
            )
            conn.commit()

        conn.close()
        return user_id

    cursor.execute(
        "INSERT INTO users (username, email, google_id) VALUES (%s,%s,%s)",
        (username, email, google_id)
    )

    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id
