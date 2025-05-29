from telethon import TelegramClient
import asyncio
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import time
import json

# Load environment variables from .env file
load_dotenv()

# Message limits
unread_chats_limit = 5
unread_messages_limit = 10

latest_chats_limit = 2
latest_messages_limit = 10

# specific_chat_id = None
# specific_chat_id = 423285916
specific_chat_id = 6836049135
specific_chat_messages_limit = 100

# Access the variables
api_id = os.getenv('api_id')
api_hash = os.getenv('api_hash')

if not api_id or not api_hash:
    raise ValueError("Please set api_id and api_hash in your .env file")

# Create a unique session name
session_name = 'my_account'

clients = {}
code_store = {}  # Temporary storage for login codes

async def initiate_login(phone):
    client = TelegramClient(f"sessions/{phone}", api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        clients[phone] = client
        return {"status": "WAITING_FOR_CODE"}

    return {"status": "ALREADY_LOGGED_IN"}

async def submit_code(phone, code):
    client = clients.get(phone)
    if not client:
        return {"error": "No login in progress for this phone number"}

    try:
        await client.sign_in(phone, code)
        return {"status": "LOGGED_IN"}
    except Exception as e:
        error_msg = str(e)
        if "password" in error_msg.lower():
            # Store the client for password step
            clients[phone] = client
            return {
                "status": "NEED_PASSWORD",
                "message": "Two-factor authentication is enabled. Please enter your Telegram password to continue.",
                "next_step": "Call /submit-password endpoint with your password"
            }
        return {"error": error_msg}

async def submit_password(phone, password):
    client = clients.get(phone)
    if not client:
        return {"error": "No login in progress for this phone number"}

    try:
        await client.sign_in(password=password)
        return {"status": "LOGGED_IN"}
    except Exception as e:
        return {"error": str(e)}

def get_sender_info(message):
    """Fast method to get sender information"""
    sender = message.sender
    if not sender:
        return ""
        
    # Get basic info without additional API calls
    info = []
    if sender.first_name:
        info.append(sender.first_name)
    if sender.last_name:
        info.append(sender.last_name)
        
    return " ".join(info)

def format_time(seconds):
    """Format seconds into a human-readable string"""
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.2f} hours"

async def store_messages(chat_id=None):
    """
    Store messages from a specific chat or process all chats
    chat_id: Optional ID of a specific chat to process. If None, processes all chats as before.
    """
    start_time = time.time()
    print(f"Starting message collection at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize the client
        client = TelegramClient(session_name, api_id, api_hash)
        
        # Start the client
        await client.start()
        
        # Create messages directory if it doesn't exist
        os.makedirs('messages', exist_ok=True)
        
        # Initialize JSON structure
        messages_data = {
            "messages": {
                "most_recent": {},
                "unread": {}
            }
        }
        
        if chat_id is not None:
            # Process specific chat
            try:
                messages_data = []
                # Get the chat entity
                safe_name = "".join(c for c in str(chat_id) if c.isalnum()).rstrip()
                # safe_name = "".join(c for c in str(chat_id) if c.isalnum() or c in (' ', '-', '_')).rstrip()
                
                # Get all messages
                messages = await client.get_messages(chat_id, limit=specific_chat_messages_limit)
                
                if messages:
                    # Initialize chat messages array
                    # messages_data[safe_name] = []
                    
                    for message in messages[::-1]:
                        try:
                            sender_info = get_sender_info(message)
                            if message.text:
                                message_data = {
                                    "sender": sender_info,
                                    "message": message.text,
                                    "date": str(message.date)
                                }
                                messages_data.append(message_data)
                                # messages_data[safe_name].append(message_data)
                        except Exception as e:
                            print(f"Error processing message: {str(e)}")
                            continue
                    
                    # Write to JSON file
                    filename = f"messages/{safe_name}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(messages_data, f, ensure_ascii=False, indent=4)
                return messages_data
                
            except Exception as e:
                print(f"Error processing chat {chat_id}: {str(e)}")
                
        else:
            # Regular process for all chats
            # Counter for top chats
            chat_count = 0
            
            # Get all dialogs (chats, channels, groups)
            async for dialog in client.iter_dialogs():
                if chat_count >= max(unread_chats_limit, latest_chats_limit):
                    break
                    
                try:
                    # Skip non-private chats and bots
                    if not dialog.is_user or (hasattr(dialog.entity, 'bot') and dialog.entity.bot):
                        continue
                        
                    safe_name = "".join(c for c in dialog.name if c.isalnum()).rstrip()
                    # safe_name = "".join(c for c in dialog.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    
                    # Process unread messages
                    if dialog.unread_count > 0:
                        print(f"Found {dialog.unread_count} unread messages")
                        
                        # Get unread messages
                        unread_messages = await client.get_messages(
                            dialog.id,
                            limit=min(dialog.unread_count, unread_messages_limit)
                        )
                        
                        if unread_messages:
                            # Initialize unread messages array for this chat
                            messages_data["messages"]["unread"][safe_name] = []
                            
                            for message in unread_messages[::-1]:
                                try:
                                    sender_info = get_sender_info(message)
                                    if message.text:
                                        message_data = {
                                            "sender": sender_info,
                                            "text": message.text,
                                            "date": str(message.date)
                                        }
                                        messages_data["messages"]["unread"][safe_name].append(message_data)
                                except Exception as e:
                                    print(f"Error processing unread message in {dialog.name}: {str(e)}")
                                    continue
                            
                            print(f"Processed {len(unread_messages)} unread messages from {dialog.name}")
                    
                    # Process latest messages
                    latest_messages = await client.get_messages(
                        dialog.id,
                        limit=latest_messages_limit
                    )
                    
                    if latest_messages:
                        # Initialize most recent messages array for this chat
                        messages_data["messages"]["most_recent"][safe_name] = []
                        
                        for message in latest_messages[::-1]:
                            try:
                                sender_info = get_sender_info(message)
                                if message.text:
                                    message_data = {
                                        "name": sender_info,
                                        "text": message.text,
                                        "date": str(message.date)
                                    }
                                    messages_data["messages"]["most_recent"][safe_name].append(message_data)
                            except Exception as e:
                                print(f"Error processing latest message in {dialog.name}: {str(e)}")
                                continue
                        
                        print(f"Processed {len(latest_messages)} latest messages from {dialog.name}")
                    
                    chat_count += 1
                        
                except Exception as e:
                    print(f"Error processing chat {dialog.name}: {str(e)}")
                    continue
            
            # Write all messages to a single JSON file
            filename = "messages/all_messages.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(messages_data, f, ensure_ascii=False, indent=4)
        
        # Disconnect the client
        await client.disconnect()
        
        # Calculate and display total time
        end_time = time.time()
        total_time = end_time - start_time
        print(f"\nProcess completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total execution time: {format_time(total_time)}")
        print("All messages have been stored in JSON format")
        return messages_data
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Ensure the client is disconnected
        if 'client' in locals():
            await client.disconnect()
    
def main():
    # Run the async function to store messages
    # For specific chat:
    # asyncio.run(store_messages(chat_id=123456789))  # Replace with actual chat ID
    # For all chats:
    asyncio.run(store_messages(specific_chat_id))
    # asyncio.run(store_messages())

if __name__ == "__main__":
    main()