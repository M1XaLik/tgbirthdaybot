import telebot # TELEGRAM
from telebot import types
import sqlite3 # DATABASE
import threading
import time
from datetime import datetime, timedelta
import re # REGULAR EXPRESSIONS
import random

import config # IMPORT ALL CONFIGS

import logging # LOGGER

# Initialize LOGGER
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s') 
logger = logging.getLogger(__name__) # CHAGE THE NAME

# Add console handler to the logger with DEBUG level
console_handler = logging.StreamHandler() # Create a stream handler for the console 
console_handler.setLevel(logging.DEBUG) # Set the logging level for the handler to DEBUG 
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')) # Set the format for log messages 
logger.addHandler(console_handler) # Add the handler to the LOGGER

# Add file handler to the logger CURRENTLY OFF
# file_handler = logging.FileHandler('app.log')
# file_handler.setLevel(logging.INFO)
# file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
# logger.addHandler(file_handler)

# INITIALISING BOT 
bot = telebot.TeleBot(config.TESTTOKEN)
print("BOT STARTED SUCCESSFULLY\a\n")

# CONNECT THE DATABASE
conn = sqlite3.connect("data/botbase.db", check_same_thread=False)
# CREATING CURSOR
cursor = conn.cursor()
# USING "?" TO PREVENT SQLinjections

# TEST COMMAND
@bot.message_handler(commands=['testgif'])
def testgif(message):
	bot.send_animation(message.chat.id, random.choice(config.birthdayGifs))
	bot.send_message(message.chat.id, random.choice(config.birthdayText))

# START COMMAND
@bot.message_handler(commands=['start'])
def start(message):
	# ANIME GIF
	hellogif = open('media/hellogif.mp4', 'rb')
	# SEND GIF & MESSAGE
	bot.send_animation(message.chat.id, hellogif)
	bot.reply_to(message, "<b>Привіт, <i>{0.first_name}</i>! \nЯ - <i>{1.first_name}</i>. Бот, створений для задовільнення особистих потреб одного збоченого покидька.😊 \nДля отримання розширеної інформації скористайся командою 👉🏿 <i>/help</i></b>".format(message.from_user, bot.get_me()), parse_mode='html')

# HELP
@bot.message_handler(commands=['help'])
def help(message):
	bot.reply_to(message, config.commandsList + "<i>\nНа даний момент бот знаходиться у розробці</i>", parse_mode='html')

# GLOBAL VARIABLES
# to add user to the db
current_name = None
current_date = None
# to check message author
message_author = None
# list to delete all previous INLINEKEYBOARDMARKUP
previous_message_ids = []

# COMMAND TO ADD NEW REMINDER & START THE CHAIN
# 1
@bot.message_handler(commands=['new'])
def new_birthday(message):

	# bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)

	global message_author
	message_author = message.from_user.id

	# INLINE BUTTON to cancel the operation
	markup = types.InlineKeyboardMarkup()
	cancel = types.InlineKeyboardButton('✕ Cancel', callback_data='CANCEL')
	markup.add(cancel)

	botreply = bot.reply_to(message, "<b>Введіть ім'я</b> \n\n<i>для коректної роботи команд рекомендовано вводити дані у відповідь на повідомлення бота</i>", parse_mode='html', reply_markup=markup)
	
	# add id of current message to the list
	previous_message_ids.append(botreply.message_id)

	bot.register_next_step_handler(botreply, get_name)
	
