from mysql.connector import Error


class Tutor:
    TABLE_NAME = 'tutors'
    CREATE_TABLE_QUERY = """
    CREATE TABLE IF NOT EXISTS tutors (
        id INT AUTO_INCREMENT PRIMARY KEY,
        telegram_id BIGINT UNIQUE NOT NULL,
        username VARCHAR(255),
        name VARCHAR(255),
        creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """

    def __init__(self, db):
        self.db = db

    def create(self, telegram_id: int, username: str = None, name: str = None):
        """Create a new tutor"""
        connection = self.db.get_connection()
        cursor = connection.cursor()
        query = """
        INSERT INTO tutors (telegram_id, username, name)
        VALUES (%s, %s, %s)
        """
        try:
            cursor.execute(query, (telegram_id, username, name))
            connection.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error creating tutor: {e}")
            return None
        finally:
            cursor.close()

    def get_by_telegram_id(self, telegram_id: int):
        """Get tutor by telegram_id"""
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM tutors WHERE telegram_id = %s"
        try:
            cursor.execute(query, (telegram_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error getting tutor: {e}")
            return None
        finally:
            cursor.close()

    def get_by_id(self, tutor_id: int):
        """Get tutor by ID"""
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM tutors WHERE id = %s"
        try:
            cursor.execute(query, (tutor_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error getting tutor: {e}")
            return None
        finally:
            cursor.close()

    def update(self, telegram_id: int, username: str = None, name: str = None):
        """Update tutor information"""
        connection = self.db.get_connection()
        cursor = connection.cursor()
        query = """
        UPDATE tutors 
        SET username = %s, name = %s
        WHERE telegram_id = %s
        """
        try:
            cursor.execute(query, (username, name, telegram_id))
            connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error updating tutor: {e}")
            return False
        finally:
            cursor.close()

    def delete(self, tutor_id: int):
        """Delete tutor by tutor_id"""
        connection = self.db.get_connection()
        cursor = connection.cursor()
        query = "DELETE FROM tutors WHERE id = %s"
        try:
            cursor.execute(query, (tutor_id,))
            connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error deleting tutor: {e}")
            return False
        finally:
            cursor.close()
