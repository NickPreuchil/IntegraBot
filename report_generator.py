import os
import numpy
import pandas as pd
from database import Database
from models import AnswerStatus

# Явная инициализация numpy
numpy.set_printoptions(suppress=True)

class ReportGenerator:
    def __init__(self, db: Database):
        self.db = db

    def generate_total_statistics_report(self, output_dir: str = None):
        """
        Генерирует Excel-отчет со статистикой по всем студентам
        
        :param output_dir: Директория для сохранения отчета (по умолчанию - текущая)
        :return: Путь к сгенерированному файлу отчета
        """
        # Получаем полную статистику
        query = """
        SELECT 
            t.name as tutor_name, 
            s.name as student_name, 
            s.username as student_username, 
            tasks.task_id, 
            tasks.created_at,
            COALESCE(a.answer_status, 0) as status
        FROM tutors t
        JOIN students s ON t.id = s.tutor_id
        CROSS JOIN tasks
        LEFT JOIN answers a ON a.task_id = tasks.task_id AND a.student_id = s.id
        ORDER BY t.name, s.name, tasks.task_id
        """
        
        # Выполняем запрос
        cursor = self.db.connection.cursor(dictionary=True)
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Преобразуем результаты в DataFrame
        df = pd.DataFrame(results)
        
        # Создаем колонку с отформатированной датой
        df['task_label'] = pd.to_datetime(df['created_at']).dt.strftime('Задание %d.%m.%Y %H:%M')
        
        # Создаем сводную таблицу
        pivot_df = df.pivot_table(
            index=['tutor_name', 'student_name', 'student_username'], 
            columns='task_label', 
            values='status', 
            fill_value=0
        )
        
        # Сбрасываем многоуровневый индекс
        pivot_df = pivot_df.reset_index()
        
        # Переименовываем колонки
        pivot_df.rename(columns={
            'tutor_name': 'Имя куратора', 
            'student_name': 'Имя студента', 
            'student_username': 'Username студента'
        }, inplace=True)
        
        # Определяем путь для сохранения
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Создаем имя файла с текущей датой
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f'student_statistics_{timestamp}.xlsx')
        
        # Сохраняем в Excel
        pivot_df.to_excel(output_file, index=False)
        
        return output_file

    def format_status(self, status: int) -> str:
        """Форматирование статуса для читаемого вывода"""
        status_map = {
            0: 'Не сдано',
            int(AnswerStatus.NEEDS_REVIEW): 'На проверке',
            int(AnswerStatus.NEEDS_REVISION): 'На доработке',
            int(AnswerStatus.REVIEWED): 'Проверено'
        }
        return status_map.get(status, 'Неизвестный статус')