#2
# GET NAME FUNCTION
def get_name(message):
    try:
        # if USER == AUTHOR OF CHAIN
        if message.from_user.id == message_author:
            # if NAME != COMMAND
            if not message.text.startswith('/'):
                logger.debug(f"Received name: {message.text}")

                # ASKING A NAME FROM USER
                global current_name
                current_name = message.text

                markup = types.InlineKeyboardMarkup()
                cancel = types.InlineKeyboardButton('✕ Cancel', callback_data='CANCEL')
                markup.add(cancel)

                botreply = bot.reply_to(message, "Введіть дату у форматі \n• <b>YEAR-MONTH-DAY</b>\n• <b>РІК-МІСЯЦЬ-ДЕНЬ</b> \n\n<i>для коректної роботи команд рекомендовано вводити дані у відповідь на повідомлення бота</i>", parse_mode='html', reply_markup=markup)
                logger.debug("Prompted user for date")

                # DELETE MARKUPS
                for message_id in previous_message_ids:
                    bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message_id, reply_markup=None)
                # CLEAR LIST
                previous_message_ids.clear()
                # ADD ID OF CURRENT MESSAGE TO THE LIST
                previous_message_ids.append(botreply.message_id)

                bot.register_next_step_handler(botreply, get_date)
                logger.debug("Registered next step handler for get_date")
            else:
                logger.warning("Name cannot be a command")
                bot.reply_to(message, f"<b>✕ Операцію скасовано</b>\n\n<i>Ім'я не може бути командою</i>", parse_mode='html')

                # DELETE MARKUPS
                for message_id in previous_message_ids:
                    bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message_id, reply_markup=None)
                # CLEAR LIST
                previous_message_ids.clear()
                # STOP THE CHAIN
                bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
        elif message.from_user.id != message_author or message.text.startswith('/'):
            logger.debug("Unauthorized message or command started with '/'")
            bot.send_animation(message.chat.id, random.choice(config.nogifs))
            error_reply = bot.reply_to(message, f"<b>✕ Запущений ланцюг команд ще не завершений</b>", parse_mode='html')
            bot.register_next_step_handler(error_reply, get_name)
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        print(e)

# 3
# GET BIRTH DATE FUNCTION 
def get_date(message):
    if message.from_user.id == message_author:
        # REGULAR EXPRESION
        date_pattern = r"\d{4}-\d{2}-\d{2}"
        logger.debug(f"Received message: {message.text}")

        # WE NEED TO CHECK IF INPUT IS CORRECT
        if re.match(date_pattern, message.text):
            # REMEMBER INPUTED DATA
            global current_date
            current_date = message.text
            logger.debug(f"Valid date format: {current_date}")

            # CHAT ID
            user_id = message.chat.id

            # CHAT NAME or USERNAME
            # IF CHAT TYPE IS GROUP
            if message.chat.type in ['group', 'supergroup', 'channel']:
                # user_name = title of chat
                user_name = message.chat.title
            # IF NOT
            else:
                # IF username exists ELSE firstName
                user_name = message.chat.username if message.chat.username else message.chat.first_name

            try:
                # console test
                logger.debug(f"User ID: {user_id}, User Name: {user_name}")

                # SQL CODE
                with conn:
                    # SELECT ALL CHATS FROM DB
                    cursor.execute("SELECT * FROM user WHERE id = ?", (user_id,))
                    # IF CHAT DOES NOT EXIST
                    if not cursor.fetchall():
                        # ADD IT
                        cursor.execute("INSERT INTO user (id, chat_name) VALUES (?, ?)", (user_id, user_name))

                    cursor.execute("INSERT INTO birthday_reminder (user_id, name, date) VALUES (?, ?, ?)", (user_id, current_name, current_date))
                    # COMMIT THE TRANSACTION
                    conn.commit()
                    logger.debug("User added to database successfully")
                
                # IF SUCCESS
                bot.reply_to(message, f"✓ Користувача \"<b>{current_name}</b>\" Додано до бази ({current_date})", parse_mode='html')
                # STOP THE CHAIN
                bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
            except Exception as e:
                logger.error(f"Database error: {e}")
                bot.reply_to(message, f"<b>✕ Помилка додавання користувача до бази</b>\n\n{e}", parse_mode='html')
        else:
            logger.warning("Invalid date format")
            bot.reply_to(message, "<b>✕ Операцію скасовано</b>\n\n<b>ДАНІ ВВЕДЕНО НЕКОРЕКТНО</b>\n\nДату потрібно вносити у форматі \n• <b>YEAR-MONTH-DAY</b>\n• <b>РІК-МІСЯЦЬ-ДЕНЬ</b> \n\n<i>для коректної роботи команд рекомендовано вводити дані у відповідь на повідомлення бота</i>", parse_mode='html')

        # delete markups
        for message_id in previous_message_ids:
            bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message_id, reply_markup=None)
        # CLEAR LIST
        previous_message_ids.clear()
    elif message.from_user.id != message_author or message.text.startswith('/'):
        logger.debug("Unauthorized message or command started with '/'")
        bot.send_animation(message.chat.id, random.choice(config.nogifs))
        error_reply = bot.reply_to(message, f"<b>✕ Запущений ланцюг команд ще не завершений</b>", parse_mode='html')
        bot.register_next_step_handler(error_reply, get_date)


