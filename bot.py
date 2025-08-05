import discord
from discord.ext import commands
from discord import File
from datetime import datetime, timezone
import os
from discord import app_commands
from ollama import PERSONALITY, query_ollama
import asyncio
import uuid 
from scheduler import reminder_loop 
from storage import save_reminder_to_user
from user_data import ensure_user_entry, add_message, get_user_data
from parser import parse_datetime, get_now_timestamp
from dotenv import load_dotenv
import time

import sys 

MODEL_LIST = [
    "flanimeIllustriousXL_v16",
    "noobai",
    "novaAnimeXL_ilV90",
    "animagineXL40_v4Opt"
]

target_dir = os.path.abspath(r"C:\dsektop\stablediffusion\stable-diffusion-webui")
if target_dir not in sys.path: 
    sys.path.insert(0, target_dir)


from generate_mascot import generate


load_dotenv()
token = os.getenv('BOT_TOKEN')



intents = discord.Intents.default()
intents.message_content = True  

bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')
    bot.loop.create_task(reminder_loop(bot))
    await tree.sync()



@tree.command(name="gen", description="Generates an image from prompt")
@app_commands.describe(
    model="Type to search model",
    prompt="Prompt text, comma-separate tags (e.g. cute cat, orange fur)", 
    neg_prompt="Negative prompt text (tags excluded from generation), comma-separate tags (e.g. explicit, nsfw)",
    width="Set the width of image (Pls something under 1500)",
    height="Set the height of image (Pls something under 1500 pls)",
    censor="Type on/off to choose whether to censor explicit tags",
    cfg_scale="Change the cfg scale",
    steps="Change the steps"
)
# @app_commands.choices(
#     model=[
#         app_commands.Choice(name="FL Anime Illustrious XL", value="flanimeIllustriousXL_v16"),
#         app_commands.Choice(name="Janku NSFW", value="JANKUV4NSFWTrainedNoobaiEPS_v40"),
#         app_commands.Choice(name="Nova Anime XL", value="novaAnimeXL_ilV90")
#     ]
# )
@app_commands.choices(
    censor=[
        app_commands.Choice(name="On", value="on"),
        app_commands.Choice(name="Off", value="off")
    ]
)
async def gen(
    interaction: discord.Interaction,
    prompt:str,
    model: str="noobai",
    neg_prompt: str="",
    width: int=612,
    height: int=612,
    censor: app_commands.Choice[str] = None,
    cfg_scale: int=5,
    steps: int=10,
): 
    user_tag = interaction.user.mention

    # check model 
    if model not in MODEL_LIST:
        model_string = "" 
        for model in MODEL_LIST: 
            model_string += model + " | "
        await interaction.response.send_message(f"Invalid model. Choose between: {model_string}", ephemeral=True)
        return

    # default censor true if none provided
    censor_bool = True if censor is None or censor.value.strip().lower() == "on" else False
    censored_words = ""
    
    await interaction.response.send_message("Generating very slowly... fund me more gpu")
    msg = await interaction.original_response()
    print(f"width: {width}, height: {height}")
    if censor_bool: 
        image_path = await generate_image_async(prompt, neg_prompt + censored_words, path=r"C:\dsektop\woodstock", model=model, width=width, height=height, cfg_scale=cfg_scale, steps=steps)
    else:
        image_path = await generate_image_async(prompt, neg_prompt, path=r"C:\dsektop\woodstock", model=model, width=width, height=height, steps=steps, cfg_scale=cfg_scale)


    if image_path and os.path.exists(image_path): 
        if wait_for_file(image_path):
            # print(f"The user's neg prompts are: {neg_prompt}")
            neg_text = f"\n**Negative Prompt:** {neg_prompt}" if neg_prompt != "" else "\n**Negative Prompt:** _None_"
            await interaction.followup.send(
                content=f"{user_tag} used /gen\n**Prompt:** {prompt}{neg_text}\n**Dimensions:** {width} x {height}\n**Model:** {model}\n**CFG Scale:** {cfg_scale}\n**Steps**: {steps}",
                file=File(image_path))
            os.remove(image_path)
            # await msg.delete()
    else:
        await interaction.followup.send("Failed to generate or find the image.")

@gen.autocomplete("model")
async def autocomplete_model(interaction: discord.Interaction, current: str): 
    matches = [
        app_commands.Choice(name=m, value=m)
        for m in MODEL_LIST 
        if current.lower() in m.lower() 
    ]
    return matches[:25]

async def generate_image_async(*args, **kwargs):
    return await asyncio.to_thread(generate, *args, **kwargs)

def wait_for_file(file_path, timeout=None, check_interval=1):
    start_time = time.time()

    while True:
        if os.path.exists(file_path):
            return True

        if (time.time() - start_time) > timeout:
            return False

        time.sleep(check_interval)

    





chat_channels = set()
chat_history = {}

# chat_enabled = False 



