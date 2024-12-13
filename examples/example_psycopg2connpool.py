from contextlib import contextmanager
from dotenv import load_dotenv
from psycopg2 import pool
import atexit
import os
import psycopg2

load_dotenv("env.env")

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}


# Инициализируем пул подключений
connection_pool = psycopg2.pool.SimpleConnectionPool(**DB_CONFIG, minconn=1, maxconn=10)


@contextmanager
def get_connection():
    connection = connection_pool.getconn()
    try:
        yield connection
    finally:
        connection_pool.putconn(connection)


def on_exit():
    print("Приложение завершено! Закрываем ресурсы...")
    connection_pool.closeall()
    print("Connection pool closed.")


# Регистрируем функцию для выполнения при завершении программы
atexit.register(on_exit)


def example_fetchall():
    query = "SELECT barcode, name, package_size, weight FROM shop.products"

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    for row in rows:
        print(row)

    print("example4 finished")


def example_insert():
    query = """
    INSERT INTO shop.products
        (barcode, name, package_size, weight)
    VALUES
        (%s, %s, %s, %s)
    """
    params = (
        "1234567890",
        "Test Product",
        "1*1*1cm",
        10.0,
    )

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
        conn.commit()


def example_executemany():
    query = "INSERT INTO shop.products (barcode, name, package_size, weight) VALUES (%s, %s, %s, %s)"
    params = [
        ("1234564212", "Test Product executemany 1", "1*1*1cm", 10.0),
        ("1234567891", "Test Product executemany 2", "1*1*1cm", 10.0),
    ]
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, params)
            conn.commit()


def example_with_params(barcode: str):
    # VERY BAD CODE
    # query = f"SELECT barcode, name, package_size, weight FROM shop.products where barcode = '{barcode}'"

    query = """
        SELECT
            barcode,
            name,
            package_size,
            weight
        FROM
            shop.products
        WHERE
            barcode = %s
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (barcode,))
            columns = [desc[0] for desc in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    for row in rows:
        print(row)

    print("example4 finished")


def example_with_keys_params(barcode: str):
    # VERY BAD CODE
    # query = f"SELECT barcode, name, package_size, weight FROM shop.products where barcode = '{barcode}'"

    query = """
        SELECT
            barcode,
            name,
            package_size,
            weight
        FROM
            shop.products
        WHERE
            barcode = %(barcode)s
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, {"barcode": barcode})
            columns = [desc[0] for desc in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    for row in rows:
        print(row)

    print("example4 finished")


if __name__ == "__main__":
    # example_fetchall()
    # example_insert()
    # example_executemany()
    # example_fetchall()

    # example_with_params("123456789012")
    example_with_keys_params("123456789012")