# CANCEL FUNCTION to end the chain
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.message:
        if call.data == 'CANCEL':
            if call.from_user.id == message_author:
                bot.reply_to(call.message, text='<b>✕ Операцію скасовано</b>',  parse_mode='html')
                try:
                    # DELETE MARKUPS
                    for message_id in previous_message_ids:
                        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=message_id, reply_markup=None)
                    # CLEAR LIST
                    previous_message_ids.clear()
                    logger.debug("Cleared previous message markups and list")
                except Exception as e:
                    logger.error(f"Error occurred while clearing markups: {e}")
                    print(e)

                bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
                logger.debug("Cleared step handler by chat ID")
            else:
                logger.warning("Unauthorized user attempted to cancel")
                bot.answer_callback_query(call.id, show_alert=False, text="✕ Ви не можете відповісти!")


# SAVE HANDLERS
bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()

# PAUSE PROCESS UNTIL A SPECIFIC HOUR AND MINUTE
def wait_until(hour, minute = 0):
	# GET CURRENT DATA AND TIME
	now = datetime.now()
	# DESIRED TIME
	target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

	# IF CURRENT TIME IS GONE, ADD ONE DAY TO OUR DESIRED TIME
	if now > target_time:
		target_time += timedelta(days=1)
	
	# SET TIMER (CALCULATE DIFFERENCE BETW CURRENT & DESIRED TIME)
	time_to_sleep = (target_time - now).total_seconds()
	print(f"Sleeping for {time_to_sleep} seconds")
	time.sleep(time_to_sleep)

# FUNCTION TO CHECK DATABASE & SEND MESSAGES
def do_reminders():
    while True:
        try:
            # WAIT UNTIL DESIRED HOUR
            wait_until(hour=0, minute=10) # 12pm
            logger.debug("Waited until desired hour")

            # GET TODAY's birthdays FROM DB 
            cursor.execute("SELECT * FROM birthday_reminder WHERE strftime('%d', date) = strftime('%d', 'now') AND strftime('%m', date) = strftime('%m', 'now')")
            conn.commit()
            logger.debug("Executed query to get today's birthdays")

            # FETCH ALL ELEMENTS
            rows = cursor.fetchall()
            logger.debug(f"Fetched {len(rows)} rows from database")

            for row in rows:
                # GET NAME FROM DB (ROW WITH NUMBER 2)
                name = row[2]
                # GET CHAT_ID FROM DB (ROW WITH NUMBER 3)
                user_id = row[3]
                logger.debug(f"Preparing to send birthday reminder for {name} to user {user_id}")

                # REMIND ABOUT BIRTHDAYS
                bot.send_message(chat_id=user_id, text=f"Сьогодні День народження в 👉🏿 {name}!")
                bot.send_animation(chat_id=user_id, animation=random.choice(config.birthdayGifs))
                bot.send_message(chat_id=user_id, text=random.choice(config.birthdayText))
                logger.debug(f"Sent birthday reminders for {name} to user {user_id}")

            logger.info("THE LOOP IS GOING TO SLEEP FOR one day")
        except Exception as e:
            logger.error(f"Error occurred in do_reminders: {e}")
            print(e)


