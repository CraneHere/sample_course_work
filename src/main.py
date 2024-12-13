import streamlit as st
from frontend.frontend import (
    show_games_page, show_login_page, show_registration_page, 
    show_keys_page, show_profile_page, show_analyze_sales_page, 
    show_selling_products_page, show_admin_page, setup_shop_page
)
from database import connect_db
import bcrypt
import psycopg2
from settings import DB_CONFIG

def initialize_admin():
    try:
        # Подключение к базе данных
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Проверка, существует ли уже администратор
        cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1;")
        admin = cursor.fetchone()

        if admin:
            return "Admin user already exists."
        
        # Если администратора нет, создаем нового
        username = 'admin'
        password = 'admin_password'  # Вы можете задать здесь сложный пароль
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf8')

        cursor.execute("""
            INSERT INTO users (username, password, role) 
            VALUES (%s, %s, 'admin');
        """, (username, hashed_password))

        # Сохраняем изменения и закрываем соединение
        conn.commit()
        cursor.close()
        conn.close()

        return "Admin user created successfully."

    except Exception as e:
        return f"Error: {str(e)}"

def main():
    initialize_admin()
    # Проверка аутентификации
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    if not st.session_state['authenticated']:
        # Отображение логина или регистрации
        mode = st.sidebar.radio("Select mode", ["Login", "Register"])
        if mode == "Login":
            show_login_page()  # Показать страницу логина
        else:
            show_registration_page()  # Показать страницу регистрации
    else:
        # Интерфейс после входа
        st.sidebar.title(f"Welcome, {st.session_state['username']}!")
        role = st.session_state.get('role', 'buyer')

        # Навигация по страницам, которая зависит от роли
        pages = {
            "Games Management": show_games_page,
            "Selling Products": show_selling_products_page,
            "Sales Analysis": show_analyze_sales_page,
            "Key Buying": show_keys_page,
            "Profile": show_profile_page,
            "Admin Panel": show_admin_page,
            "Setup Your Shop": setup_shop_page  # Adding shop setup page
        }

        # Фильтруем доступные страницы в зависимости от роли
        accessible_pages = {}
        if role == "admin":
            accessible_pages = {name: page for name, page in pages.items() if name in ["Admin Panel", "Games Management"]}
        elif role == "seller":
            accessible_pages = {name: page for name, page in pages.items() if name in ["Selling Products", "Sales Analysis", "Profile", "Setup Your Shop"]}
        elif role == "buyer":
            accessible_pages = {name: page for name, page in pages.items() if name in ["Key Buying", "Profile"]}

        # Отображение навигации для доступных страниц
        page_name = st.sidebar.radio("Navigation", list(accessible_pages.keys()))

        # Показать соответствующую страницу
        accessible_pages[page_name]()  

if __name__ == "__main__":
    main()
