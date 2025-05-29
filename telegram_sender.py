from telethon import TelegramClient
import asyncio
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

unread_chats_limit = 10
unread_messages_limit = 100

latest_chats_limit = 10
latest_messages_limit = 200

# Access the variables
api_id = os.getenv('api_id')
api_hash = os.getenv('api_hash')

# Create a unique session name
session_name = 'my_account'

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
    if sender.username:
        info.append(f"(@{sender.username})")
        
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

async def store_messages():
    start_time = time.time()
    print(f"Starting message collection at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize the client
        client = TelegramClient(session_name, api_id, api_hash)
        
        # Start the client
        await client.start()
        
        # Create messages directories if they don't exist
        os.makedirs('messages/unread', exist_ok=True)
        os.makedirs('messages/read', exist_ok=True)
        
        # Counter for top chats
        chat_count = 0
        
        # Get all dialogs (chats, channels, groups)
        async for dialog in client.iter_dialogs():
            if chat_count >= max(unread_chats_limit, latest_chats_limit):  # Process enough chats for both operations
                break
                
            try:
                # Skip non-private chats and bots
                if not dialog.is_user or (hasattr(dialog.entity, 'bot') and dialog.entity.bot):
                    continue
                    
                safe_name = "".join(c for c in dialog.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                
                # Process unread messages
                if dialog.unread_count > 0:
                    print(f"Found {dialog.unread_count} unread messages")
                    
                    # Get unread messages
                    unread_messages = await client.get_messages(
                        dialog.id,
                        limit=min(dialog.unread_count, unread_messages_limit)  # Get only unread messages
                    )
                    
                    if unread_messages:
                        unread_filename = f"messages/unread/{safe_name}.txt"
                        unread_text = str()
                        
                        for message in unread_messages[::-1]:
                            try:
                                sender_info = get_sender_info(message)
                                if message.text:
                                    msg_text = f"{sender_info}: {message.text}\n\n{message.date}"
                                    unread_text += msg_text + "\n" + "-"*20 + "\n"
                                
                                # Write to unread file
                                with open(unread_filename, 'w', encoding='utf-8') as f:
                                    f.write(unread_text)
                            except Exception as e:
                                print(f"Error processing unread message in {dialog.name}: {str(e)}")
                                continue
                        
                        print(f"Stored {len(unread_messages)} unread messages from {dialog.name} in {unread_filename}")
                
                # Process latest messages
                latest_messages = await client.get_messages(
                    dialog.id,
                    limit=latest_messages_limit  # Get latest messages
                )
                
                if latest_messages:
                    read_filename = f"messages/read/{safe_name}.txt"
                    read_text = str()
                    
                    for message in latest_messages[::-1]:
                        try:
                            sender_info = get_sender_info(message)
                            if message.text:
                                msg_text = f"{sender_info}: {message.text}\n\n{message.date}"
                                read_text += msg_text + "\n" + "-"*20 + "\n"
                            
                            # Write to read file
                            with open(read_filename, 'w', encoding='utf-8') as f:
                                f.write(read_text)
                        except Exception as e:
                            print(f"Error processing latest message in {dialog.name}: {str(e)}")
                            continue
                    
                    print(f"Stored {len(latest_messages)} latest messages from {dialog.name} in {read_filename}")
                
                chat_count += 1  # Increment chat counter
                    
            except Exception as e:
                print(f"Error processing chat {dialog.name}: {str(e)}")
                continue
        
        # Disconnect the client
        await client.disconnect()
        
        # Calculate and display total time
        end_time = time.time()
        total_time = end_time - start_time
        print(f"\nProcess completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total execution time: {format_time(total_time)}")
        print("All messages have been stored in separate files")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Ensure the client is disconnected
        if 'client' in locals():
            await client.disconnect()

def main():
    # Run the async function to store messages
    asyncio.run(store_messages())

if __name__ == "__main__":
    main()