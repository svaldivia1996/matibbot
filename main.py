import discord
from discord.ext import commands, tasks
import os
import asyncio
import random
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configuration
SOUNDS_DIR = 'sounds'
CONFIG_FILE = 'sound_config.json'
MIN_INTERVAL = 120
MAX_INTERVAL = 300

# Ensure sounds directory exists
if not os.path.exists(SOUNDS_DIR):
    os.makedirs(SOUNDS_DIR)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Global state
sound_config = {}
alone_time = {}

class SoundButton(discord.ui.Button):
    def __init__(self, sound_name, file_name):
        super().__init__(label=sound_name, style=discord.ButtonStyle.primary)
        self.file_name = file_name

    async def callback(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc:
            if interaction.user.voice:
                vc = await interaction.user.voice.channel.connect()
            else:
                await interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
                return
        
        if vc.is_playing():
            vc.stop()
            
        file_path = os.path.join(SOUNDS_DIR, self.file_name)
        try:
            vc.play(discord.FFmpegPCMAudio(file_path))
            await interaction.response.defer()
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

def load_config():
    global sound_config
    # Load existing config
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            sound_config = json.load(f)
    
    # Sync with actual files
    files = [f for f in os.listdir(SOUNDS_DIR) if f.endswith(('.mp3', '.wav', '.ogg'))]
    
    # Add new files to config (default enabled)
    for f in files:
        if f not in sound_config:
            sound_config[f] = True
            
    # Remove missing files from config
    for f in list(sound_config.keys()):
        if f not in files:
            del sound_config[f]
            
    save_config()

def save_config():
    with open(CONFIG_FILE, 'w') as f:
        json.dump(sound_config, f, indent=4)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    load_config()
    if not random_sound_loop.is_running():
        random_sound_loop.start()
    if not auto_disconnect_loop.is_running():
        auto_disconnect_loop.start()

@tasks.loop(seconds=60)
async def auto_disconnect_loop():
    for vc in bot.voice_clients:
        # Check if bot is alone in the channel (members includes the bot itself)
        if len(vc.channel.members) == 1:
            guild_id = vc.guild.id
            alone_time[guild_id] = alone_time.get(guild_id, 0) + 1
            
            if alone_time[guild_id] >= 5:
                await vc.disconnect()
                print(f"Disconnected from {vc.guild.name} due to inactivity.")
                del alone_time[guild_id]
        else:
            # Reset timer if not alone
            if vc.guild.id in alone_time:
                alone_time[vc.guild.id] = 0

@tasks.loop(seconds=1) # Dummy interval, we control it inside
async def random_sound_loop():
    # Wait for a random interval
    wait_time = random.randint(MIN_INTERVAL, MAX_INTERVAL)
    await asyncio.sleep(wait_time)
    
    # Check if bot is in any voice channels
    for vc in bot.voice_clients:
        if vc.is_connected() and not vc.is_playing():
            # Get enabled sounds
            enabled_sounds = [s for s, enabled in sound_config.items() if enabled]
            if enabled_sounds:
                sound_name = random.choice(enabled_sounds)
                file_path = os.path.join(SOUNDS_DIR, sound_name)
                try:
                    vc.play(discord.FFmpegPCMAudio(file_path))
                    print(f"Playing random sound: {sound_name} in {vc.channel.name}")
                except Exception as e:
                    print(f"Error playing sound: {e}")

@random_sound_loop.before_loop
async def before_random_sound_loop():
    await bot.wait_until_ready()

@bot.command(name='summon', aliases=['join'])
async def summon(ctx):
    """Summons the bot to your voice channel."""
    if not ctx.author.voice:
        await ctx.send("You are not connected to a voice channel.")
        return
    
    channel = ctx.author.voice.channel
    if ctx.voice_client:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()
    await ctx.send(f"Joined {channel.name}!")

    # Play a random sound immediately
    if ctx.voice_client and not ctx.voice_client.is_playing():
        enabled_sounds = [s for s, enabled in sound_config.items() if enabled]
        if enabled_sounds:
            sound_name = random.choice(enabled_sounds)
            file_path = os.path.join(SOUNDS_DIR, sound_name)
            try:
                ctx.voice_client.play(discord.FFmpegPCMAudio(file_path))
            except Exception as e:
                print(f"Error playing summon sound: {e}")

@bot.command(name='leave', aliases=['disconnect'])
async def leave(ctx):
    """Disconnects the bot from the voice channel."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected.")
    else:
        await ctx.send("I am not in a voice channel.")

@bot.command(name='play')
async def play(ctx, sound_name: str = None):
    """Plays a specific sound. Usage: !play <sound_name>"""
    if not ctx.voice_client:
        await ctx.send("I need to be in a voice channel first. Use !summon")
        return

    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()

    if not sound_name:
        await ctx.send("Please specify a sound name.")
        return

    # Try to find the sound (case insensitive search)
    found_sound = None
    for s in sound_config.keys():
        if s.lower().startswith(sound_name.lower()):
            found_sound = s
            break
    
    if found_sound:
        file_path = os.path.join(SOUNDS_DIR, found_sound)
        try:
            ctx.voice_client.play(discord.FFmpegPCMAudio(file_path))
            await ctx.send(f"Playing: {found_sound}")
        except Exception as e:
            await ctx.send(f"Error playing sound: {e}")
    else:
        await ctx.send(f"Sound '{sound_name}' not found.")

@bot.command(name='list')
async def list_sounds(ctx):
    """Lists all available sounds and their status."""
    load_config() # Refresh config
    if not sound_config:
        await ctx.send("No sounds available.")
        return

    message = "**Available Sounds:**\n"
    for sound, enabled in sorted(sound_config.items()):
        status = "✅" if enabled else "❌"
        message += f"{status} {sound}\n"
    
    # Split message if too long
    if len(message) > 2000:
        # Simple split for now, could be improved
        chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
        for chunk in chunks:
            await ctx.send(chunk)
    else:
        await ctx.send(message)

@bot.command(name='enable')
async def enable_sound(ctx, sound_name: str):
    """Enables a sound for random playback."""
    for s in sound_config.keys():
        if s.lower().startswith(sound_name.lower()):
            sound_config[s] = True
            save_config()
            await ctx.send(f"Enabled: {s}")
            return
    await ctx.send(f"Sound '{sound_name}' not found.")

@bot.command(name='disable')
async def disable_sound(ctx, sound_name: str):
    """Disables a sound for random playback."""
    for s in sound_config.keys():
        if s.lower().startswith(sound_name.lower()):
            sound_config[s] = False
            save_config()
            await ctx.send(f"Disabled: {s}")
            return
    await ctx.send(f"Sound '{sound_name}' not found.")

@bot.command(name='add')
async def add_sound(ctx):
    """Adds a sound file attached to the message."""
    if not ctx.message.attachments:
        await ctx.send("Please attach an audio file (mp3, wav, ogg).")
        return

    attachment = ctx.message.attachments[0]
    if not attachment.filename.endswith(('.mp3', '.wav', '.ogg')):
        await ctx.send("Invalid file type. Please upload mp3, wav, or ogg.")
        return

    save_path = os.path.join(SOUNDS_DIR, attachment.filename)
    await attachment.save(save_path)
    
    load_config() # Update config with new file
    await ctx.send(f"Added sound: {attachment.filename}")

@bot.command(name='remove', aliases=['delete'])
async def remove_sound(ctx, sound_name: str):
    """Removes a sound file."""
    found_sound = None
    for s in sound_config.keys():
        if s.lower().startswith(sound_name.lower()):
            found_sound = s
            break
    
    if found_sound:
        file_path = os.path.join(SOUNDS_DIR, found_sound)
        try:
            os.remove(file_path)
            load_config() # Update config
            await ctx.send(f"Removed sound: {found_sound}")
        except Exception as e:
            await ctx.send(f"Error removing file: {e}")
    else:
        await ctx.send(f"Sound '{sound_name}' not found.")

@bot.command(name='gui', aliases=['soundboard'])
async def soundboard_gui(ctx):
    """Opens an interactive soundboard."""
    load_config()
    enabled_sounds = sorted([f for f, e in sound_config.items() if e])
    
    if not enabled_sounds:
        await ctx.send("No sounds available.")
        return

    # Chunk sounds into groups of 25 (Discord limit per view)
    chunks = [enabled_sounds[i:i + 25] for i in range(0, len(enabled_sounds), 25)]
    
    await ctx.send("🎧 **Soundboard**")
    
    for chunk in chunks:
        view = discord.ui.View(timeout=None)
        for file_name in chunk:
            sound_name = os.path.splitext(file_name)[0]
            view.add_item(SoundButton(sound_name, file_name))
        await ctx.send(view=view)

@bot.command(name='help')
async def help_command(ctx):
    """Displays this help message."""
    embed = discord.Embed(title="🤖 Matibbot Help", description="Here are the available commands:", color=0x3498db)
    
    commands_list = [
        ("!gui", "Opens an interactive soundboard with buttons."),
        ("!summon / !join", "Summons the bot to your voice channel."),
        ("!leave / !disconnect", "Disconnects the bot from the voice channel."),
        ("!play <name>", "Plays a specific sound immediately."),
        ("!list", "Lists all available sounds and their status."),
        ("!enable <name>", "Enables a sound for random playback."),
        ("!disable <name>", "Disables a sound for random playback."),
        ("!add", "Upload an attached audio file (mp3, wav, ogg)."),
        ("!remove <name>", "Permanently deletes a sound file.")
    ]

    for name, desc in commands_list:
        embed.add_field(name=name, value=desc, inline=False)
    
    await ctx.send(embed=embed)

if __name__ == "__main__":
    if not TOKEN or TOKEN == 'your_token_here':
        print("Error: Please set your DISCORD_TOKEN in the .env file.")
    else:
        bot.run(TOKEN)
