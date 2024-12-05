import os
import logging
import traceback
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from database import Database
from models import AnswerStatus
import asyncio
from report_generator import ReportGenerator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()  # This will also print to console
    ]
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

# Initialize database
db = Database(logger)
db.init_db()

# Constants
MAIN_CHANNEL_INTERNAL_ID = '-100' + os.getenv('MAIN_CHANNEL_ID')
DISCUSSION_GROUP_INTERNAL_ID = '-100' + os.getenv('DISCUSSION_GROUP_ID')

# Callback data constants
NEEDS_REVISION = "revision"
REVIEWED = "reviewed"
PREV_ANSWER = "prev"
NEXT_ANSWER = "next"
GOTO_MESSAGE = "goto"

#///////////////////////////////////////////////////////////
#|------------------ADDITIONAL FUNCTIONS-------------------|
#///////////////////////////////////////////////////////////

def get_answer_keyboard(answer: dict) -> InlineKeyboardMarkup:
    """Create inline keyboard for answer review"""
    keyboard = [
        # First row - status buttons
        [
            InlineKeyboardButton(text="⚠️ Доработка", callback_data=f"{NEEDS_REVISION}:{answer['answer_id']}"),
            InlineKeyboardButton(text="✅ Проверено", callback_data=f"{REVIEWED}:{answer['answer_id']}")
        ],
        # Second row - navigation buttons
        [
            InlineKeyboardButton(text="⬅️ Пред.", callback_data=f"{PREV_ANSWER}:{answer['answer_id']}"),
            InlineKeyboardButton(text="🔗 Ответ", url=answer['message_link']),
            InlineKeyboardButton(text="След. ➡️", callback_data=f"{NEXT_ANSWER}:{answer['answer_id']}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_answer_status_text(status: int) -> str:
    """Get human readable status text"""
    if status == 0 or status is None:  # Нет ответа
        return "Не отправлено"
    elif status == AnswerStatus.NEEDS_REVIEW:
        return "Требует проверки"
    elif status == AnswerStatus.NEEDS_REVISION:
        return "Отправлен на доработку"
    elif status == AnswerStatus.REVIEWED:
        return "Проверено"
    return "Неизвестный статус"

def format_answer_message(answer: dict) -> str:
    """Format answer message with all details"""
    created_at = datetime.fromisoformat(str(answer['created_at'])).strftime("%Y-%m-%d %H:%M:%S")
    status_text = get_answer_status_text(answer['answer_status'])
    return (
        f"📝 Ответ #{answer['answer_id']}:\n"
        f"👤 Имя: {answer['student_name']}\n"
        f"🔗 Username: @{answer['student_username']}\n"
        f"⏰ Время ответа: {created_at}\n"
        f"📊 Статус: {status_text}"
    )

async def send_answer_review_message(answer: dict, chat_id: int) -> None:
    """Send or edit message with answer details and review buttons"""
    await bot.send_message(
        chat_id=chat_id,
        text=format_answer_message(answer),
        reply_markup=get_answer_keyboard(answer)
    )

async def delete_messages_later(messages_to_delete, delay_seconds=180):
    """Delete messages after specified delay"""
    await asyncio.sleep(delay_seconds)
    for message in messages_to_delete:
        try:
            await message.delete()
        except Exception as e:
            logger.error(f"Error deleting message: {e}")

def format_status_emoji(status: int) -> str:
    """Get emoji for answer status"""
    if status == 0 or status is None:  # Нет ответа
        return "❌ "
    elif status == int(AnswerStatus.NEEDS_REVIEW):
        return "⏳ "
    elif status == int(AnswerStatus.NEEDS_REVISION):
        return "🔄 "
    elif status == int(AnswerStatus.REVIEWED):
        return "✅ "
    return "❓ "

def format_task_name(task: dict) -> str:
    """Format task name based on name and created_at fields"""
    if task['task_name']:
        return task['task_name']
    return f"Задание {task['task_created_at'].strftime('%d.%m.%Y %H:%M')}"

#///////////////////////////////////////////////////////////
#|-------------------CALLBACK FUNCTIONS--------------------|
#///////////////////////////////////////////////////////////

@dp.callback_query(F.data.startswith(f"{NEEDS_REVISION}:"))
async def handle_needs_revision(callback: types.CallbackQuery):
    """Handle 'needs revision' button press"""
    try:
        answer_id = int(callback.data.split(':')[1])
        logger.info(f"Updating answer {answer_id} to status NEEDS_REVISION")
        
        # Update answer status
        new_status = int(AnswerStatus.NEEDS_REVISION)
        logger.info(f"New status value: {new_status}")
        
        success = db.answer.update_status(answer_id, new_status)
        if success:
            # Get updated answer data
            answer = db.answer.get_by_id(answer_id)
            if answer:
                logger.info(f"Answer {answer_id} updated successfully")
                # Update message text and keyboard
                await callback.message.edit_text(
                    text=format_answer_message(answer),
                    reply_markup=get_answer_keyboard(answer)
                )
                await callback.answer(text="Статус обновлен: требуется доработка", show_alert=False)
            else:
                logger.error(f"Could not find answer {answer_id} after update")
                await callback.answer(text="Ошибка: ответ не найден после обновления", show_alert=True)
        else:
            logger.error(f"Failed to update answer {answer_id}")
            logger.error(traceback.format_exc())
            await callback.answer(text="Ошибка при обновлении статуса", show_alert=True)
    
    except Exception as e:
        logger.error(f"Error handling needs revision callback: {e}")
        await callback.answer(text="Произошла ошибка", show_alert=True)

@dp.callback_query(F.data.startswith(f"{REVIEWED}:"))
async def handle_reviewed(callback: types.CallbackQuery):
    """Handle 'reviewed' button press"""
    try:
        answer_id = int(callback.data.split(':')[1])
        logger.info(f"Updating answer {answer_id} to status REVIEWED")
        
        # Update answer status
        new_status = int(AnswerStatus.REVIEWED)
        logger.info(f"New status value: {new_status}")
        
        success = db.answer.update_status(answer_id, new_status)
        if success:
            # Get updated answer data
            answer = db.answer.get_by_id(answer_id)
            if answer:
                logger.info(f"Answer {answer_id} updated successfully")
                # Update message text and keyboard
                await callback.message.edit_text(
                    text=format_answer_message(answer),
                    reply_markup=get_answer_keyboard(answer)
                )
                await callback.answer(text="Статус обновлен: проверено", show_alert=False)
            else:
                logger.error(f"Could not find answer {answer_id} after update")
                await callback.answer(text="Ошибка: ответ не найден после обновления", show_alert=True)
        else:
            logger.error(f"Failed to update answer {answer_id}")
            await callback.answer(text="Ошибка при обновлении статуса", show_alert=True)
    
    except Exception as e:
        logger.error(f"Error handling reviewed callback: {e}")
        await callback.answer(text="Произошла ошибка", show_alert=True)

@dp.callback_query(F.data.startswith(f"{PREV_ANSWER}:"))
async def handle_prev_answer(callback: types.CallbackQuery):
    """Handle 'previous answer' button press"""
    try:
        answer_id = int(callback.data.split(':')[1])
        tutor = db.tutor.get_by_telegram_id(callback.from_user.id)
        if not tutor:
            await callback.answer(text="Эта команда доступна только для кураторов", show_alert=True)
            return

        prev_answer = db.answer.get_previous_answer(answer_id, tutor['id'])
        if prev_answer:
            await callback.message.edit_text(
                text=format_answer_message(prev_answer),
                reply_markup=get_answer_keyboard(prev_answer)
            )
            await callback.answer()
        else:
            await callback.answer(text="Это первый ответ", show_alert=True)

    except Exception as e:
        logger.error(f"Error handling previous answer callback: {e}")
        await callback.answer(text="Произошла ошибка", show_alert=True)

@dp.callback_query(F.data.startswith(f"{NEXT_ANSWER}:"))
async def handle_next_answer(callback: types.CallbackQuery):
    """Handle 'next answer' button press"""
    try:
        answer_id = int(callback.data.split(':')[1])
        tutor = db.tutor.get_by_telegram_id(callback.from_user.id)
        if not tutor:
            await callback.answer(text="Эта команда доступна только для кураторов", show_alert=True)
            return

        next_answer = db.answer.get_next_answer(answer_id, tutor['id'])
        if next_answer:
            await callback.message.edit_text(
                text=format_answer_message(next_answer),
                reply_markup=get_answer_keyboard(next_answer)
            )
            await callback.answer()
        else:
            # Проверяем, есть ли ещё ответы для проверки
            answers = db.answer.get_by_tutor(tutor['id'])
            if not answers:
                # Если ответов для проверки больше нет, показываем сообщение о завершении
                await callback.message.edit_text("✅ Все ответы проверены!")
                await callback.answer(text="Все ответы проверены", show_alert=True)
            else:
                # Если есть ещё ответы, значит это просто последний в текущем направлении
                await callback.answer(text="Это последний ответ", show_alert=True)

    except Exception as e:
        logger.error(f"Error handling next answer callback: {e}")
        await callback.answer(text="Произошла ошибка", show_alert=True)

@dp.callback_query(F.data.startswith(f"{GOTO_MESSAGE}:"))
async def handle_goto_message(callback: types.CallbackQuery):
    """Handle 'goto message' button press"""
    try:
        answer_id = int(callback.data.split(':')[1])
        
        # Get answer details
        answer = db.answer.get_by_id(answer_id)
        if not answer:
            await callback.answer("Ответ не найден")
            return

        await callback.answer(f"Переход к сообщению: {answer['message_link']}")
    
    except Exception as e:
        logger.error(f"Error handling goto message callback: {e}")
        await callback.answer("Произошла ошибка")

@dp.callback_query(F.data.startswith("stats_page:"))
async def handle_stats_pagination(callback: types.CallbackQuery):
    """Handle statistics pagination"""
    try:
        # Разбираем callback data
        _, student_id, page = callback.data.split(":")
        student_id = int(student_id)
        page = int(page)

        # Получаем информацию о студенте
        student = db.student.get_by_id(student_id)
        if not student:
            await callback.answer("Студент не найден")
            return

        # Проверяем права куратора
        tutor = db.tutor.get_by_telegram_id(callback.from_user.id)
        if not tutor or student['tutor_id'] != tutor['id']:
            await callback.answer("У вас нет прав для просмотра этой статистики")
            return

        # Получаем статистику
        answer_model = db.answer
        stats = answer_model.get_student_statistics(student_id)
        if not stats:
            await callback.answer("Не удалось получить статистику")
            return

        # Формируем общую статистику
        response = [
            f"📊 Статистика для студента {student['name']} ({student['username']})\n",
            "Общая статистика:",
            f"✅ Выполнено: {stats['summary']['reviewed']}",
            f"⏳ На проверке: {stats['summary']['needs_review']}",
            f"🔄 На доработке: {stats['summary']['needs_revision']}\n"
        ]

        # Формируем детальную статистику для текущей страницы
        tasks_per_page = 2
        total_tasks = len(stats['details'])
        total_pages = (total_tasks + tasks_per_page - 1) // tasks_per_page

        # Проверяем валидность номера страницы
        if page < 1 or page > total_pages:
            await callback.answer("Неверный номер страницы")
            return

        response.append("Детальная статистика:")
        start_idx = (page - 1) * tasks_per_page
        end_idx = min(start_idx + tasks_per_page, total_tasks)
        
        for task in stats['details'][start_idx:end_idx]:
            # response.append(
            #     f"{format_task_name(task)}: {format_status_emoji(task['status'])}"
            # )
            task_name = format_task_name(task)
            status_emoji = format_status_emoji(task['status'])
            status_text = get_answer_status_text(task['status'])

            task_line = f"{task_name}: {status_emoji} {status_text}"
            if task['message_link'] and task['status']:  # Добавляем ссылку только если есть ответ
                task_line += f" [Ссылка на ответ]({task['message_link']})"
            response.append(task_line)


        # Создаем клавиатуру с кнопками пагинации
        keyboard = []
        if total_pages > 1:
            buttons = []
            if page > 1:
                buttons.append(InlineKeyboardButton(
                    text="◀️",
                    callback_data=f"stats_page:{student_id}:{page-1}"
                ))
            buttons.append(InlineKeyboardButton(
                text=f"{page}/{total_pages}",
                callback_data="current_page"
            ))
            if page < total_pages:
                buttons.append(InlineKeyboardButton(
                    text="▶️",
                    callback_data=f"stats_page:{student_id}:{page+1}"
                ))
            keyboard.append(buttons)

        # Обновляем сообщение
        await callback.message.edit_text(
            "\n".join(response),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard) if keyboard else None
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error handling stats pagination: {e}")
        await callback.answer("Произошла ошибка при обновлении статистики")

@dp.callback_query(F.data.startswith("confirm_remove:"))
async def handle_confirm_remove(callback: types.CallbackQuery):
    """Handle student removal confirmation"""
    try:
        # Получаем ID студента из callback data
        student_id = int(callback.data.split(":")[1])

        # Получаем информацию о студенте
        student = db.student.get_by_id(student_id)
        if not student:
            await callback.answer("Студент не найден")
            return

        # Проверяем права куратора
        tutor = db.tutor.get_by_telegram_id(callback.from_user.id)
        if not tutor or student['tutor_id'] != tutor['id']:
            await callback.answer("У вас нет прав для удаления этого студента")
            return

        # Удаляем студента
        if db.student.delete(student_id):
            await callback.message.edit_text(
                f"✅ Студент {student['name']} (@{student['username']}) успешно удален"
            )
        else:
            await callback.message.edit_text("❌ Не удалось удалить студента")

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in confirm_remove: {e}")
        await callback.answer("Произошла ошибка при удалении студента")

@dp.callback_query(F.data == "cancel_remove")
async def handle_cancel_remove(callback: types.CallbackQuery):
    """Handle student removal cancellation"""
    try:
        await callback.message.edit_text("❌ Удаление студента отменено")
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in cancel_remove: {e}")
        await callback.answer("Произошла ошибка")

#///////////////////////////////////////////////////////////
#|--------------------COMMANDS HANDLERS--------------------|
#///////////////////////////////////////////////////////////

@dp.message(Command("stats"))
async def handle_stats_command(message: types.Message):
    """Handle the /stats command from tutors"""
    try:
        # Get tutor ID from message
        tutor_id = message.from_user.id
        
        # Get student ID from command arguments
        command_parts = message.text.split()
        if len(command_parts) != 2:
            await message.reply("Пожалуйста, укажите ID студента после команды /stats")
            return

        # Проверяем, что запрос от куратора
        tutor = db.tutor.get_by_telegram_id(tutor_id)
        if not tutor:
            await message.reply("Эта команда доступна только для кураторов")
            return
        
        try:
            student_telegram_id = int(command_parts[1])
        except ValueError:
            await message.reply("ID студента должен быть числом")
            return
        
        # Получаем информацию о студенте
        student = db.student.get_by_telegram_id(student_telegram_id)
        if not student:
            await message.reply("Студент не найден")
            return

        # Проверяем, что студент закреплен за этим куратором
        if student['tutor_id'] != tutor['id']:
            await message.reply("Этот студент не закреплен за вами")
            return
        
        # Get statistics
        answer_model = db.answer
        stats = answer_model.get_student_statistics(student['id'])
        
        if not stats:
            await message.reply("Не удалось получить статистику")
            return

        response = [
            f"📊 Статистика для студента {student['name']} ({student['username']})\n\n",
            "Общая статистика:",
            f"✅ Выполнено: {stats['summary']['reviewed']}",
            f"⏳ На проверке: {stats['summary']['needs_review']}",
            f"🔄 На доработке: {stats['summary']['needs_revision']}\n"
        ]
        
        # Count totals
        total_tasks = len(stats)
        completed_tasks = sum(1 for stat in stats if stat['status'] == AnswerStatus.REVIEWED.value)
        needs_review = sum(1 for stat in stats if stat['status'] == AnswerStatus.NEEDS_REVIEW.value)
        needs_revision = sum(1 for stat in stats if stat['status'] == AnswerStatus.NEEDS_REVISION.value)
        
        # Add summary
        msg += f"Всего заданий: {total_tasks}\n"
        msg += f"✅ Выполнено: {completed_tasks}\n"
        msg += f"👀 На проверке: {needs_review}\n"
        msg += f"🔄 На доработке: {needs_revision}\n\n"
        
        # Add details for each task
        msg += "Детали по заданиям:\n"
        for stat in stats:
            task_name = format_task_name(stat)
            status_emoji = format_status_emoji(stat['status'])
            status_text = get_answer_status_text(stat['status'])
            
            task_line = f"{task_name}: {status_emoji} {status_text}"
            if stat['message_link'] and stat['status']:  # Добавляем ссылку только если есть ответ
                task_line += f" [Ссылка на ответ]({stat['message_link']})"
            msg += task_line + "\n"

        # Формируем детальную статистику с пагинацией
        page = 1
        tasks_per_page = 10
        total_tasks = len(stats['details'])
        total_pages = (total_tasks + tasks_per_page - 1) // tasks_per_page

        response.append("Детальная статистика:")
        start_idx = 0
        end_idx = min(tasks_per_page, total_tasks)

        keyboard = []
        if total_pages > 1:
            buttons = []
            if page > 1:
                buttons.append(InlineKeyboardButton(
                    text="◀️",
                    callback_data=f"stats_page:{student['id']}:{page - 1}"
                ))
            buttons.append(InlineKeyboardButton(
                text=f"{page}/{total_pages}",
                callback_data="current_page"
            ))
            if page < total_pages:
                buttons.append(InlineKeyboardButton(
                    text="▶️",
                    callback_data=f"stats_page:{student['id']}:{page + 1}"
                ))
            keyboard.append(buttons)

        await message.reply(
            "\n".join(response),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard) if keyboard else None
        )

        # Send message with statistics
        await message.reply(msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        logger.error(traceback.format_exc())

@dp.message(Command("rename_task"))
async def handle_rename_task(message: types.Message):
    """Handle task renaming command"""
    try:
        # Проверяем, что запрос от куратора
        tutor = db.tutor.get_by_telegram_id(message.from_user.id)
        if not tutor:
            await message.reply("Эта команда доступна только для кураторов")
            return

        # Разбираем текст сообщения
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await message.reply(
                "Формат команды: /rename_task <ссылка_на_задание> <новое_название>\n"
                "Пример: /rename_task https://t.me/channel/123 Домашнее задание №1"
            )
            return

        # Извлекаем message_id из ссылки (последний элемент)
        try:
            message_id = int(parts[1].split('/')[-1])
        except (ValueError, IndexError):
            await message.reply("Некорректная ссылка на задание. Убедитесь, что в конце ссылки указан message_id")
            return

        # Получаем новое название
        new_name = parts[2].strip()

        # Проверяем существование задания
        task = db.task.get_by_channel_message(message_id)
        if not task:
            await message.reply(f"Задание с ID {message_id} не найдено")
            return

        # Обновляем название
        if db.task.update_name(message_id, new_name):
            await message.reply(f"Название задания обновлено на: {new_name}")
        else:
            await message.reply("Не удалось обновить название задания")

    except Exception as e:
        logger.error(f"Error in rename_task: {e}")
        await message.reply("Произошла ошибка при обновлении названия задания")

@dp.message(Command("report"))
async def handle_report_command(message: types.Message):
    """Generate and send total statistics report"""
    try:
        # Проверяем, что запрос от куратора
        tutor = db.tutor.get_by_telegram_id(message.from_user.id)
        if not tutor:
            await message.reply("Эта команда доступна только для кураторов")
            return

        # Создаем генератор отчетов
        report_generator = ReportGenerator(db)
        
        # Генерируем отчет
        report_path = report_generator.generate_total_statistics_report()
        
        # Отправляем файл
        with open(report_path, 'rb') as report_file:
            await message.answer_document(
                types.input_file.BufferedInputFile(
                    report_file.read(), 
                    filename=os.path.basename(report_path)
                ),
                caption="Отчет по статистике студентов"
            )
        
        # Удаляем файл после отправки
        os.remove(report_path)

    except Exception as e:
        logger.error(f"Error generating report: {e}")
        await message.reply("Произошла ошибка при генерации отчета")

@dp.message(Command("add_student"))
async def handle_add_student(message: types.Message, bot: Bot):
    """Handle add student command from tutor"""
    try:
        # Проверяем, что запрос от куратора
        tutor = db.tutor.get_by_telegram_id(message.from_user.id)
        if not tutor:
            await message.reply("Эта команда доступна только для кураторов")
            return

        # Разбираем аргументы команды
        args = message.text.split()
        if len(args) != 2:
            await message.reply(
                "Формат команды: /add_student <telegram_id>\n"
                "Пример: /add_student 123456789"
            )
            return

        try:
            student_telegram_id = int(args[1])
        except ValueError:
            await message.reply("Telegram ID должен быть числом")
            return

        # Проверяем, не существует ли уже такой студент
        existing_student = db.student.get_by_telegram_id(student_telegram_id)
        if existing_student:
            await message.reply(f"Студент с Telegram ID {student_telegram_id} уже существует")
            return

        # Получаем информацию о пользователе из главного канала
        try:
            chat_member = await bot.get_chat_member(
                chat_id=MAIN_CHANNEL_INTERNAL_ID,
                user_id=student_telegram_id
            )

            if not chat_member.user:
                await message.reply("Не удалось получить информацию о пользователе")
                return

            if db.student.create(student_telegram_id, tutor['id'], chat_member.user.username, chat_member.user.full_name):
                await message.reply(
                    f"✅ Студент успешно добавлен:\n"
                    f"Имя: {chat_member.user.full_name}\n"
                    f"Username: @{chat_member.user.username}"
                )

                student_data = {
                    'telegram_id': student_telegram_id,
                    'name': chat_member.user.full_name,
                    'username': chat_member.user.username,
                    'tutor_id': tutor['id']
                }
                logger.info(f"Created new student: {student_data}")
            else:
                await message.reply("❌ Не удалось создать студента")

        except TelegramBadRequest as e:
            await message.reply(
                "Пользователь не найден в главном канале. "
                "Убедитесь, что пользователь является участником канала."
            )

    except Exception as e:
        logger.error(f"Error in add_student: {e}")
        await message.reply("Произошла ошибка при добавлении студента")

@dp.message(Command("check"))
async def handle_check_command(message: types.Message):
    """Handle the /check command from tutors"""
    try:
        # Get tutor by telegram_id
        tutor = db.tutor.get_by_telegram_id(message.from_user.id)
        if not tutor:
            await message.reply("Эта команда доступна только для кураторов.")
            return

        # Get answers that need review
        answers = db.answer.get_by_tutor(tutor['id'])
        if not answers:
            # Отправляем сообщение об отсутствии ответов
            bot_response = await message.reply("У ваших студентов нет ответов для проверки")

            # Запускаем асинхронное удаление сообщений
            asyncio.create_task(delete_messages_later(
                [message, bot_response],
                delay_seconds=180  # 3 минуты
            ))
            return

        # Send first answer for review
        await send_answer_review_message(answers[0], message.chat.id)

    except Exception as e:
        logger.error(f"Error handling check command: {e}")
        await message.reply("Произошла ошибка при обработке команды.")

@dp.message(Command("my_students"))
async def handle_my_students(message: types.Message):
    """Handle my students command from tutor"""
    try:
        # Проверяем, что запрос от куратора
        tutor = db.tutor.get_by_telegram_id(message.from_user.id)
        if not tutor:
            await message.reply("Эта команда доступна только для кураторов")
            return

        # Получаем список студентов
        students = db.student.get_by_tutor(tutor['id'])
        if not students:
            await message.reply("У вас пока нет студентов")
            return

        # Формируем сообщение со списком
        response = ["📚 Список ваших студентов:"]
        for i, student in enumerate(students, 1):
            username = f"@{student['username']}" if student['username'] else "нет username"
            response.append(f"{i}. {student['name']} ({username})")

        await message.reply("\n".join(response))

    except Exception as e:
        logger.error(f"Error in my_students: {e}")
        await message.reply("Произошла ошибка при получении списка студентов")

@dp.message(Command("remove_student"))
async def handle_remove_student(message: types.Message):
    """Handle remove student command from tutor"""
    try:
        # Проверяем, что запрос от куратора
        tutor = db.tutor.get_by_telegram_id(message.from_user.id)
        if not tutor:
            await message.reply("Эта команда доступна только для кураторов")
            return

        # Разбираем аргументы команды
        args = message.text.split()
        if len(args) != 2:
            await message.reply(
                "Формат команды: /remove_student <telegram_id>\n"
                "Пример: /remove_student 123456789"
            )
            return

        try:
            student_telegram_id = int(args[1])
        except ValueError:
            await message.reply("Telegram ID должен быть числом")
            return

        # Получаем информацию о студенте
        student = db.student.get_by_telegram_id(student_telegram_id)
        if not student:
            await message.reply("Студент не найден")
            return

        # Проверяем, что студент закреплен за этим куратором
        if student['tutor_id'] != tutor['id']:
            await message.reply("Этот студент не закреплен за вами")
            return

        # Подтверждаем удаление с помощью inline кнопок
        keyboard = [
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=f"confirm_remove:{student['id']}"
                ),
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data="cancel_remove"
                )
            ]
        ]

        await message.reply(
            f"Вы действительно хотите удалить студента {student['name']} (@{student['username']})?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

    except Exception as e:
        logger.error(f"Error in remove_student: {e}")
        await message.reply("Произошла ошибка при удалении студента")

#///////////////////////////////////////////////////////////
#|-----------------CHANNEL EVENTS HANDLERS-----------------|
#///////////////////////////////////////////////////////////

@dp.channel_post()
async def handle_channel_post(message: types.Message):
    """Handle new posts in the channel"""
    try:
        # Check if this message is from our main channel
        if str(message.chat.id) != MAIN_CHANNEL_INTERNAL_ID:
            return

        # Get message text (can be in text or caption)
        post_text = message.text or message.caption or ""
        
        # Check if post contains the test keyword
        if os.getenv('CHANNEL_POST_TRIGGER_TEXT') not in post_text:
            logger.info(f"Skipping post {message.message_id} - no test keyword found")
            return

        # Create new task from the channel message
        task_id = db.task.create(channel_message_id=message.message_id)
        
        if task_id:
            logger.info(
                f"Created new task (ID: {task_id}) from channel message {message.message_id}. "
                f"Text: {post_text[:100]}..."
            )
        else:
            logger.error(f"Failed to create task from channel message {message.message_id}")
            
    except Exception as e:
        logger.error(f"Error handling channel post: {e}")

@dp.message()
async def handle_message(message: types.Message):
    """Handle messages in discussion group"""
    try:
        # Only process messages from the discussion group
        if str(message.chat.id) != DISCUSSION_GROUP_INTERNAL_ID:
            return

        # Only process replies to channel posts
        if not message.reply_to_message:
            return

        # Проверяем наличие триггер-текста в комментарии
        if os.getenv('ANSWER_TRIGGER_TEXT') not in message.text:
            logger.info(f"Message doesn't contain trigger text: {message.text}")
            return

        # Получаем информацию о студенте
        student = db.student.get_by_telegram_id(message.from_user.id)
        if not student:
            logger.warning(f"Message from non-student user: {message.from_user.id}")
            return

        # Get the channel message ID that this comment is replying to
        channel_message_id = message.reply_to_message.forward_from_message_id
        
        # Get task by channel message ID
        task = db.task.get_by_channel_message(channel_message_id)
        if not task:
            logger.error(f"No task found for channel message: {channel_message_id}")
            return

        # Create message link
        message_link = f"https://t.me/c/{os.getenv('DISCUSSION_GROUP_ID')}/{message.message_id}"

        # Create new answer
        answer_id = db.answer.create(
            student_id=student['id'],
            task_id=task['task_id'],
            message_link=message_link
        )
        
        if answer_id:
            logger.info(
                f"Created answer (ID: {answer_id}) from student {student['name']} "
                f"for task {task['task_id']}"
            )
        else:
            logger.error(
                f"Failed to create answer from student {student['name']} "
                f"for task {task['task_id']}"
            )

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        logger.error(traceback.format_exc())

@dp.edited_message()
async def handle_edited_message(message: types.Message):
    """Handle edited messages in discussion group"""
    try:
        # Only process messages from the discussion group
        if str(message.chat.id) != DISCUSSION_GROUP_INTERNAL_ID:
            return

        # Only process replies to channel posts
        if not message.reply_to_message:
            return

        # Проверяем наличие триггер-текста в комментарии
        if os.getenv('ANSWER_TRIGGER_TEXT') not in message.text:
            logger.info(f"Edited message doesn't contain trigger text: {message.text}")
            return

        # Создаем ссылку на сообщение
        message_link = f"https://t.me/c/{os.getenv('DISCUSSION_GROUP_ID')}/{message.message_id}"

        # Получаем существующий ответ по ссылке на сообщение
        existing_answer = db.answer.get_by_message_link(message_link)
        if not existing_answer:
            logger.info(f"No answer found for message link: {message_link}")
            student = db.student.get_by_telegram_id(message.from_user.id)
            if not student:
                logger.warning(f"Message from non-student user: {message.from_user.id}")
                return

            channel_message_id = message.reply_to_message.forward_from_message_id
            task = db.task.get_by_channel_message(channel_message_id)
            if not task:
                logger.error(f"No task found for channel message: {channel_message_id}")
                return

            answer_id = db.answer.create(
                student_id=student['id'],
                task_id=task['task_id'],
                message_link=message_link
            )

            if answer_id:
                logger.info(
                    f"Created answer (ID: {answer_id}) (edited msg) from student {student['name']} "
                    f"for task {task['task_id']}"
                )
            else:
                logger.error(
                    f"Failed to create answer (edited msg) from student {student['name']} "
                    f"for task {task['task_id']}"
                )

            existing_answer = db.answer.get_by_message_link(message_link)

        # Если ответ требует доработки, обновляем его статус
        if existing_answer['answer_status'] == int(AnswerStatus.NEEDS_REVISION):
            db.answer.update(
                existing_answer['answer_id'],
                {
                    'answer_status': int(AnswerStatus.NEEDS_REVIEW)
                }
            )
            logger.info(f"Updated answer {existing_answer['id']} status to NEEDS_REVIEW")

    except Exception as e:
        logger.error(f"Error handling edited message: {e}")

async def main():
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(token=os.getenv('BOT_TOKEN'))
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
