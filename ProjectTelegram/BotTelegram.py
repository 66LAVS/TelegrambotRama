import telebot
import io
import sqlite3

# @bot.message_handler(content_types=['text'])

bot = telebot.TeleBot("7573510567:AAEIGSRzFN9WyiVfd_IpjYo2iGPsvsRsuB4", parse_mode=None)

# Словарь для хранения заметок и прогрессбаров
notes = {}
progress_bars = {}


def create_database(db_name):
    """
    Создает базу данных SQLite.

    Args:
     db_name: Имя базы данных.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Создание таблицы
    cursor.execute("""
  CREATE TABLE IF NOT EXISTS documents (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   Note TEXT,
   Proggbar TEXT
  )
 """)

    conn.commit()
    conn.close()


def send_welcome(message, db_name):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Создать заметку", "Редактировать заметку", "Показать заметки")
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)
    bot.register_next_step_handler(message, handle_user_choice, db_name)


def handle_user_choice(message, db_name):
    if message.text == 'Создать заметку':
        newnote(message, db_name)
    elif message.text == 'Показать заметки':
        show_notes(message, db_name)
    elif message.text == "Редактировать заметку":
        handle_update_progress(message, db_name)


@bot.message_handler(commands=['start', 'help'])
def send_welcome1(message):
    bot.reply_to(message, "привет это бот для заметок\nВыберите действие:")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Создать заметку", "Редактировать заметку", "Показать заметки")
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)
    create_database('database.db')
    db_name = 'database.db'
    send_welcome(message, db_name)


def newnote(message, db_name):
    send = bot.send_message(message.chat.id, 'Введи название заметки')
    bot.register_next_step_handler(send, create_note, db_name)


def create_note(message, db_name):
    note_title = message.text
    send = bot.send_message(message.chat.id, f"Введи текст заметки для {note_title}")
    bot.register_next_step_handler(send, save_note, note_title, db_name)


def save_note(message, note_title, db_name):
    note_text = message.text
    notes[note_title] = note_text
    # conn = sqlite3.connect(db_name)
    # cursor = conn.cursor()
    # cursor.execute("INSERT INTO documents (Note) VALUES (?)",
    #                (note_text,))
    send = bot.send_message(message.chat.id, f"Заметка '{note_title}' сохранена.")
    send = bot.send_message(message.chat.id, f"Введите количество задач для прогрессбара:")
    # conn.commit()

    bot.register_next_step_handler(send, init_progressbar, note_title, db_name,note_text )

def init_progressbar(message, note_title, db_name,note_text):
  try:
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    task_count = int(message.text)
    progress_bars[note_title] = [0] * task_count# Инициализируем прогрессбар
    progbartext = '0' * task_count
    cursor.execute("INSERT INTO documents (Note, Proggbar) VALUES (?,?)",
                   (note_text,progbartext))
    send = bot.send_message(message.chat.id, f"Прогрессбар инициализирован для {task_count} задач.")
    send_welcome(message,db_name)  # Возврат в главное меню
    conn.commit()
    conn.close()
  except ValueError:
    bot.reply_to(message, "Введите целое число.")

def show_notes(message, db_name):
  conn = sqlite3.connect(db_name)
  cursor = conn.cursor()
  cursor.execute("SELECT Note, Proggbar FROM documents")
  notes_data = cursor.fetchall()
  conn.close()
  if notes_data:
    for note_text, progress_bar_data in notes_data:
      progress_bar = eval(progress_bar_data)
      progress_str = f"{sum(progress_bar)}/{len(progress_bar)}"
      bot.send_message(message.chat.id, f"Заметка: {note_text}\nПрогресс: {progress_str}")
  else:
    bot.send_message(message.chat.id, "У вас нет сохраненных заметок.")
  send_welcome(message, db_name)

def handle_update_progress(message, db_name):
  if notes:
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for note_title in notes:
      keyboard.add(note_title)
    bot.send_message(message.chat.id, "Выберите заметку для редактирования:", reply_markup=keyboard)
    bot.register_next_step_handler(message, update_progress_bar, db_name)
  else:
    bot.send_message(message.chat.id, "У вас нет сохраненных заметок.")
    send_welcome(message, db_name)

def update_progress_bar(message, db_name):
  note_title = message.text
  if note_title in progress_bars:
    send = bot.send_message(message.chat.id, f"Введите номер задачи для обновления прогресса (от 1 до {len(progress_bars[note_title])}):")
    bot.register_next_step_handler(send, update_task_progress, note_title, db_name)
  else:
    bot.send_message(message.chat.id, "Прогрессбар для этой заметки не найден.")
    handle_update_progress(message, db_name)

def update_task_progress(message, note_title, db_name):
  try:
    task_index = int(message.text) - 1
    if 0 <= task_index < len(progress_bars[note_title]):
      if progress_bars[note_title][task_index] == 0:
        progress_bars[note_title][task_index] = 1
        bot.send_message(message.chat.id, f"Задача {task_index + 1} в заметке '{note_title}' отмечена как выполненная.")
      else:
        progress_bars[note_title][task_index] = 0
        bot.send_message(message.chat.id, f"Задача {task_index + 1} в заметке '{note_title}' отмечена как невыполненная.")
      conn = sqlite3.connect(db_name)
      cursor = conn.cursor()
      cursor.execute("UPDATE documents SET Proggbar = ? WHERE Note = ?", (str(progress_bars[note_title]), note_title))
      conn.commit()
      conn.close()
    else:
      bot.send_message(message.chat.id, "Неверный номер задачи.")
  except ValueError:
    bot.reply_to(message, "Введите целое число.")
  handle_update_progress(message, db_name)

bot.polling()
