from database import Database
import logging
from datetime import datetime
from models import AnswerStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_tutors(db: Database, tutors_data: list[dict]) -> None:
    """
    Заполняет таблицу tutors данными.
    
    Пример использования:
    tutors = [
        {
            'telegram_id': 123456789,
            'username': 'tutor1',
            'name': 'Иван Иванов'
        },
        {
            'telegram_id': 987654321,
            'username': 'tutor2',
            'name': 'Петр Петров'
        }
    ]
    seed_tutors(db, tutors)
    """
    for tutor in tutors_data:
        try:
            tutor_id = db.tutor.create(
                telegram_id=tutor['telegram_id'],
                username=tutor['username'],
                name=tutor['name']
            )
            if tutor_id:
                logger.info(f"Created tutor: {tutor['name']} (ID: {tutor_id})")
            else:
                logger.error(f"Failed to create tutor: {tutor['name']}")
        except Exception as e:
            logger.error(f"Error creating tutor {tutor['name']}: {e}")

def seed_students(db: Database, students_data: list[dict]) -> None:
    """
    Заполняет таблицу students данными.
    
    Пример использования:
    students = [
        {
            'telegram_id': 111222333,
            'username': 'student1',
            'name': 'Алексей Алексеев',
            'tutor_id': 1  # ID существующего тьютора
        },
        {
            'telegram_id': 444555666,
            'username': 'student2',
            'name': 'Мария Маринова',
            'tutor_id': 2  # ID существующего тьютора
        }
    ]
    seed_students(db, students)
    """
    for student in students_data:
        try:
            student_id = db.student.create(
                telegram_id=student['telegram_id'],
                username=student['username'],
                name=student['name'],
                tutor_id=student['tutor_id']
            )
            if student_id:
                logger.info(f"Created student: {student['name']} (ID: {student_id})")
            else:
                logger.error(f"Failed to create student: {student['name']}")
        except Exception as e:
            logger.error(f"Error creating student {student['name']}: {e}")

def seed_tasks(db: Database, tasks_data: list[dict]) -> None:
    """
    Заполняет таблицу tasks данными.
    
    Пример использования:
    tasks = [
        {
            'channel_message_id': 1001
        },
        {
            'channel_message_id': 1002
        }
    ]
    seed_tasks(db, tasks)
    """
    for task in tasks_data:
        try:
            task_id = db.task.create(
                channel_message_id=task['channel_message_id']
            )
            if task_id:
                logger.info(f"Created task for message: {task['channel_message_id']} (ID: {task_id})")
            else:
                logger.error(f"Failed to create task for message: {task['channel_message_id']}")
        except Exception as e:
            logger.error(f"Error creating task for message {task['channel_message_id']}: {e}")

def seed_answers(db: Database, answers_data: list[dict]) -> None:
    """
    Заполняет таблицу answers данными.
    
    Пример использования:
    answers = [
        {
            'student_id': 1,  # ID существующего студента
            'task_id': 1,     # ID существующей задачи
            'message_link': 'https://t.me/c/channel_id/message_id',
            'answer_status': AnswerStatus.NEEDS_REVIEW  # Опционально, по умолчанию 1
        },
        {
            'student_id': 2,
            'task_id': 1,
            'message_link': 'https://t.me/c/channel_id/message_id2',
            'answer_status': AnswerStatus.REVIEWED
        }
    ]
    seed_answers(db, answers)
    """
    for answer in answers_data:
        try:
            answer_id = db.answer.create(
                student_id=answer['student_id'],
                task_id=answer['task_id'],
                message_link=answer['message_link'],
                answer_status=answer.get('answer_status', AnswerStatus.NEEDS_REVIEW)
            )
            if answer_id:
                logger.info(f"Created answer for student {answer['student_id']} and task {answer['task_id']} (ID: {answer_id})")
            else:
                logger.error(f"Failed to create answer for student {answer['student_id']} and task {answer['task_id']}")
        except Exception as e:
            logger.error(f"Error creating answer for student {answer['student_id']} and task {answer['task_id']}: {e}")

def seed_all(db: Database, tutors: list[dict], students: list[dict], tasks: list[dict], answers: list[dict]) -> None:
    """
    Заполняет все таблицы данными.
    
    Пример использования:
    tutors = [
        {
            'telegram_id': 123456789,
            'username': 'tutor1',
            'name': 'Иван Иванов'
        }
    ]
    
    students = [
        {
            'telegram_id': 111222333,
            'username': 'student1',
            'name': 'Алексей Алексеев',
            'tutor_id': 1
        }
    ]
    
    tasks = [
        {
            'channel_message_id': 1001
        }
    ]
    
    answers = [
        {
            'student_id': 1,
            'task_id': 1,
            'message_link': 'https://t.me/c/channel_id/message_id'
        }
    ]
    
    seed_all(db, tutors, students, tasks, answers)
    """
    logger.info("Starting database seeding...")
    
    # Сначала создаем тьюторов
    seed_tutors(db, tutors)
    
    # Затем создаем студентов (они зависят от тьюторов)
    seed_students(db, students)
    
    # Создаем задачи
    seed_tasks(db, tasks)
    
    # И наконец создаем ответы (они зависят от студентов и задач)
    seed_answers(db, answers)
    
    logger.info("Database seeding completed!")

if __name__ == "__main__":
    # Пример использования:
    db = Database()
    
    # Подготовка данных
    example_tutors = []
    
    example_students = [
        # {
        #     'telegram_id': 6218907689,
        #     'username': '@testing58260',
        #     'name': 'Алексей Алексеев',
        #     'tutor_id': 1
        # }
    ]

    example_tasks = [
        # {
        #     'channel_message_id': 14
        # }
    ]

    example_answers = [
        {
            'student_id': 3,  # ID существующего студента
            'task_id': 2,     # ID существующей задачи
            'message_link': 'https://t.me/testPNA_channel/14?comment=157',
            'answer_status': AnswerStatus.NEEDS_REVIEW  # Опционально, по умолчанию 1
        },
        {
            'student_id': 3,  # ID существующего студента
            'task_id': 2,     # ID существующей задачи
            'message_link': 'https://t.me/testPNA_channel/14?comment=156',
            'answer_status': AnswerStatus.NEEDS_REVIEW  # Опционально, по умолчанию 1
        }
    ]
    
    # Заполнение базы данных
    seed_all(db, example_tutors, example_students, example_tasks, example_answers)
