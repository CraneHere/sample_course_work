import psycopg2

import os
from dotenv import load_dotenv

load_dotenv("env.env")

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}


def example1():
    connection = psycopg2.connect(**DB_CONFIG)
    try:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM shop.products")

        rows = cursor.fetchall()

        for row in rows:
            print(row)

        cursor.close()
    finally:
        connection.close()


def example2():
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    cursor.execute("SELECT barcode, name, package_size, weight FROM shop.products")

    columns = [desc[0] for desc in cursor.description]

    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    for row in rows:
        print(row)

    cursor.close()
    connection.close()


# @contextmanager
# def get_connection():
#     connection = psycopg2.connect(**DB_CONFIG)
#     try:
#         yield connection
#     finally:
#         connection.close()


def example3():
    query = "SELECT barcode, name, package_size, weight FROM shop.products"

    with psycopg2.connect(**DB_CONFIG) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    for row in rows:
        print(row)


if __name__ == "__main__":
    # example2()

    connection = psycopg2.connect(**DB_CONFIG)
    try:
        example2(connection)
        example3(connection)
    finally:
        connection.close()
