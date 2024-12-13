import psycopg2
import pandas as pd
from psycopg2 import extras
from psycopg2.extras import RealDictCursor
from datetime import date
import random
from datetime import datetime
from services.sales import SalesService
from database import connect_db
from psycopg2 import connect, extras
from settings import DB_CONFIG

def delete_user(admin_id, target_user_id):
        """Удаление пользователя администратором."""
        with connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                # Вызов функции delete_user на базе данных
                cur.execute("SELECT delete_user(%s, %s);", (admin_id, target_user_id))
                conn.commit()

def get_sales_statistics(game_id):
    """Fetch sales statistics for a specific game."""
    with connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    s.sale_date,
                    g.title AS game_title,
                    pl.name AS platform_name,
                    COUNT(k.key_id) AS sold_keys_count,
                    SUM(pr.price) AS total_revenue
                FROM
                    sales s
                    JOIN sales_details sd ON s.sale_id = sd.sale_id
                    JOIN keys k ON sd.key_id = k.key_id
                    JOIN games g ON k.game_id = g.game_id
                    JOIN platforms pl ON g.platform_id = pl.platform_id
                    JOIN prices pr ON g.game_id = pr.barcode
                WHERE
                    g.game_id = %s
                    AND s.sale_date BETWEEN pr.start_date AND COALESCE(pr.end_date, '5999-12-31'::date)
                GROUP BY
                    s.sale_date, g.title, pl.name
                ORDER BY s.sale_date;
            """, (game_id,))
            results = cur.fetchall()
    
    if results:
        df = pd.DataFrame(results)
        # Ensure the 'sale_date' column is parsed correctly as a datetime
        df['sale_date'] = pd.to_datetime(df['sale_date'])
        return df
    else:
        return pd.DataFrame()

def get_games():
    """Fetch all games from the database."""
    with connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("SELECT game_id, title FROM games ORDER BY title;")
            games = cur.fetchall()
    return games


def get_available_keys():
    """Fetch available game keys from the database."""
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT s.shop_id, s.name AS shop_name, g.title, k.key_value, k.status, p.name AS platform
                FROM keys k
                JOIN games g ON k.game_id = g.game_id
                JOIN platforms p ON g.platform_id = p.platform_id
                JOIN shop_keys sk ON k.key_id = sk.key_id
                JOIN shops s ON sk.shop_id = s.shop_id
                WHERE k.status = 'available';
            """)
            keys = cur.fetchall()
    return keys

def create_shop(user_id, shop_name):
    try:
        with connect_db() as conn:
            with conn.cursor(cursor_factory=extras.DictCursor) as cur:
                # Check if the seller already has a shop
                cur.execute("""
                    SELECT shop_id FROM shops WHERE seller_id = %s
                """, (user_id,))
                existing_shop = cur.fetchone()

                if existing_shop:
                    return "You already have a shop."

                # Insert the new shop into the database
                cur.execute("""
                    INSERT INTO shops (seller_id, name) 
                    VALUES (%s, %s)
                    RETURNING shop_id;
                """, (user_id, shop_name))
                shop_id = cur.fetchone()['shop_id']

                # Remove the user from the pending sellers list
                cur.execute("""
                    DELETE FROM pending_sellers WHERE user_id = %s;
                """, (user_id,))

                conn.commit()

                return f"Shop '{shop_name}' has been created successfully!"
    except Exception as e:
        return f"An error occurred: {e}"

def get_seller_games(user_id):
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT g.title, p.name AS platform, g.genre, g.release_date 
                FROM games g
                JOIN platforms p ON g.platform_id = p.platform_id
                JOIN shop_games sg ON sg.game_id = g.game_id
                JOIN shops s ON sg.shop_id = s.shop_id
                WHERE s.seller_id = %s;
            """, (user_id,))
            games = cur.fetchall()
            return games

def get_games_by_seller(seller_id):
    """Получить игры, связанные с продавцом."""
    with connect_db() as conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT g.game_id, g.title, p.name AS platform, g.genre, g.release_date 
                FROM games g
                JOIN platforms p ON g.platform_id = p.platform_id
                JOIN shop_games sg ON sg.game_id = g.game_id
                JOIN shops s ON sg.shop_id = s.shop_id
                WHERE s.seller_id = %s;
            """, (seller_id,))
            return cur.fetchall()

def delete_game(game_id):
    """Удалить игру из базы данных."""
    with connect_db() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("DELETE FROM shop_games WHERE game_id = %s;", (game_id,))
                cur.execute("DELETE FROM games WHERE game_id = %s;", (game_id,))
                conn.commit()
                return True
            except Exception as e:
                return str(e)

def get_platforms():
    """Получить список доступных платформ."""
    with connect_db() as conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("SELECT platform_id, name FROM platforms;")
            return cur.fetchall()

