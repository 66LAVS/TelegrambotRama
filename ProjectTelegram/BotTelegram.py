import telebot
import io

# @bot.message_handler(content_types=['text'])

bot = telebot.TeleBot("7573510567:AAEIGSRzFN9WyiVfd_IpjYo2iGPsvsRsuB4", parse_mode=None)

notes = {} # Словарь для хранения заметок
progress_bars = {} # Словарь для хранения прогрессбаров


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
 bot.reply_to(message, "привет это бот для заметок\nВыберите действие:")
 keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
 keyboard.add("Создать заметку", "Редактировать заметку", "Показать заметки")
 bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == "Создать заметку")
def newnote(message):
 send = bot.send_message(message.chat.id, 'Введи название заметки')
 bot.register_next_step_handler(send, create_note)

def create_note(message):
 note_title = message.text
 send = bot.send_message(message.chat.id, f"Введи текст заметки для {note_title}")
 bot.register_next_step_handler(send, save_note, note_title)

def save_note(message, note_title):
 note_text = message.text
 notes[note_title] = note_text
 send = bot.send_message(message.chat.id, f"Заметка '{note_title}' сохранена.")
 send = bot.send_message(message.chat.id, f"Введите количество задач для прогрессбара:")
 bot.register_next_step_handler(send, init_progressbar, note_title)

def init_progressbar(message, note_title):
 try:
  task_count = int(message.text)
  progress_bars[note_title] = [0] * task_count # Инициализируем прогрессбар
  send = bot.send_message(message.chat.id, f"Прогрессбар инициализирован для {task_count} задач.")
  send_welcome(message) # Возврат в главное меню
 except ValueError:
  bot.reply_to(message, "Введите целое число.")

@bot.message_handler(func=lambda message: message.text == "Редактировать заметку")
def update_progress(message):
  if notes:
   keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
   for note_title in notes:
    keyboard.add(note_title)
   bot.send_message(message.chat.id, "Выберите заметку для редактирования:", reply_markup=keyboard)
   bot.register_next_step_handler(message, handle_update_progress)
  else:
   bot.send_message(message.chat.id, "У вас нет сохраненных заметок.")
   send_welcome(message)

def handle_update_progress(message, note_title=None):
  note_title = message.text
  if note_title in notes:
      send = bot.send_message(message.chat.id, 'Введите число выполненных задач:')
      bot.register_next_step_handler(send, update_progress_bar, note_title)
  else:
      bot.reply_to(message, 'Заметки с таким названием не существует.')
      send_welcome(message)
def update_progress_bar(message, note_title):
    try:
        completed_tasks = int(message.text)
        if 0 <= completed_tasks <= len(progress_bars[note_title]):
            progress_bars[note_title] = [1] * completed_tasks + [0] * (len(progress_bars[note_title]) - completed_tasks)
            progress_bar = "[" + "✅" * completed_tasks + "❌" * (len(progress_bars[note_title]) - completed_tasks) + "]"  # Используем эмодзи
            bot.reply_to(message, f"Заметка: {notes[note_title]}"
                              f"\nПрогресс: {progress_bar}")
            send_welcome(message) # Возврат в главное меню
        else:
            bot.reply_to(message, "Некорректное число. Введите число в диапазоне от 0 до количества задач.")
    except ValueError:
        bot.reply_to(message, "Введите число.")

@bot.message_handler(func=lambda message: message.text == "Показать заметки")
def show_notes(message):
  if notes:
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Показать текстом", "Показать файлом")
    bot.send_message(message.chat.id, "Выберите способ отображения:", reply_markup=keyboard)
    bot.register_next_step_handler(message, show_notes_action)
  else:
    bot.send_message(message.chat.id, "У вас нет сохраненных заметок.")
    send_welcome(message)

def show_notes_action(message):
  if message.text == "Показать текстом":
    if notes:
      text = ""
      for note_title, note_text in notes.items():
          progress_bar = "[" + "✅" * progress_bars[note_title].count(1) + "❌" * progress_bars[note_title].count(0) + "]"
          text += f"Заметка: {note_title}\nТекст: {note_text}\nПрогресс: {progress_bar}\n\n"
      bot.reply_to(message, text)
    else:
      bot.send_message(message.chat.id, "У вас нет сохраненных заметок.")
    send_welcome(message)
  elif message.text == "Показать файлом":
    if notes:
      text_file = io.StringIO()
      for note_title, note_text in notes.items():
          progress_bar = "[" + "✅" * progress_bars[note_title].count(1) + "❌" * progress_bars[note_title].count(0) + "]"
          text_file.write(f"Заметка: {note_title}\nТекст: {note_text}\nПрогресс: {progress_bar}\n\n")
      text_file.seek(0)
      bot.send_document(message.chat.id, text_file, caption='Ваши заметки:')
    else:
      bot.send_message(message.chat.id, "У вас нет сохраненных заметок.")
    send_welcome(message)

bot.infinity_polling()