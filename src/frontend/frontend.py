import streamlit as st
import pandas as pd
from psycopg2 import connect
from settings import DB_CONFIG
from psycopg2.extras import RealDictCursor
from database import connect_db
from backend.auth import authenticate_user, register_user
from backend.backend import get_games_by_seller, delete_game, get_platforms, add_game
from backend.backend import get_sales_statistics, get_games
from backend.backend import get_available_keys
from backend.backend import get_seller_games
from backend.backend import create_shop
from backend.backend import delete_user
from backend.backend import purchase_key, fetch_available_keys
from backend.backend import add_product_to_sales_table, clear_sales_table, upload_sales, get_products, get_platform_options, get_keys_for_seller, add_key_to_db

def show_admin_page():
    """Страница для администратора."""
    if 'user_id' not in st.session_state or st.session_state['user_id'] is None:
        st.error("You are not logged in.")
        return

    user_role = st.session_state.get('role')
    
    if user_role != 'admin':
        st.error("Access restricted to administrators only.")
        return

    st.title("Admin Panel")
    
    # Список пользователей, которых администратор может удалить
    users = get_all_users()  # Эта функция должна возвращать всех пользователей из базы данных
    
    if users:
        user_to_delete = st.selectbox("Select user to delete", users, format_func=lambda u: u['username'])
        if st.button(f"Delete User {user_to_delete['username']}"):
            try:
                # Удаление пользователя через сервис
                delete_user(st.session_state['user_id'], user_to_delete['id'])
                st.success(f"User {user_to_delete['username']} has been deleted.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.write("No users found.")
        
def get_all_users():
    """Получить всех пользователей для отображения на панели администратора."""
    with connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, username FROM users;")
            users = cur.fetchall()
    return users

def show_keys_page():
    """Frontend function to show available keys and handle purchases."""
    if 'user_id' not in st.session_state or st.session_state['user_id'] is None:
        st.error("You are not logged in.")
        return

    user_role = st.session_state.get('role')

    if user_role == 'buyer':
        st.title("Key Management - Buyer")
        st.write("View and purchase available game keys.")

        # Fetch keys from the backend
        keys = fetch_available_keys()

        if keys:
            # Convert keys list to DataFrame
            keys_df = pd.DataFrame(keys)

            # Display the available keys with prices
            st.dataframe(keys_df[['key_value', 'game_title', 'platform_name', 'shop_name', 'price']])

            # Select a key to purchase
            selected_key = st.selectbox("Select a key to purchase", [key['key_value'] for key in keys])

            # Get selected key details
            selected_key_data = next(key for key in keys if key['key_value'] == selected_key)

            # Show key details including the price
            st.write(f"Key to purchase: {selected_key_data['key_value']}")
            st.write(f"Game: {selected_key_data['game_title']}")
            st.write(f"Platform: {selected_key_data['platform_name']}")
            st.write(f"Shop: {selected_key_data['shop_name']}")
            st.write(f"Price: {selected_key_data['price']}")

            # Trigger purchase logic when the buyer clicks the "Purchase" button
            if st.button("Purchase Key"):
                success = purchase_key(st.session_state['user_id'], selected_key_data['key_id'])

                if success is True:
                    st.success(f"Successfully purchased the key for {selected_key_data['game_title']}.")
                else:
                    st.error(f"An error occurred during the purchase: {success}")

        else:
            st.write("No keys available.")
    
    else:
        st.error("Access restricted to authenticated users only.")

def show_profile_page():
    st.title("Profile")
    if 'user_id' not in st.session_state or st.session_state['user_id'] is None:
        st.error("You are not logged in.")
        return

    games = get_seller_games(st.session_state['user_id'])
    if games:
        st.dataframe(games)
    else:
        st.write("No games found for this seller.")

def show_games_page():
    if 'user_id' not in st.session_state or st.session_state['user_id'] is None:
        st.error("You are not logged in.")
        return

    if st.session_state.get('role') != 'admin':
        st.error("Access restricted to admins only.")
        return

    st.title("Games Management")
    st.write("Manage your games here.")

    # Отображение существующих игр
    games = get_games_by_seller(st.session_state['user_id'])
    if games:
        st.dataframe(games)

        for game in games:
            if st.button(f"Delete {game['title']}", key=f"delete_{game['game_id']}"):
                result = delete_game(game['game_id'])
                if result is True:
                    st.success(f"Game '{game['title']}' deleted successfully!")
                    st.experimental_rerun()
                else:
                    st.error(f"Error deleting the game: {result}")
    else:
        st.write("No games available.")

    # Добавление новой игры
    st.header("Add a New Game")
    platforms = get_platforms()
    platform_options = {platform['name']: platform['platform_id'] for platform in platforms}

    with st.form("add_game_form", clear_on_submit=True):
        title = st.text_input("Game Title")
        publisher = st.text_input("Publisher")
        genre = st.text_input("Genre")
        release_date = st.date_input("Release Date")
        platform_name = st.selectbox("Platform", list(platform_options.keys()))
        submit_button = st.form_submit_button("Add Game")

        if submit_button:
            platform_id = platform_options[platform_name]
            result = add_game(title, publisher, genre, platform_id, release_date, st.session_state['user_id'])
            if result is True:
                st.success(f"Game '{title}' added successfully!")
                st.rerun()
            else:
                st.error(f"Error adding the game: {result}")

def setup_shop_page():
    if 'user_id' not in st.session_state or st.session_state['user_id'] is None:
        st.error("You are not logged in.")
        return

    if st.session_state.get('role') != 'seller':
        st.error("Access restricted to sellers only.")
        return

    st.title("Setup Your Shop")
    st.write("Provide details about your shop to get started.")

    shop_name = st.text_input("Shop Name", max_chars=255)

    if st.button("Create Shop"):
        if not shop_name.strip():
            st.error("Shop name cannot be empty.")
            return

        # Call the backend function to create the shop
        result = create_shop(st.session_state['user_id'], shop_name)
        
        if "successfully" in result:
            st.success(result)
        else:
            st.error(result)

def show_login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username and password:
            with connect_db() as conn:
                with conn.cursor() as cur:
                    user_info = authenticate_user(username, password, cur)
                    if user_info:
                        st.session_state['authenticated'] = True
                        st.session_state['username'] = username
                        st.session_state['role'] = user_info['role']
                        st.session_state['user_id'] = user_info['user_id']
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
        else:
            st.error("Please fill out both fields.")

def show_registration_page():
    """
    Отображение страницы регистрации.
    """
    st.title("Register")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    role = st.selectbox("Role", ["buyer", "seller"])

    if password != confirm_password:
        st.warning("Passwords do not match.")

    if st.button("Register"):
        if username and password and password == confirm_password:
            with connect_db() as conn:
                with conn.cursor() as cur:
                    success = register_user(username, password, cur, conn, role)
                    if success:
                        st.success("Registration successful!")
                        st.rerun()
                    else:
                        st.error("Registration failed. Username might already be taken.")
        else:
            st.error("All fields are required and passwords must match.")

def show_analyze_sales_page():
    # Check if the user is logged in and ensure the role is 'seller'
    if 'user_id' not in st.session_state or st.session_state['user_id'] is None:
        st.error("You are not logged in.")
        return

    # Restrict access to sellers only
    if st.session_state.get('role') != 'seller':
        st.error("Access restricted to sellers only.")
        return

    st.title("Анализ продаж")

    # Fetch available games from the backend
    games = get_games()

    if not games:
        st.warning("Нет данных о играх для отображения.")
        return

    products = {game["title"]: game["game_id"] for game in games}

    selected_product = st.selectbox("Выберите игру", products.keys())

    if selected_product:
        selected_product_id = products[selected_product]

        # Fetch sales data for the selected game
        sales_data = get_sales_statistics(selected_product_id)

        if sales_data.empty:
            st.warning("Нет продаж для выбранного продукта.")
        else:
            display_option = st.radio("Отображать как", ["Таблица", "График"])

            if display_option == "Таблица":
                st.dataframe(sales_data)
            elif display_option == "График":
                if len(sales_data) > 1:
                    # Sort by sale_date and plot the graph
                    sales_data_sorted = sales_data.sort_values(by="sale_date")
                    st.line_chart(sales_data_sorted.set_index("sale_date")[["sold_keys_count"]])
                else:
                    # Warning when there is only one sale
                    st.warning("Только одна продажа для отображения графика.")

def show_selling_products_page():
    # Check if the user is a seller
    if st.session_state.get('role') != 'seller':
        st.error("Access restricted to sellers only.")
        return  # Exit the function if the user is not a seller

    st.title("Управление продажей ")

    platform_options = get_platform_options()

    st.subheader("Управление ключами")
    keys = get_keys_for_seller(st.session_state['user_id'])

    if keys:
        keys_df = pd.DataFrame(keys)
        st.dataframe(keys_df[['key_value', 'game_title', 'platform_name', 'status', 'price']])
    else:
        st.write("Нет доступных ключей.")

    st.subheader("Добавить новый ключ")
    key_value = st.text_input("Ключ", key="key_input_1")

    games = list(get_products().keys())
    game_title = st.selectbox("Игра", games, key="game_select_1")
    status = st.selectbox("Статус", ["available", "sold"], key="status_select_1")

    selected_platform_name_for_key = st.selectbox("Выберите платформу для ключа", list(platform_options.keys()))

    price = st.number_input("Цена", min_value=0.0, step=0.01, key="price_input_1")

    if st.button("Добавить ключ", key="add_key_button_1"):
        if key_value and game_title and status and selected_platform_name_for_key and price > 0:
            success = add_key_to_db(
                key_value,
                game_title,
                status,
                selected_platform_name_for_key,
                st.session_state['user_id'],
                price,
                start_date=pd.Timestamp.now()
            )
            if success:
                st.success("Ключ добавлен успешно!")
            else:
                st.error("Игра или платформа не найдены.")
        else:
            st.error("Все поля обязательны для заполнения и цена должна быть больше 0.")


