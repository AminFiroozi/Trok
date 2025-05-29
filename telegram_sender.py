from telethon import TelegramClient
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the variables
api_id = os.getenv('api_id')
api_hash = os.getenv('api_hash')

# Create a unique session name
session_name = 'my_account'

async def get_channels_and_messages():
    try:
        # Initialize the client
        client = TelegramClient(session_name, api_id, api_hash)
        
        # Start the client
        await client.start()
        
        # Get all dialogs (chats, channels, groups)
        async for dialog in client.iter_dialogs():
            try:
                # Get the last message from the dialog
                messages = await client.get_messages(dialog.id, limit=1)
                if messages:
                    last_message = messages[0].text
                    # Write to file
                    with open('channels_messages.txt', 'a', encoding='utf-8') as f:
                        f.write(f"{dialog.id}: {last_message}\n")
                    print(f"Processed channel: {dialog.name}")
            except Exception as e:
                print(f"Error processing channel {dialog.name}: {str(e)}")
                continue
        
        # Disconnect the client
        await client.disconnect()
        print("\nChannel messages have been saved to 'channels_messages.txt'")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Ensure the client is disconnected
        if 'client' in locals():
            await client.disconnect()

async def send_message(recipient, message):
    try:
        # Initialize the client
        client = TelegramClient(session_name, api_id, api_hash)
        
        # Start the client
        await client.start()
        
        # Send the message
        await client.send_message(recipient, message)
        print(f"Message sent successfully to {recipient}")
        
        # Disconnect the client
        await client.disconnect()
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Ensure the client is disconnected
        if 'client' in locals():
            await client.disconnect()

async def forward_last_message(source_chat, target_chat):
    try:
        # Initialize the client
        client = TelegramClient(session_name, api_id, api_hash)
        
        # Start the client
        await client.start()
        
        # Get the last message from source chat
        messages = await client.get_messages(source_chat, limit=1)
        
        if messages:
            last_message = messages[0]
            
            # Forward the message to target chat
            await client.forward_messages(
                target_chat,
                last_message
            )
            print(f"Successfully forwarded message from {source_chat} to {target_chat}")
        else:
            print(f"No messages found in {source_chat}")
        
        # Disconnect the client
        await client.disconnect()
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Ensure the client is disconnected
        if 'client' in locals():
            await client.disconnect()

async def send_message_info(source_chat, target_chat):
    try:
        # Initialize the client
        client = TelegramClient(session_name, api_id, api_hash)
        
        # Start the client
        await client.start()
        
        # Get the last message from source chat
        messages = await client.get_messages(source_chat, limit=1)
        
        if messages:
            message = messages[0]
            
            # Get sender information
            sender = await message.get_sender()
            sender_info = f"Sender: {sender.first_name} {sender.last_name if sender.last_name else ''} (@{sender.username if sender.username else 'No username'})"
            
            # Format message information
            message_info = f"""
📨 Message Information:
{sender_info}
Message ID: {message.id}
Date: {message.date}
Edit Date: {message.edit_date if message.edit_date else 'Not edited'}
Message Type: {message.media.__class__.__name__ if message.media else 'Text'}
Message Text: {message.text if message.text else 'No text content'}
Views: {message.views if hasattr(message, 'views') else 'N/A'}
Forwards: {message.forwards if hasattr(message, 'forwards') else 'N/A'}
"""
            
            # Send the formatted information to target chat
            await client.send_message(target_chat, message_info)
            print(f"Successfully sent message info from {source_chat} to {target_chat}")
        else:
            print(f"No messages found in {source_chat}")
        
        # Disconnect the client
        await client.disconnect()
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Ensure the client is disconnected
        if 'client' in locals():
            await client.disconnect()

def main():
    # Clear the output file if it exists
    if os.path.exists('channels_messages.txt'):
        os.remove('channels_messages.txt')
    
    # Run the async function to get channels and messages
    # asyncio.run(get_channels_and_messages())

    # Get source and target chat IDs from user input
    source_chat = input("Enter the source chat ID or username: ")
    target_chat = input("Enter the target chat ID or username: ")
    
    # Run the async function
    asyncio.run(send_message_info(source_chat, target_chat))

if __name__ == "__main__":
    main()