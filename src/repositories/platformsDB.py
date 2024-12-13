import psycopg2
import psycopg2.extras
from settings import DB_CONFIG

def get_platforms() -> list[dict]:
    print("Получение платформ")
    query = "SELECT platform_id, name FROM Platforms;"
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()
