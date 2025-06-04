import asyncio
import os
from dotenv import load_dotenv
from telegram_sender import initiate_login, submit_code, submit_password

# Load environment variables
load_dotenv()

async def handle_login():
    print("Welcome to Telegram Login")
    print("------------------------")
    
    # Get phone number
    phone = input("Please enter your phone number (with country code, e.g., +1234567890): ").strip()
    
    # Start login process
    print("\nInitiating login process...")
    login_result = await initiate_login(phone)
    
    if login_result.get("status") == "ALREADY_LOGGED_IN":
        print("You are already logged in!")
        return True
    
    if login_result.get("status") != "WAITING_FOR_CODE":
        print(f"Error: {login_result.get('error', 'Unknown error occurred')}")
        return False
    
    # Get verification code
    print("\nA verification code has been sent to your Telegram account.")
    code = input("Please enter the verification code: ").strip()
    
    # Submit verification code
    code_result = await submit_code(phone, code)
    
    if code_result.get("status") == "NEED_PASSWORD":
        # Handle 2FA
        print("\nTwo-factor authentication is enabled.")
        password = input("Please enter your Telegram password: ").strip()
        
        # Submit password
        password_result = await submit_password(phone, password)
        
        if password_result.get("status") == "LOGGED_IN":
            print("\nSuccessfully logged in!")
            return True
        else:
            print(f"\nError: {password_result.get('error', 'Failed to login with password')}")
            return False
    
    elif code_result.get("status") == "LOGGED_IN":
        print("\nSuccessfully logged in!")
        return True
    else:
        print(f"\nError: {code_result.get('error', 'Failed to login with code')}")
        return False

def main():
    try:
        asyncio.run(handle_login())
    except KeyboardInterrupt:
        print("\nLogin process cancelled by user.")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    main() 