def add_game(title, publisher, genre, platform_id, release_date, seller_id):
    """Добавить новую игру."""
    with connect_db() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    INSERT INTO games (title, publisher, genre, platform_id, release_date)
                    VALUES (%s, %s, %s, %s, %s) RETURNING game_id;
                """, (title, publisher, genre, platform_id, release_date))
                game_id = cur.fetchone()[0]

                cur.execute("""
                    INSERT INTO shop_games (shop_id, game_id)
                    SELECT shop_id, %s
                    FROM shops
                    WHERE seller_id = %s;
                """, (game_id, seller_id))
                conn.commit()
                return True
            except Exception as e:
                return str(e)

def connect_db():
    return psycopg2.connect(**DB_CONFIG)


def add_product_to_sales_table(product_name, product_barcode, product_quantity, platform_id):
    new_row = pd.DataFrame(
        {
            "Название продукта": [product_name],
            "Barcode": [product_barcode],
            "Количество": [product_quantity],
            "Платформа": [platform_id],
        }
    )
    return new_row


def clear_sales_table():
    return pd.DataFrame(columns=["Название продукта", "Barcode", "Количество", "Платформа"])


def upload_sales(sales_table: pd.DataFrame) -> int:
    sale_date = date(2024, random.randint(1, 12), random.randint(1, 28))
    sale_id = SalesService().process_sale(sale_date, sales_table)
    return sale_id


def get_products() -> dict[str, str]:
    products = {}
    with connect_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT title, game_id FROM games;")
            for row in cur.fetchall():
                products[row["title"]] = row["game_id"]
    return products


def get_platform_options() -> dict:
    with connect_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT platform_id, name FROM platforms;")
            platforms = cur.fetchall()
            return {platform['name']: platform['platform_id'] for platform in platforms}


def get_keys_for_seller(seller_id: int):
    with connect_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT k.key_value, g.title, k.status, p.name AS platform
                FROM keys k
                JOIN games g ON k.game_id = g.game_id
                JOIN platforms p ON g.platform_id = p.platform_id
                JOIN shops s ON k.shop_id = s.shop_id
                WHERE s.seller_id = %s;
            """, (seller_id,))
            return cur.fetchall()


def add_key_to_db(key_value, game_title, status, platform_name, seller_id, price, start_date, end_date=None):
    with connect_db() as conn:
        with conn.cursor() as cur:
            # Получаем game_id и platform_id из таблицы games
            cur.execute("SELECT game_id, platform_id FROM games WHERE title = %s;", (game_title,))
            game_data = cur.fetchone()
            if game_data:
                game_id, platform_id = game_data
                # Вставляем новый ключ в таблицу keys
                cur.execute(
                    "INSERT INTO keys (key_value, game_id, status) VALUES (%s, %s, %s) RETURNING key_id;",
                    (key_value, game_id, status)
                )
                key_id = cur.fetchone()[0]
                
                # Вставляем цену в таблицу prices, связав цену с ключом
                cur.execute(
                    "INSERT INTO prices (key_id, start_date, end_date, price) VALUES (%s, %s, %s, %s);",
                    (key_id, start_date, end_date, price)
                )
                
                # Получаем shop_id продавца
                cur.execute("SELECT shop_id FROM shops WHERE seller_id = %s;", (seller_id,))
                shop_data = cur.fetchone()
                if shop_data:
                    shop_id = shop_data[0]
                    # Вставляем связь магазина с ключом в таблицу shop_keys
                    cur.execute("INSERT INTO shop_keys (shop_id, key_id) VALUES (%s, %s);", (shop_id, key_id))
                else:
                    # Если у продавца нет магазина, генерируем исключение
                    raise ValueError(f"No shop found for seller_id {seller_id}")
                
                conn.commit()
                return True
            return False

def fetch_available_keys():
    """Fetch the available keys from the database."""
    with connect_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    k.key_id,
                    k.key_value,
                    g.title AS game_title,
                    p.name AS platform_name,
                    k.status,
                    s.name AS shop_name,
                    pr.price
                FROM
                    keys k
                LEFT JOIN games g ON k.game_id = g.game_id
                LEFT JOIN platforms p ON g.platform_id = p.platform_id
                CROSS JOIN shops s
                LEFT JOIN prices pr ON k.key_id = pr.key_id
                WHERE
                    k.status = 'available';
            """)
            keys = cur.fetchall()
            print(keys)
    return keys

def purchase_key(user_id, key_id):
    """Handle the key purchase transaction."""
    with connect_db() as conn:
        try:
            with conn.cursor() as cur:
                # Start transaction
                cur.execute("""
                    INSERT INTO sales (buyer_id, sale_date)
                    VALUES (%s, %s)
                    RETURNING sale_id;
                """, (user_id, datetime.now()))
                sale_id = cur.fetchone()[0]

                # Insert into sales_details
                cur.execute("""
                    INSERT INTO sales_details (sale_id, key_id)
                    VALUES (%s, %s);
                """, (sale_id, key_id))

                # Update the key status to 'sold'
                cur.execute("""
                    UPDATE keys
                    SET status = 'sold', shop_id = NULL
                    WHERE key_id = %s;
                """, (key_id,))

                # Commit transaction
                conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return str(e)