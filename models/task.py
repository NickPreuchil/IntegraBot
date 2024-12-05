from mysql.connector import Error

class Task:
    TABLE_NAME = 'tasks'
    CREATE_TABLE_QUERY = """
    CREATE TABLE IF NOT EXISTS tasks (
        task_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) DEFAULT NULL,
        channel_message_id BIGINT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """

    def __init__(self, db_connection):
        self.connection = db_connection

    def create(self, channel_message_id: int, name: str = None):
        """Create a new task"""
        if not self.connection:
            return None

        cursor = self.connection.cursor()
        query = """
        INSERT INTO tasks (channel_message_id, name)
        VALUES (%s, %s)
        """
        
        try:
            cursor.execute(query, (channel_message_id, name))
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error creating task: {e}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()

    def get_by_channel_message(self, channel_message_id: int):
        """Get task by channel message ID"""
        if not self.connection:
            return None

        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM tasks WHERE channel_message_id = %s"
        try:
            cursor.execute(query, (channel_message_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error getting task: {e}")
            return None
        finally:
            cursor.close()

    def get_by_id(self, task_id: int):
        """Get task by task ID"""
        if not self.connection:
            return None

        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM tasks WHERE task_id = %s"
        
        try:
            cursor.execute(query, (task_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error getting task: {e}")
            return None
        finally:
            cursor.close()

    def delete(self, task_id: int):
        """Delete task by ID"""
        if not self.connection:
            return False

        cursor = self.connection.cursor()
        query = "DELETE FROM tasks WHERE task_id = %s"
        try:
            cursor.execute(query, (task_id,))
            self.connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error deleting task: {e}")
            return False
        finally:
            cursor.close()

    def update_name(self, message_id: int, name: str):
        """Update task name"""
        if not self.connection:
            return False

        cursor = self.connection.cursor()
        query = "UPDATE tasks SET name = %s WHERE channel_message_id = %s"
        
        try:
            cursor.execute(query, (name, message_id))
            self.connection.commit()
            return True
        except Error as e:
            print(f"Error updating task name: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()
