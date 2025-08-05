import json
import os

FILE = "user_data.json"

def load_data():
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_reminders():
    data = load_data()
    reminders = []
    for guild_id, guild_data in data.items():
        members = guild_data.get("members", {})
        for member_id, member_data in members.items():
            reminders.extend(member_data.get("reminders", []))
    return reminders

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

    user_data = data[guild_id]["members"][user_id]

    if "reminders" not in user_data or not isinstance(user_data["reminders"], list):
        user_data["reminders"] = []

    user_data["reminders"].append(reminder)


    save_data(data)



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
