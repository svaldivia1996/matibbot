import json
import discord
import time
import random
import threading
import os

fconfig = open("config.json", "r")
config = json.load(fconfig)
fconfig.close()

intens = discord.Intents.default()
intens.message_content = True

threadStarted = False
client = discord.Client(intents=intens)
play_time = 0  # Keep track of the total play time

def playSound():
    global play_time
    play_interval = random.randint(15, 60)  # Play a sound every 30 seconds
    total_play_duration = 300  # Total play duration of 5 minutes (300 seconds)

    if play_time < total_play_duration:
        sounds = [f for f in os.listdir('sounds') if f.endswith('.mp3')]
        selected = f'sounds/{random.choice(sounds)}'
        print(selected)
        random_source = discord.FFmpegPCMAudio(selected)
        vClient.play(random_source)

        play_time += play_interval
        threading.Timer(play_interval, playSound).start()
    else:
        # Reset play_time and disconnect after 5 minutes
        print('Disconnecting after 5 minutes')
        play_time = 0
        if vClient.is_connected():
            client.loop.create_task(vClient.disconnect())
            global threadStarted
            threadStarted = False


@client.event
async def on_ready():
    print(f'me conecte como {client.user}')

@client.event
async def on_message(message):
    global threadStarted, vClient
    if message.content.startswith('|') and threadStarted == False:
        threadStarted = True
        vChannel = message.author.voice.channel
        vClient = await vChannel.connect()
        vClient.stop()
        threading.Timer(1, playSound).start()


client.run(config["token"])