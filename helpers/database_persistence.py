# database_persistence.py

import os
from contextlib import contextmanager
import logging
import psycopg2
from psycopg2.extras import DictCursor
from werkzeug.security import generate_password_hash, check_password_hash

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

class DatabasePersistence:
    def __init__(self):
        self._setup_schema()
        self.ITEMS_PER_PAGE = 5  # Define the number of people per page

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

    def _execute_query(self, query, params=None):
        with self._database_connect() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchall()

    def _execute_one(self, query, params=None):
        with self._database_connect() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchone()

    def _execute_none(self, query, params=None):
        with self._database_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                conn.commit()

    def get_paginated_people(self, user_id, page):
        offset = (page - 1) * self.ITEMS_PER_PAGE
        query = """
            SELECT P.id, P.name
            FROM Person P
            WHERE P.user_id = %s
            ORDER BY P.name
            LIMIT %s OFFSET %s;
        """
        results = self._execute_query(query, (user_id, self.ITEMS_PER_PAGE, offset))
        return [dict(row) for row in results]

    def get_person_count(self, user_id):
        query = """
            SELECT COUNT(*) FROM Person WHERE user_id = %s;
        """
        result = self._execute_one(query, (user_id,))
        return result['count'] if result else 0

    def find_person(self, person_id, user_id):
        query = """
            SELECT P.id, P.name
            FROM Person P
            WHERE P.id = %s AND P.user_id = %s;
        """
        person = self._execute_one(query, (person_id, user_id))
        return dict(person) if person else None

    def find_person_with_gifts(self, person_id, user_id, page, gifts_per_page):
        offset = (page - 1) * gifts_per_page
        query = """
            SELECT P.id, P.name,
                   (SELECT COUNT(*) FROM Gift WHERE person_id = P.id) AS total_gifts,
                   COALESCE(ARRAY_AGG(G.gift ORDER BY G.id) FILTER (WHERE G.gift IS NOT NULL), ARRAY[]::VARCHAR[]) AS all_gifts
            FROM Person P
            LEFT JOIN Gift G ON P.id = G.person_id
            WHERE P.id = %s AND P.user_id = %s
            GROUP BY P.id, P.name;
        """
        person_data = self._execute_one(query, (person_id, user_id))

        if not person_data:
            return None

        # Convert to a standard dictionary
        person_data = dict(person_data)

        # Add paginated gifts
        person_data['paginated_gifts'] = []
        if 'all_gifts' in person_data and person_data['all_gifts']:
            all_gifts = person_data['all_gifts']
            person_data['paginated_gifts'] = all_gifts[offset:offset + gifts_per_page]

        # Add gift_lst (all gifts)
        person_data['gift_lst'] = person_data.get('all_gifts', [])

        return person_data

    def get_gift_count(self, person_id):
        query = """
            SELECT COUNT(*) FROM Gift WHERE person_id = %s;
        """
        result = self._execute_one(query, (person_id,))
        return result['count'] if result else 0

    def validate_person(self, name, gift_lst, user_id, exclude_id=None):
        MAX_NAME_LENGTH = 50
        MAX_GIFT_LENGTH = 100

        query = "SELECT id FROM Person WHERE LOWER(name) = LOWER(%s) AND user_id = %s"
        existing_person = self._execute_one(query, (name, user_id))
        if existing_person and existing_person['id'] != exclude_id:
            return "The name must be unique for this user."

        if not (1 <= len(name) <= MAX_NAME_LENGTH):
            return f"The name must be between 1 and {MAX_NAME_LENGTH} characters."

        if any(len(gift) > MAX_GIFT_LENGTH for gift in gift_lst):
            return f"Each gift must not exceed {MAX_GIFT_LENGTH} characters."

        return None

    def add_person(self, person, user_id):
        """Add a new person and their gifts to the database."""
        query_person = "INSERT INTO Person (user_id, name) VALUES (%s, %s) RETURNING id"
        query_gift = "INSERT INTO Gift (person_id, gift) VALUES (%s, %s)"
        with self._database_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query_person, (user_id, person['name']))
                person_id = cursor.fetchone()[0]

                for gift in person['gift_lst']:
                    cursor.execute(query_gift, (person_id, gift))
                conn.commit()
        return person_id

    def update_person(self, person, new_name, gift_lst, user_id):
        query_update_person = "UPDATE Person SET name = %s WHERE id = %s AND user_id = %s"
        query_delete_gifts = "DELETE FROM Gift WHERE person_id = %s"
        query_insert_gift = "INSERT INTO Gift (person_id, gift) VALUES (%s, %s)"
        with self._database_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query_update_person, (new_name, person['id'], user_id))
                cursor.execute(query_delete_gifts, (person['id'],))
                for gift in gift_lst:
                    cursor.execute(query_insert_gift, (person['id'], gift))
                conn.commit()

    def delete_person(self, person_id, user_id):
        query = "DELETE FROM Person WHERE id = %s AND user_id = %s"
        self._execute_none(query, (person_id, user_id))

    def search_matching_with_gifts(self, query_str, user_id):
        query = """
            SELECT P.id AS person_id, P.name AS person_name, G.gift
            FROM Person P
            LEFT JOIN Gift G ON P.id = G.person_id
            WHERE P.user_id = %s AND (P.name ILIKE %s OR G.gift ILIKE %s)
            ORDER BY P.name, G.id;
        """
        results = self._execute_query(query, (user_id, f"%{query_str}%", f"%{query_str}%"))
        
        # Group results by person
        grouped_results = {}
        for row in results:
            person_id = row['person_id']
            if person_id not in grouped_results:
                grouped_results[person_id] = {
                    'id': person_id,
                    'name': row['person_name'],
                    'paginated_gifts': []
                }
            if row['gift']:
                grouped_results[person_id]['paginated_gifts'].append(row['gift'])

        return {'results': list(grouped_results.values())}

    def get_search_result_count(self, query, user_id):
        query = """
            SELECT COUNT(*)
            FROM (
                SELECT P.id AS person_id, G.id AS gift_id
                FROM Person P
                LEFT JOIN Gift G ON P.id = G.person_id
                WHERE P.user_id = %s AND (P.name ILIKE %s OR G.gift ILIKE %s)
            ) AS subquery;
        """
        result = self._execute_one(query, (user_id, f"%{query}%", f"%{query}%"))
        return result['count'] if result else 0

    def create_user(self, username, password):
        """Creates a new user in the database."""
        hashed_password = generate_password_hash(password)
        query = "INSERT INTO Users (username, password_hash) VALUES (%s, %s) RETURNING id"
        user = self._execute_one(query, (username, hashed_password))
        return user['id'] if user else None

    def get_user_by_username(self, username):
        """Retrieves a user from the database by username."""
        query = "SELECT * FROM Users WHERE username = %s"
        return self._execute_one(query, (username,))

    def _setup_schema(self):
        logger.info("Setting up schema if necessary.")
        with self._database_connect() as conn:
            with conn.cursor() as cursor:
                # Check and create the Person table
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
                            name VARCHAR(50) NOT NULL,
                            user_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
                            UNIQUE (user_id, name)
                        );
                    """)
                    logger.info("Created table: Person")
                else:
                    # Check if user_id column exists in Person table and add it if missing
                    cursor.execute("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = 'person' AND column_name = 'user_id';
                    """)
                    user_id_exists = cursor.fetchone()

                    if not user_id_exists:
                        cursor.execute("""
                            ALTER TABLE Person
                            ADD COLUMN user_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE;
                        """)
                        logger.info("Added user_id column to Person table.")
                    # Add unique constraint if missing (important for the logic)
                    cursor.execute("""
                        SELECT constraint_name
                        FROM information_schema.table_constraints
                        WHERE table_name = 'person' AND constraint_type = 'UNIQUE';
                    """)
                    unique_constraint_exists = cursor.fetchone()
                    if not unique_constraint_exists:
                        cursor.execute("""
                            ALTER TABLE Person
                            ADD CONSTRAINT unique_user_name UNIQUE (user_id, name);
                        """)
                        logger.info("Added unique constraint to Person table (user_id, name).")


                # Check and create the Gift table
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
                            gift VARCHAR(100) NOT NULL
                        );
                    """)
                    logger.info("Created table: Gift")

                # Check and create the Users table
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = 'users'
                    );
                """)
                users_exists = cursor.fetchone()[0]

                if not users_exists:
                    cursor.execute("""
                        CREATE TABLE Users (
                            id SERIAL PRIMARY KEY,
                            username VARCHAR(50) NOT NULL UNIQUE,
                            password_hash VARCHAR(255) NOT NULL
                        );
                    """)
                    logger.info("Created table: Users")
                conn.commit()