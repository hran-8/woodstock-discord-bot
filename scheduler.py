import asyncio
from storage import load_reminders, remove_reminder_by_id
from user_data import get_user_data
from ollama import query_ollama, PERSONALITY
from clock import get_accurate_utc_timestamp


async def reminder_loop(bot): 
    await bot.wait_until_ready()

    while not bot.is_closed(): 
        now = get_accurate_utc_timestamp()
        reminders = load_reminders()

        for r in reminders: 
            if now >= r["time"]: 
                try: 
                    channel = bot.get_channel(r["channel_id"])
                    if not channel:
                        continue

                    guild_id = str(channel.guild.id)
                    member_id = r["user_id"]
                    user_data = get_user_data(guild_id, member_id)

                    messages = user_data.get("messages", []) if user_data else []
                    recent_context = "\n".join(messages[-20:]) if messages else "(no message history)"

                    llama_input = [
                    PERSONALITY,
                    {
                        "role": "user",
                        "content": (
                            f"You need to remind this user about something they asked you to remember: \"{r['text']}\"\n"
                            "Here are their recent messages:\n"
                            f"{recent_context}\n"
                            "Remind them about their own reminder. "
                            "Make it clear this is THEIR reminder that THEY set. "
                            "Keep it short and natural."
                            "Include what they wanted to be reminded about so they remember what it was."
                        )
                    }
                    ]

                    reply = await query_ollama("llama3", llama_input)
                    await channel.send(f"{r['user_mention']} {reply}")

                except Exception as e:
                    print("Error delivering reminder:", e)

                remove_reminder_by_id(r["id"])

        await asyncio.sleep(10)
