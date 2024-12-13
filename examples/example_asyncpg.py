from contextlib import contextmanager
from dotenv import load_dotenv
from psycopg2 import pool
import os
import asyncpg
import asyncio

load_dotenv("env.env")

DB_CONFIG = {
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}


# Инициализируем пул подключений
async def create_connection_pool():
    connection_pool: asyncpg.Pool = await asyncpg.create_pool(
        **DB_CONFIG,
        min_size=1,
        max_size=10,
    )
    return connection_pool


async def close_connection_pool(connection_pool: asyncpg.Pool):
    await connection_pool.close()
    print("Connection pool closed.")


async def get_products(connection_pool: asyncpg.Pool, barcode: str):
    query = """
        SELECT
            barcode,
            name,
            package_size,
            weight
        FROM
            shop.products
        WHERE
            barcode = $1
    """

    async with connection_pool.acquire() as connection:
        rows = await connection.fetch(query, barcode)

    for row in rows:
        print(row)

    print("get_products finished")


async def get_products_with_stmt(connection_pool: asyncpg.Pool, barcodes: list[str]):
    query = """
        SELECT
            barcode,
            name,
            package_size,
            weight
        FROM
            shop.products
        WHERE
            barcode = $1
    """

    async with connection_pool.acquire() as connection:
        stmt = await connection.prepare(query)

        for barcode in barcodes:
            rows = await stmt.fetch(barcode)

            for row in rows:
                print(row)

    print("get_products finished")


async def get_products_pro(connection_pool: asyncpg.Pool, barcodes: tuple[str]):
    query = """
        SELECT
            barcode,
            name,
            package_size,
            weight
        FROM
            shop.products
        WHERE
            barcode = ANY($1)
    """

    async with connection_pool.acquire() as connection:
        rows = await connection.fetch(query, barcodes)

    for row in rows:
        print(row)

    print("get_products finished")


async def example_executemany(connection_pool: asyncpg.Pool):
    query = """
        INSERT INTO shop.products
            (barcode, name, package_size, weight)
        VALUES
            ($1, $2, $3, $4);
    """
    params = [
        ("12345642121", "Test Product asyncpg executemany 1", "1*1*1cm", 10.0),
        ("12345678911", "Test Product asyncpg executemany 2", "1*1*1cm", 10.0),
    ]
    async with connection_pool.acquire() as connection:
        await connection.executemany(query, params)


async def example_delete(connection_pool: asyncpg.Pool, barcodes: tuple[str]):
    query = """
        DELETE FROM shop.products
        WHERE
            barcode = ANY($1)
    """

    async with connection_pool.acquire() as connection:
        await connection.execute(query, barcodes)


async def main():
    connection_pool: asyncpg.Pool = await create_connection_pool()

    await example_executemany(connection_pool)
    await get_products_pro(connection_pool, ("12345642121", "12345678911"))

    await example_delete(connection_pool, ("12345642121", "12345678911"))
    await get_products_pro(connection_pool, ("12345642121", "12345678911"))

    await close_connection_pool(connection_pool)


if __name__ == "__main__":
    asyncio.run(main())
