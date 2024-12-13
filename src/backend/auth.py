import bcrypt

def authenticate_user(username, password, cursor):
    try:
        cursor.execute("SELECT username, password, role, id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if user:
            stored_password = user[1]
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                return {'role': user[2], 'user_id': user[3]}
        return None
    except Exception as e:
        print(f"Error during authentication: {e}")
        return None

def register_user(username, password, cursor, conn, role='buyer'):
    try:
        cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return False

        # Хэширование пароля
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf8')
        cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, hashed_password, role))
        conn.commit()

        if role == 'seller':
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user_id_result = cursor.fetchone()
            if user_id_result:
                user_id = user_id_result[0]
                cursor.execute("INSERT INTO pending_sellers (user_id) VALUES (%s)", (user_id,))
                conn.commit()
        return True
    except Exception as e:
        print(f"Error during registration: {e}")
        return False