@tree.command(name="startchat", description="Enables chat. Woodstock will reply to every message in the channel.")
async def startchat(interaction: discord.Interaction):
    # global chat_enabled
    chat_channels.add(interaction.channel.id)
    await interaction.response.send_message("Chat enabled for this channel")

@tree.command(name="stopchat", description="Disable chat mode (Does nothing if chat mode is not enabled)")
async def stopchat(interaction: discord.Interaction): 
    # global chat_enabled 
    # chat_enabled = False 
    # await ctx.send("Chat mode disabled") 
    chat_channels.remove(interaction.channel.id)
    await interaction.response.send_message("Chat disabled for this channel")


@bot.event
async def on_message(message): 
    await bot.process_commands(message) 

    if message.author == bot.user: 
        return 
    if message.channel.id in chat_channels:
        add_message(message.guild.id, message.author, message.content)
        channel_id = message.channel.id 


        if channel_id not in chat_history: 
            chat_history[channel_id] = [PERSONALITY]
        
        username = message.author.nick or message.author.name 
        chat_history[channel_id].append({
            "role": "user",
            "content": f"{username} just said: {message.content}"
        })
        chat_history[channel_id] = [chat_history[channel_id][0]] + chat_history[channel_id][-20:]

        reply = await query_ollama("llama3", chat_history[channel_id])
        if reply: 
            chat_history[channel_id].append({"role": "assistant", "content": reply})
            await message.channel.send(reply) 



















@tree.command(name="remindme", description="Reminds u in however minutes, hours, days, months, years whatever u want")
async def remindme(interaction: discord.Interaction, time: str, *, message: str):
    dt = parse_datetime(time)
    if not dt:
        await interaction.response.send_message("Couldn't understand the time you gave me.", ephemeral=True)
        return
    
    
    if dt.tzinfo is None:
        reminder_utc = dt.replace(tzinfo=timezone.utc)
    else:
        reminder_utc = dt.astimezone(timezone.utc)
    
    reminder_ts = reminder_utc.timestamp()
    now_ts = get_now_timestamp() 
    
 
    
    if reminder_ts <= now_ts:
        await interaction.response.send_message("You can't set a reminder in the past!", ephemeral=True)
        return
        
    ensure_user_entry(interaction.guild.id, interaction.user)
    reminder = {
        "id": str(uuid.uuid4()),
        "user_id": str(interaction.user.id),
        "user_mention": interaction.user.mention,
        "channel_id": interaction.channel.id,
        "text": message,
        "time": reminder_ts
    }
    
    add_message(interaction.guild.id, interaction.user, f"The user asked for a reminder to themself: {time} {message}")
    save_reminder_to_user(interaction.guild.id, interaction.user.id, reminder)
    
    discord_time = f"<t:{int(reminder_ts)}:F>"  # full date/time format
    
    await interaction.response.defer()    
    try:
        llama_input = [
        PERSONALITY,
        {
            "role": "user",
            "content": (
                f"A user wants you to remind them about: \"{message}\" "
                f"in {time}.\n"
                f"Confirm that you'll remind them in {time}. "
                f"Be sarcastic or snarky about the reminder content itself - "
                f"Keep it casual and funny but make sure they know you got the right message and timing. "
                f"Don't add specific clock times unless they were explicitly provided."
            )
        },
        ]
        reply = await query_ollama("llama3", llama_input)
        await interaction.followup.send(f"{interaction.user.mention} {reply}")
    except Exception as e:
        print(f"Error getting AI response: {e}")
        await interaction.followup.send(f"{interaction.user.mention} reminder set")


@tree.command(name="reminders", description="Lists all your active reminders")
async def reminders(interaction: discord.Interaction):
    user_data = get_user_data(interaction.guild.id, interaction.user.id)
    
    if not user_data or not user_data.get("reminders"):
        await interaction.response.send_message("You don't have any reminders set!", ephemeral=True)
        return
    
    reminders_list = user_data["reminders"]
    
    now_ts = get_now_timestamp()
    active_reminders = [r for r in reminders_list if r.get("time", 0) > now_ts]
    
    if not active_reminders:
        await interaction.response.send_message("You don't have any active reminders!", ephemeral=True)
        return
    
    active_reminders.sort(key=lambda x: x.get("time", 0))
    
    response = f"**{interaction.user.mention} Your Reminders ({len(active_reminders)}):**\n\n"
    
    for i, reminder in enumerate(active_reminders, 1):
        reminder_ts = reminder.get("time", 0)
        discord_time = f"<t:{int(reminder_ts)}:F>"  
        relative_time = f"<t:{int(reminder_ts)}:R>"  
        text = reminder.get("text", "No message")
        reminder_id = reminder.get("id", "Unknown")[:8]  
        
        response += f"**{i}.** {text}\n"
        response += f" {discord_time} ({relative_time})\n"
        
        if len(response) > 1800:
            response += f"... and {len(active_reminders) - i} more reminders"
            break
    
    await interaction.response.send_message(response)

bot.run(token)