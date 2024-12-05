from mysql.connector import Error
from enum import IntEnum
from typing import List, Dict

class AnswerStatus(IntEnum):
    NEEDS_REVIEW = 1  # требует проверки
    NEEDS_REVISION = 2  # отправлен на переделывание
    REVIEWED = 3  # проверен

class Answer:
    TABLE_NAME = 'answers'
    CREATE_TABLE_QUERY = """
    CREATE TABLE IF NOT EXISTS answers (
        answer_id INT AUTO_INCREMENT PRIMARY KEY,
        student_id INT NOT NULL,
        task_id INT NOT NULL,
        answer_status TINYINT NOT NULL DEFAULT 1,
        message_link VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
        CHECK (answer_status IN (1, 2, 3))
    )
    """

    def __init__(self, db_connection):
        self.connection = db_connection

    def create(self, student_id: int, task_id: int, message_link: str, answer_status: int = AnswerStatus.NEEDS_REVIEW):
        """Create a new answer"""
        if not self.connection:
            return None

        cursor = self.connection.cursor()
        query = """
        INSERT INTO answers (student_id, task_id, message_link, answer_status)
        VALUES (%s, %s, %s, %s)
        """
        try:
            # Convert enum to int for database
            status_value = int(answer_status)
            cursor.execute(query, (student_id, task_id, message_link, status_value))
            self.connection.commit()
            return cursor.latrowid
        except Error as e:
            print(f"Error creating answer: {e}")
            return None
        finally:
            cursor.close()

    def get_by_id(self, answer_id: int):
        """Get answer by ID"""
        if not self.connection:
            return None

        # Используем buffered=True и отключаем кэширование
        cursor = self.connection.cursor(dictionary=True, buffered=True)
        self.connection.commit()  # Сбрасываем кэш перед запросом
        
        query = """
        SELECT a.*, s.name as student_name, s.username as student_username
        FROM answers a
        JOIN students s ON a.student_id = s.id
        WHERE a.answer_id = %s
        """
        try:
            cursor.execute(query, (answer_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error getting answer: {e}")
            return None
        finally:
            cursor.close()

    def get_by_student(self, student_id: int):
        """Get all answers by student ID"""
        if not self.connection:
            return None

        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM answers WHERE student_id = %s ORDER BY created_at DESC"
        try:
            cursor.execute(query, (student_id,))
            return cursor.fetchall()
        except Error as e:
            print(f"Error getting answers: {e}")
            return None
        finally:
            cursor.close()

    def get_by_task(self, task_id: int):
        """Get all answers for a specific task"""
        if not self.connection:
            return None

        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM answers WHERE task_id = %s ORDER BY created_at DESC"
        try:
            cursor.execute(query, (task_id,))
            return cursor.fetchall()
        except Error as e:
            print(f"Error getting answers: {e}")
            return None
        finally:
            cursor.close()

    def update_status(self, answer_id: int, new_status: int):
        """Update answer status"""
        if not self.connection:
            print("Error: No database connection")
            return False

        # Validate status value
        valid_statuses = [status.value for status in AnswerStatus]
        if new_status not in valid_statuses:
            print(f"Error: Invalid status value {new_status}. Valid values are {valid_statuses}")
            return False

        cursor = self.connection.cursor()
        query = "UPDATE answers SET answer_status = %s WHERE answer_id = %s"
        try:
            print(f"Executing query: {query} with params: ({new_status}, {answer_id})")
            cursor.execute(query, (new_status, answer_id))
            self.connection.commit()
            rows_affected = cursor.rowcount
            print(f"Rows affected: {rows_affected}")
            return rows_affected > 0
        except Error as e:
            print(f"Error updating answer status: {e}")
            return False
        finally:
            cursor.close()

    def get_by_status(self, status: int):
        """Get all answers with specific status"""
        if not self.connection:
            return None

        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM answers WHERE answer_status = %s ORDER BY created_at DESC"
        try:
            cursor.execute(query, (status,))
            return cursor.fetchall()
        except Error as e:
            print(f"Error getting answers by status: {e}")
            return None
        finally:
            cursor.close()

    def get_by_tutor(self, tutor_id: int):
        """Get answers for tutor's students that need review"""
        if not self.connection:
            return None

        # Используем buffered=True и отключаем кэширование
        cursor = self.connection.cursor(dictionary=True, buffered=True)
        self.connection.commit()  # Сбрасываем кэш перед запросом
        
        query = """
        SELECT a.*, s.name as student_name, s.username as student_username
        FROM answers a
        JOIN students s ON a.student_id = s.id
        WHERE s.tutor_id = %s AND a.answer_status = %s
        ORDER BY a.created_at ASC
        """
        try:
            cursor.execute(query, (tutor_id, int(AnswerStatus.NEEDS_REVIEW)))
            return cursor.fetchall()
        except Error as e:
            print(f"Error getting answers for tutor: {e}")
            return None
        finally:
            cursor.close()

    def get_next_answer(self, current_answer_id: int, tutor_id: int):
        """Get next answer that needs review"""
        if not self.connection:
            return None

        # Используем buffered=True и отключаем кэширование
        cursor = self.connection.cursor(dictionary=True, buffered=True)
        self.connection.commit()  # Сбрасываем кэш перед запросом
        
        query = """
        WITH current_answer AS (
            SELECT created_at, answer_id
            FROM answers
            WHERE answer_id = %s
        )
        SELECT a.*, s.name as student_name, s.username as student_username
        FROM answers a
        JOIN students s ON a.student_id = s.id
        JOIN current_answer ca
        WHERE s.tutor_id = %s 
        AND (
            a.created_at > ca.created_at
            OR (a.created_at = ca.created_at AND a.answer_id > ca.answer_id)
        )
        AND a.answer_status = %s
        ORDER BY a.created_at ASC, a.answer_id ASC
        LIMIT 1
        """
        try:
            cursor.execute(query, (current_answer_id, tutor_id, int(AnswerStatus.NEEDS_REVIEW)))
            return cursor.fetchone()
        except Error as e:
            print(f"Error getting next answer: {e}")
            return None
        finally:
            cursor.close()

    def get_previous_answer(self, current_answer_id: int, tutor_id: int):
        """Get previous answer that needs review"""
        if not self.connection:
            return None

        # Используем buffered=True и отключаем кэширование
        cursor = self.connection.cursor(dictionary=True, buffered=True)
        self.connection.commit()  # Сбрасываем кэш перед запросом
        
        query = """
        WITH current_answer AS (
            SELECT created_at, answer_id
            FROM answers
            WHERE answer_id = %s
        )
        SELECT a.*, s.name as student_name, s.username as student_username
        FROM answers a
        JOIN students s ON a.student_id = s.id
        JOIN current_answer ca
        WHERE s.tutor_id = %s 
        AND (
            a.created_at < ca.created_at
            OR (a.created_at = ca.created_at AND a.answer_id < ca.answer_id)
        )
        AND a.answer_status = %s
        ORDER BY a.created_at DESC, a.answer_id DESC
        LIMIT 1
        """
        try:
            cursor.execute(query, (current_answer_id, tutor_id, int(AnswerStatus.NEEDS_REVIEW)))
            return cursor.fetchone()
        except Error as e:
            print(f"Error getting previous answer: {e}")
            return None
        finally:
            cursor.close()

    def get_student_statistics(self, student_id: int) -> List[Dict]:
        """Get statistics for a student"""
        if not self.connection:
            return None

        cursor = self.connection.cursor(dictionary=True)
        
        query = """
            SELECT 
                t.task_id,
                t.name as task_name,
                t.created_at as task_created_at,
                a.answer_status as status,
                a.message_link,
                COUNT(*) as attempts_count,
                MAX(a.created_at) as last_attempt
            FROM tasks t
            LEFT JOIN answers a ON t.task_id = a.task_id AND a.student_id = %s
            GROUP BY t.task_id, t.name, t.created_at, a.answer_status, a.message_link
            ORDER BY t.created_at DESC
        """
        
        try:
            cursor.execute(query, (student_id,))
            return cursor.fetchall()
        except Error as e:
            print(f"Error getting student statistics: {e}")
            return None
        finally:
            cursor.close()

    def get_by_message_link(self, message_link: str):
        """Get answer by message link"""
        if not self.connection:
            return None

        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM answers WHERE message_link = %s"
        
        try:
            cursor.execute(query, (message_link,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error getting answer by message link: {e}")
            return None
        finally:
            cursor.close()

    def update(self, answer_id: int, data: dict):
        """Update answer"""
        if not self.connection:
            return False

        cursor = self.connection.cursor()
        
        # Формируем SET часть запроса из словаря data
        set_parts = []
        values = []
        for key, value in data.items():
            set_parts.append(f"{key} = %s")
            values.append(value)
        
        # Добавляем answer_id в конец списка значений
        values.append(answer_id)
        
        query = f"""
        UPDATE answers 
        SET {', '.join(set_parts)}
        WHERE answer_id = %s
        """
        
        try:
            cursor.execute(query, values)
            self.connection.commit()
            return True
        except Error as e:
            print(f"Error updating answer: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()
