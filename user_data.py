import json
import os

FILE = "user_data.json"

import json
import os
from filelock import FileLock

FILE = "user_data.json"
LOCK = "user_data.json.lock" 

def load_data():
    if not os.path.exists(FILE):
        return {}
    with FileLock(LOCK):  
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)

def save_data(data):
    with FileLock(LOCK):  
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def ensure_user_entry(guild_id, member):
    data = load_data()
    guild_id = str(guild_id)
    member_id = str(member.id)
    
    if guild_id not in data:
        data[guild_id] = {"members": {}}
    if "members" not in data[guild_id]:
        data[guild_id]["members"] = {}
    if member_id not in data[guild_id]["members"]:
        data[guild_id]["members"][member_id] = {
            "nickname": member.display_name,
            "tag": str(member),
            "messages": [],
            "reminders": []
        }
    save_data(data)

def add_message(guild_id, member, message_content):
    ensure_user_entry(guild_id, member)
    data = load_data()
    messages = data[str(guild_id)]["members"][str(member.id)]["messages"]
    messages.append(message_content)
    if len(messages) > 20:
        messages.pop(0)
    save_data(data)

def save_reminder_to_user(guild_id, user_id, reminder):

    data = load_data()
    guild_id = str(guild_id)
    user_id = str(user_id)
    
    if guild_id not in data:
        data[guild_id] = {"members": {}}
    if "members" not in data[guild_id]:
        data[guild_id]["members"] = {}
    if user_id not in data[guild_id]["members"]:
        data[guild_id]["members"][user_id] = {
            "nickname": "",
            "tag": "",
            "messages": [],
            "reminders": []
        }
    
    data[guild_id]["members"][user_id]["reminders"].append(reminder)
    save_data(data)

def get_user_data(guild_id, member_id):
    data = load_data()
    return data.get(str(guild_id), {}).get("members", {}).get(str(member_id))

def load_reminders():
    data = load_data()
    reminders = []
    for guild_id, guild_data in data.items():
        members = guild_data.get("members", {})
        for member_id, member_data in members.items():
            reminders.extend(member_data.get("reminders", []))
    return reminders

def remove_reminder_by_id(reminder_id):
    data = load_data()
    changed = False
    for guild_id, guild_data in data.items():
        members = guild_data.get("members", {})
        for member_id, member_data in members.items():
            reminders = member_data.get("reminders", [])
            new_reminders = [r for r in reminders if r.get("id") != reminder_id]
            if len(new_reminders) != len(reminders):
                data[guild_id]["members"][member_id]["reminders"] = new_reminders
                changed = True
    if changed:
        save_data(data)