from telethon import TelegramClient
import asyncio
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

n = 100

# Access the variables
api_id = os.getenv('api_id')
api_hash = os.getenv('api_hash')

# Create a unique session name
session_name = 'my_account'

async def store_latest_messages():
    try:
        # Initialize the client
        client = TelegramClient(session_name, api_id, api_hash)
        
        # Start the client
        await client.start()
        
        # Create messages directory if it doesn't exist
        os.makedirs('messages', exist_ok=True)
        
        # Get all dialogs (chats, channels, groups)
        async for dialog in client.iter_dialogs():
            try:
                print(f"\nProcessing {dialog.name}:")
                
                # Get only the last message
                messages = await client.get_messages(
                    dialog.id,
                    limit=n  # Get only the last message
                )
                
                if messages:
                    message = messages[0]  # Get the first (and only) message
                    safe_name = "".join(c for c in dialog.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    filename = f"messages/{dialog.id}_{safe_name}.txt"
                    total_text = str()
                    for message in messages:
                    # Create filename with chat ID and name
                        
                        # Print message info for debugging
                        msg_text = message.text if message.text else "No text content"
                        total_text += msg_text + "\n" + "-"*20 +"\n"
                        print(f"\nLast message from {message.date}:")
                        print(f"Text: {msg_text[:100]}..." if len(msg_text) > 100 else f"Text: {msg_text}")
                        
                    # Get sender information based on chat type
                    try:
                        sender = await message.get_sender()
                        if hasattr(sender, 'first_name'):  # User
                            sender_info = f"Sender: {sender.first_name} {sender.last_name if sender.last_name else ''} (@{sender.username if sender.username else 'No username'})"
                        elif hasattr(sender, 'title'):  # Channel or Group
                            sender_info = f"Sender: {sender.title}"
                        else:
                            sender_info = "Sender: Unknown"
                    except Exception:
                        sender_info = "Sender: Unknown"
                    
                    # Format message information
                    message_info = f"""
📨 Last Message Information:
Chat: {dialog.name} (ID: {dialog.id})
{sender_info}
Message ID: {message.id}
Date: {message.date}
Edit Date: {message.edit_date if message.edit_date else 'Not edited'}
Message Type: {message.media.__class__.__name__ if message.media else 'Text'}
Message Text: {total_text if total_text else 'No text content'}
Views: {message.views if hasattr(message, 'views') else 'N/A'}
Forwards: {message.forwards if hasattr(message, 'forwards') else 'N/A'}
"""
                    # Write to file
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(message_info)
                    
                    print(f"Stored last message from {dialog.name} in {filename}")
                else:
                    print(f"No messages found in {dialog.name}")
                    
            except Exception as e:
                print(f"Error processing chat {dialog.name}: {str(e)}")
                continue
        
        # Disconnect the client
        await client.disconnect()
        print("\nAll last messages have been stored in separate files")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Ensure the client is disconnected
        if 'client' in locals():
            await client.disconnect()

def main():
    # Run the async function to store latest messages
    asyncio.run(store_latest_messages())

if __name__ == "__main__":
    main()