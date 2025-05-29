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

def main():
    # Clear the output file if it exists
    if os.path.exists('channels_messages.txt'):
        os.remove('channels_messages.txt')
    
    # Run the async function to get channels and messages
    asyncio.run(get_channels_and_messages())

if __name__ == "__main__":
    main()