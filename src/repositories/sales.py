from pandas import DataFrame
import psycopg2
from settings import DB_CONFIG
from datetime import date


def add_sale(sale_date: date) -> int:
    query = """
        INSERT INTO sales (sale_date)
        VALUES (%(sale_date)s) RETURNING sale_id;
    """
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(query, {"sale_date": sale_date})
            return cur.fetchone()[0]


def add_sale_details(sales: DataFrame) -> None:
    query = """
        INSERT INTO sales_details (sale_id, barcode, quantity)
        VALUES (%s, %s, %s);
    """
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                query,
                sales[["sale_id", "barcode", "quantity"]].itertuples(
                    index=False, name=None
                ),
            )


def get_sales_statistics(barcode: str) -> DataFrame:
    query = """
        SELECT
            sum(sales_details.quantity) as quantity,
            sales.sale_date
        FROM sales_details 
            JOIN sales ON 
                sales.sale_id = sales_details.sale_id
        WHERE
            sales_details.barcode = %(barcode)s
        GROUP BY
            sales.sale_date;
    """
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, {"barcode": barcode})
            return DataFrame(cur.fetchall())
