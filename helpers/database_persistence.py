import os
from contextlib import contextmanager
import logging
import psycopg2
from psycopg2.extras import DictCursor

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

class DatabasePersistence:
    def __init__(self):
        self._setup_schema()

    @contextmanager
    def _database_connect(self):
        if os.environ.get('FLASK_ENV') == 'production':
            connection = psycopg2.connect(os.environ['DATABASE_URL'])
        else:
            connection = psycopg2.connect(dbname="gift_ideas")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def get_all_people(self):
        query = """
            SELECT P.id, P.name, ARRAY_AGG(G.gift) AS gift_lst
            FROM Person P
            LEFT JOIN Gift G ON P.id = G.person_id
            GROUP BY P.id
            ORDER BY P.name;
        """
        with self._database_connect() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                return [dict(row) for row in results]

    def find_person(self, person_id):
        query = """
            SELECT P.id, P.name, ARRAY_AGG(G.gift) AS gift_lst
            FROM Person P
            LEFT JOIN Gift G ON P.id = G.person_id
            WHERE P.id = %s
            GROUP BY P.id;
        """
        logger.info("Executing query: %s with person_id: %s", query, person_id)
        with self._database_connect() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (person_id,))
                person = cursor.fetchone()
                return dict(person) if person else None

    def validate_person(self, name, gift_lst, exclude_id=None):
        MAX_NAME_LENGTH = 30
        MAX_GIFT_LENGTH = 50

        query = "SELECT id FROM Person WHERE LOWER(name) = LOWER(%s)"
        logger.info("Executing query: %s with name: %s", query, name)
        with self._database_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (name,))
                existing_person = cursor.fetchone()
                if existing_person and existing_person[0] != exclude_id:
                    return "The name must be unique."

        if not (1 <= len(name) <= MAX_NAME_LENGTH):
            return f"The name must be between 1 and {MAX_NAME_LENGTH} characters."

        if any(len(gift) > MAX_GIFT_LENGTH for gift in gift_lst):
            return f"Each gift must not exceed {MAX_GIFT_LENGTH} characters."

        return None

    def add_person(self, person):
        """Add a new person and their gifts to the database."""
        query_person = "INSERT INTO Person (name) VALUES (%s) RETURNING id"
        query_gift = "INSERT INTO Gift (person_id, gift) VALUES (%s, %s)"
        logger.info("Adding person: %s", person)
        with self._database_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query_person, (person['name'],))
                person_id = cursor.fetchone()[0]

                for gift in person['gift_lst']:
                    cursor.execute(query_gift, (person_id, gift))

        return person_id

    def update_person(self, person, new_name, gift_lst):
        query_update_person = "UPDATE Person SET name = %s WHERE id = %s"
        query_delete_gifts = "DELETE FROM Gift WHERE person_id = %s"
        query_insert_gift = "INSERT INTO Gift (person_id, gift) VALUES (%s, %s)"
        logger.info("Updating person ID: %s with new name: %s", person['id'], new_name)
        with self._database_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query_update_person, (new_name, person['id']))
                cursor.execute(query_delete_gifts, (person['id'],))
                for gift in gift_lst:
                    cursor.execute(query_insert_gift, (person['id'], gift))

    def delete_person(self, person_id):
        query = "DELETE FROM Person WHERE id = %s"
        logger.info("Deleting person ID: %s", person_id)
        with self._database_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (person_id,))

    def search_matching(self, query):
        """Search for gifts matching a query."""
        search_query = """
            SELECT P.id, P.name, ARRAY_AGG(G.gift) AS items_lst
            FROM Person P
            JOIN Gift G ON P.id = G.person_id
            WHERE LOWER(G.gift) LIKE %s
            GROUP BY P.id
            ORDER BY P.name;
        """
        logger.info("Searching gifts with query: %s", query)
        with self._database_connect() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(search_query, (f"%{query.lower()}%",))
                results = cursor.fetchall()
                return [dict(result) for result in results]

    def _setup_schema(self):
        logger.info("Setting up schema if necessary.")
        with self._database_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = 'person'
                    );
                """)
                person_exists = cursor.fetchone()[0]

                if not person_exists:
                    cursor.execute("""
                        CREATE TABLE Person (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(30) NOT NULL UNIQUE
                        );
                    """)
                    logger.info("Created table: Person")

                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = 'gift'
                    );
                """)
                gift_exists = cursor.fetchone()[0]

                if not gift_exists:
                    cursor.execute("""
                        CREATE TABLE Gift (
                            id SERIAL PRIMARY KEY,
                            person_id INTEGER NOT NULL REFERENCES Person(id) ON DELETE CASCADE,
                            gift VARCHAR(50) NOT NULL
                        );
                    """)
                    logger.info("Created table: Gift")