# NEW THREAD TO CHECK IF ITS BIRTHDAY
threading.Thread(target=do_reminders).start()

# FUNCTION TO DIVIDE & SEND LONG MESSAGES WITHOUT ERROR
def send_long_messages(chat_id, text):
	# ONE MESSAGE SYMBOL LIMIT in telegram
	limit = 4096
	# cycle FOR goes through TEXT with iterator LIMIT
	for i in range(0, len(text), limit):
		# send messages separately
		bot.send_message(chat_id=chat_id, text=text[i:i+limit], parse_mode='html')

# TO DISPLAY ALL ADDED BIRTHDAYS IN THIS CHAT
@bot.message_handler(commands=['list'])
def display_birthdays(message):
	# GET CHAT ID 
	user_id = message.chat.id

	# GET SOME data
	cursor.execute(f"SELECT id, name, date FROM birthday_reminder WHERE user_id = {user_id}")
	conn.commit()

	# FETCH THEM INTO OUR ARRAY
	rows = cursor.fetchall()

	# IF ROWS EXISTS
	if rows:
		# MAKES LIST OF BIRTHDAYS
		# through the cycle && separator = \n
		birthdays_list = "\n".join([f"ID: <b><i>{id}</i></b>, Name: <b><i>{name}</i></b>, Date: <b><i>{date}</i></b>" for id, name, date in rows])
		# send message to our channel
		# message with array
		long_message = f"Дні народження в цьому чаті:\n\n{birthdays_list}"
		send_long_messages(chat_id=user_id, text=long_message)
	else:
		bot.reply_to(message, "Немає доданих днів народжень в цьому чаті.")

# DELETE BIRTHDAY from database REVIEW THIS BITCH
@bot.message_handler(commands=['delete'])
def delete_birthday(message):
    try:
        # SPLIT THE COMMAND AND GET THE ID
        command_parts = message.text.split()
        
        # CHECK if command consists of 2 PARTS and second part is NUMBER
        if len(command_parts) == 2 and command_parts[1].isdigit():
            record_id = int(command_parts[1]) # GET THE ID
            logger.debug(f"Received delete request for record_id: {record_id}")

            # SQL CODE TO DELETE RECORD BY ID
            try:
                with conn:
                    cursor.execute("DELETE FROM birthday_reminder WHERE id = ?", (record_id,))
                    logger.info(f"Deleted birthday record with ID {record_id}")
            except Exception as e:
                logger.error(f"Error occurred while deleting the record with ID {record_id}: {e}")
                bot.reply_to(message, f"<b>✕ Помилка під час видалення запису з ID {record_id}</b>\n\n{e}", parse_mode='html')
                return # Exit the function to prevent sending the success message
            
            # CONFIRMATION MESSAGE
            bot.reply_to(message, f"✓ Запис про день народження з ID {record_id} було видалено.", parse_mode='html')
        else: # IF NOT - SEND MESSAGE
            logger.warning("Invalid delete command format")
            bot.reply_to(message, "<b>✕ Помилка:</b> Невірний формат команди. Використовуйте <b>/delete ID</b>.", parse_mode='html')
    except Exception as e:
        logger.error(f"Error occurred while deleting birthday record: {e}")
        bot.reply_to(message, f"<b>✕ Помилка під час видалення запису</b>\n\n{e}", parse_mode='html')


# STARTING
# bot.infinity_polling()
# TO AVOID ERRORS WHILE LONG REQUESTS
bot.polling(none_stop=True, timeout=90, long_polling_timeout=90)

# OLD FUNCTIONS (FROM 2022)

''' IT WORKS tho
#ECHO
@bot.message_handler(content_types=['text'])
def send_echo(message):
	bot.send_message(message.chat.id, message.text)
'''
