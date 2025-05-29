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

def get_name(message):
    sender = message.get_sender()
    if hasattr(sender, 'first_name'):  # User
        sender_info = f"{sender.first_name} {sender.last_name if sender.last_name else ''}"
    elif hasattr(sender, 'title'):  # Channel or Group
        sender_info = f"{sender.title}"
    else:
        sender_info = ""
    return sender_info

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
                # Skip groups
                if dialog.is_group:
                    print(f"\nSkipping group: {dialog.name}")
                    continue
                    
                print(f"\nProcessing {dialog.name}:")
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
                                sender = await message.get_sender()
                                if hasattr(sender, 'first_name'):  # User
                                    sender_info = f"{sender.first_name} {sender.last_name if sender.last_name else ''}"
                                elif hasattr(sender, 'title'):  # Channel or Group
                                    sender_info = f""
                                else:
                                    sender_info = "admin"
                                sender_info = sender_info + " said:\n" if sender_info else ""
                                if message.text:
                                    msg_text = sender_info + message.text + "\n\n" + str(message.date)
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
                            sender = await message.get_sender()
                            if hasattr(sender, 'first_name'):  # User
                                sender_info = f"{sender.first_name} {sender.last_name if sender.last_name else ''}"
                            elif hasattr(sender, 'title'):  # Channel or Group
                                sender_info = f""
                            else:
                                sender_info = "admin"
                            sender_info = sender_info + " said:\n" if sender_info else ""
                            sender_info = ""
                            
                            
                            if message.text:
                                msg_text = sender_info + message.text + "\n\n" + str(message.date)
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