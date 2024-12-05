import mysql.connector
from mysql.connector import Error, connect
import os
from dotenv import load_dotenv
import sys

from models import Student, Tutor, Task, Answer

# Load environment variables
load_dotenv()

class Database:
    def __init__(self, logger):
        self.connection = None
        self.logger = logger
        try:
            # First, connect without specifying database to create it if needed
            self.connection = self.connect(with_database=False)
            
            # Create database if it doesn't exist
            self._create_database()
            
            # Close initial connection
            self.connection.close()
            
            # Reconnect with the database specified
            self.connection = self.connect()
            print("Successfully connected to MySQL database")
            
            # Initialize models with self
            self.tutor = Tutor(self)
            self.student = Student(self)
            self.task = Task(self)
            self.answer = Answer(self)
            
        except Error as e:
            print(f"Error connecting to MySQL: {e}")

    def _create_database(self):
        """Create database if it doesn't exist"""
        if not self.connection:
            return

        cursor = self.connection.cursor()
        database_name = os.getenv('MYSQL_DATABASE')
        
        try:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
            print(f"Database '{database_name}' is ready")
        except Error as e:
            print(f"Error creating database: {e}")
        finally:
            cursor.close()

    def get_connection(self):
        """Ensure database connection is active and reconnect if needed"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.logger.info("Database connection lost. Attempting to reconnect...")
                self.connection = self.connect()
                self.logger.info("Successfully reconnected to MySQL database")
            return self.connection
        except Error as e:
            self.logger.error(f"Error reconnecting to MySQL: {e}")
            sys.exit('Mysql Error')

    def init_db(self):
        """Initialize database tables if they don't exist"""
        self.connection = self.get_connection()
        if not self.connection:
            return

        cursor = self.connection.cursor()
        try:
            # Create tables using model queries
            cursor.execute(Tutor.CREATE_TABLE_QUERY)
            cursor.execute(Student.CREATE_TABLE_QUERY)
            cursor.execute(Task.CREATE_TABLE_QUERY)
            cursor.execute(Answer.CREATE_TABLE_QUERY)
            self.connection.commit()
            print("Database tables are ready")
        except Error as e:
            print(f"Error creating tables: {e}")
        finally:
            cursor.close()

    def connect(self, with_database = True):
        if (with_database):
            return mysql.connector.connect(
                host=os.getenv('MYSQL_HOST', 'localhost'),
                user=os.getenv('MYSQL_USER'),
                password=os.getenv('MYSQL_PASSWORD'),
                database=os.getenv('MYSQL_DATABASE'),
            )
        else:
            return mysql.connector.connect(
                host=os.getenv('MYSQL_HOST', 'localhost'),
                user=os.getenv('MYSQL_USER'),
                password=os.getenv('MYSQL_PASSWORD'),
            )

    def __del__(self):
        """Close database connection when object is destroyed"""
        if self.connection and self.connection.is_connected():
            self.connection.close()