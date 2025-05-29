from telethon import TelegramClient
import asyncio
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

read_chats = 10

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

async def store_unread_messages():
    try:
        # Initialize the client
        client = TelegramClient(session_name, api_id, api_hash)
        
        # Start the client
        await client.start()
        
        # Create messages directory if it doesn't exist
        os.makedirs('messages', exist_ok=True)
        
        # Counter for top chats
        chat_count = 0
        
        # Get all dialogs (chats, channels, groups)
        async for dialog in client.iter_dialogs():
            if chat_count >= read_chats:  # Only process top 10 chats
                break
                
            try:
                print(f"\nProcessing {dialog.name}:")
                
                # Check if there are unread messages
                if dialog.unread_count > 0:
                    print(f"Found {dialog.unread_count} unread messages")
                    
                    # Get messages
                    messages = await client.get_messages(
                        dialog.id,
                        limit=min(dialog.unread_count, 100)  # Get only unread messages
                    )
                    
                    if messages:
                        safe_name = "".join(c for c in dialog.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        unread_filename = f"messages/{safe_name}.txt"
                        unread_text = str()
                        
                        for message in messages[::-1]:
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
                                    msg_text = sender_info + message.text
                                    unread_text += msg_text + "\n" + "-"*20 + "\n"
                                # print(f"\nMessage from {message.date}:")
                                # print(f"Text: {msg_text[:100]}..." if len(msg_text) > 100 else f"Text: {msg_text}")
                                
                                # Format message information
                                message_info = unread_text
#                                 message_info = f"""
# Chat: {dialog.name} (ID: {dialog.id})
# Date: {message.date}
# Message Text: {unread_text}
# """
                                # Write to unread file
                                with open(unread_filename, 'w', encoding='utf-8') as f:
                                    f.write(message_info)
                            except Exception as e:
                                print(f"Error processing message in {dialog.name}: {str(e)}")
                                continue
                        
                        print(f"Stored {len(messages)} messages from {dialog.name} in {unread_filename}")
                    else:
                        print(f"No messages found in {dialog.name}")
                else:
                    print(f"No unread messages in {dialog.name}")
                
                chat_count += 1  # Increment chat counter
                    
            except Exception as e:
                print(f"Error processing chat {dialog.name}: {str(e)}")
                continue
        
        # Disconnect the client
        await client.disconnect()
        print("\nAll unread messages have been stored in separate files")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Ensure the client is disconnected
        if 'client' in locals():
            await client.disconnect()

def main():
    # Run the async function to store unread messages
    asyncio.run(store_unread_messages())

if __name__ == "__main__":
    main()