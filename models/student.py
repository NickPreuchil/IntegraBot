from mysql.connector import Error


class Student:
    TABLE_NAME = 'students'
    CREATE_TABLE_QUERY = """
    CREATE TABLE IF NOT EXISTS students (
        id INT AUTO_INCREMENT PRIMARY KEY,
        telegram_id BIGINT UNIQUE NOT NULL,
        username VARCHAR(255),
        name VARCHAR(255),
        creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        tutor_id INT NOT NULL,
        FOREIGN KEY (tutor_id) REFERENCES tutors(id)
    )
    """

    def __init__(self, db):
        self.db = db

    def create(self, telegram_id: int, tutor_id: int, username: str = None, name: str = None):
        """Create a new student"""
        connection = self.db.get_connection()
        cursor = connection.cursor()
        query = """
        INSERT INTO students (telegram_id, username, name, tutor_id)
        VALUES (%s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (telegram_id, username, name, tutor_id))
            connection.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error creating student: {e}")
            return None
        finally:
            cursor.close()

    def get_by_telegram_id(self, telegram_id: int):
        """Get student by telegram_id"""
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT s.*, t.telegram_id as tutor_telegram_id, 
               t.username as tutor_username, t.name as tutor_name
        FROM students s
        JOIN tutors t ON s.tutor_id = t.id
        WHERE s.telegram_id = %s
        """
        try:
            cursor.execute(query, (telegram_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error getting student: {e}")
            return None
        finally:
            cursor.close()

    def get_by_tutor(self, tutor_id: int):
        """Get all students for a tutor"""
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT * FROM students WHERE tutor_id = %s
        """
        try:
            cursor.execute(query, (tutor_id,))
            return cursor.fetchall()
        except Error as e:
            print(f"Error getting tutor students: {e}")
            return None
        finally:
            cursor.close()

    def get_by_id(self, student_id: int):
        """Get student by id"""
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT s.*, t.telegram_id as tutor_telegram_id, 
               t.username as tutor_username, t.name as tutor_name
        FROM students s
        JOIN tutors t ON s.tutor_id = t.id
        WHERE s.id = %s
        """
        try:
            cursor.execute(query, (student_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error getting student: {e}")
            return None
        finally:
            cursor.close()

    def update(self, telegram_id: int, username: str = None, name: str = None, tutor_id: int = None):
        """Update student information"""
        connection = self.db.get_connection()
        cursor = connection.cursor()
        if tutor_id:
            query = """
            UPDATE students 
            SET username = %s, name = %s, tutor_id = %s
            WHERE telegram_id = %s
            """
            params = (username, name, tutor_id, telegram_id)
        else:
            query = """
            UPDATE students 
            SET username = %s, name = %s
            WHERE telegram_id = %s
            """
            params = (username, name, telegram_id)

        try:
            cursor.execute(query, params)
            connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error updating student: {e}")
            return False
        finally:
            cursor.close()

    def delete(self, student_id: int):
        """Delete student by student_id"""
        connection = self.db.get_connection()
        cursor = connection.cursor()
        query = "DELETE FROM students WHERE id = %s"
        try:
            cursor.execute(query, (student_id,))
            connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error deleting student: {e}")
            return False
        finally:
            cursor.close()
