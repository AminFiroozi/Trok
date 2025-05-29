from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
import json
import re
from telegram_sender import submit_code, initiate_login, store_messages


app = FastAPI()

# Fake user database
fake_user_db: Dict[str, Dict[str, str]] = {
    "-Nicholas": {"sender": "-Nicholas🖤", "full_sender": "Nicholas Smith"},
    "bob": {"sender": "bob", "full_sender": "Bob Johnson"},
    "carol": {"sender": "carol", "full_sender": "Carol Williams"}
}

# Fake messages database
fake_messages_db: Dict[str, List[Dict]] = {
    "-Nicholas": [
        {"sender": "-Nicholas🖤", "text": "email etemadi and mohammadi", "date": datetime.now(), "read": False},
        {"sender": "-Nicholas🖤", "text": "ask majd who can i get help from for learning ai in uni", "date": datetime.now(), "read": True}
    ],
    "bob": [
        {"sender": "bob", "text": "Hi there!", "date": datetime.now(), "read": False}
    ],
    "carol": [
        {"sender": "carol", "text": "Greetings!", "date": datetime.now(), "read": True}
    ]
}

class Message(BaseModel):
    sender: str
    text: str
    date: datetime

class MessagesResponse(BaseModel):
    messages: Dict[str, Dict[str, List[Message]]]

def remove_emoji(text: str) -> str:
    """Remove emoji characters from text"""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', text)

@app.get("/users", response_model=MessagesResponse)
async def read_users():
    """Return all users' messages categorized by most recent and unread"""
    most_recent = {}
    unread = {}
    messages_data = await store_messages()
    
    # print("Raw messages_data:", messages_data)  # Debug print
    
    # Process most recent messages
    for user_id, messages in messages_data.get("messages", {}).get("most_recent", {}).items():
        # print(f"Processing most recent messages for user {user_id}:", messages)  # Debug print
        message_objects = []
        for msg in messages:
            try:
                if isinstance(msg, str):
                    msg = json.loads(msg)
                message_objects.append(Message(
                    sender=remove_emoji(msg.get("name", msg.get("sender", ""))),
                    text=remove_emoji(msg.get("text", msg.get("message", ""))),
                    date=datetime.fromisoformat(msg.get("date", datetime.now().isoformat()))
                ))
            except Exception as e:
                print(f"Error processing message for user {user_id}: {str(e)}")
                continue
        
        if message_objects:
            most_recent[user_id] = message_objects
    
    # Process unread messages
    for user_id, messages in messages_data.get("messages", {}).get("unread", {}).items():
        # print(f"Processing unread messages for user {user_id}:", messages)  # Debug print
        message_objects = []
        for msg in messages:
            try:
                if isinstance(msg, str):
                    msg = json.loads(msg)
                message_objects.append(Message(
                    sender=remove_emoji(msg.get("name", msg.get("sender", ""))),
                    text=remove_emoji(msg.get("text", msg.get("message", ""))),
                    date=datetime.fromisoformat(msg.get("date", datetime.now().isoformat()))
                ))
            except Exception as e:
                print(f"Error processing message for user {user_id}: {str(e)}")
                continue
        
        if message_objects:
            unread[user_id] = message_objects
    
    # Sort messages by date
    for user_id in most_recent:
        most_recent[user_id] = sorted(most_recent[user_id], key=lambda x: x.date, reverse=True)
    
    return MessagesResponse(messages={
        "most_recent": most_recent,
        "unread": unread
    })

@app.get("/users/{user_id}", response_model=List[Message])
async def read_user(user_id: int):
    """Return a specific user's messages"""
    messages_data = await store_messages(user_id)
    
    # Get messages from the most_recent section
    # messages = messages_data.get("messages", {}).get("most_recent", {}).get(user_id, [])
    messages = messages_data
    
    # Convert messages to Message objects
    message_objects = []
    for msg in messages:
        try:
            if isinstance(msg, str):
                msg = json.loads(msg)
            message_objects.append(Message(
                sender=remove_emoji(msg.get("name", msg.get("sender", ""))),
                text=remove_emoji(msg.get("text", msg.get("message", ""))),
                date=datetime.fromisoformat(msg.get("date", datetime.now().isoformat()))
            ))
        except Exception as e:
            print(f"Error processing message for user {user_id}: {str(e)}")
            continue
    
    # Sort messages by date
    message_objects.sort(key=lambda x: x.date, reverse=True)
    
    return message_objects

@app.post("/auth/{phone_number}")
async def auth(phone_number: str):
    """Authenticate a user by phone number"""
    if (phone_number.startswith("+98") and len(phone_number) == 13):
        return {"status": phone_number[3:]}
    elif (phone_number.startswith("0") and len(phone_number) == 11):
        return {"status": phone_number[1:]}
    elif (phone_number.startswith("9") and len(phone_number) == 10):
        return {"status": phone_number}
    elif (phone_number.startswith("9") and len(phone_number) == 12):
        return {"status": phone_number[2:]}
    else:
        raise HTTPException(status_code=400, detail="Invalid phone number")

@app.post("/start-login")
async def start_login(request: Request):
    data = await request.json()
    phone = data["phone"]
    result = await initiate_login(phone)
    return result

@app.post("/submit-code")
async def submit_code_route(request: Request):
    data = await request.json()
    phone = data["phone"]
    code = data["code"]
    result = await submit_code(phone, code)
    return result