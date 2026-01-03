# Matibbot 🤖🔊

A Discord bot that joins your voice channel and plays random audio clips at random intervals (every 2-3 minutes). It also allows users to manage the sound library directly from Discord.

## Features

*   **Random Playback**: Plays a random sound from the `sounds/` folder every 2-3 minutes when connected to a voice channel.
*   **Sound Management**: Users can upload (`!add`) and delete (`!remove`) sounds via Discord commands.
*   **Control**: Enable/Disable specific sounds from the random rotation without deleting them.
*   **Manual Play**: Play any sound on demand with `!play`.

## Setup

1.  **Prerequisites**:
    *   [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Recommended)
    *   OR Python 3.10+ and [FFmpeg](https://ffmpeg.org/) installed on your system.

2.  **Configuration**:
    *   Create a `.env` file in the root directory (or use the provided template).
    *   Add your Discord Bot Token:
        ```env
        DISCORD_TOKEN=your_actual_token_here
        ```

## How to Run

### Option 1: Docker (Recommended 🐳)

This is the easiest way to run the bot, as it handles all dependencies (including FFmpeg) for you.

1.  Make sure Docker Desktop is running.
2.  **Windows**: Double-click `start_bot.bat`.
3.  **Linux/Mac/Terminal**: Run the following command:
    ```bash
    docker-compose up -d --build
    ```

The bot will start in the background.
*   To stop it: `docker-compose down`
*   To view logs: `docker-compose logs -f`

### Option 2: Manual Python Setup 🐍

1.  Install FFmpeg and add it to your system PATH.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the bot:
    ```bash
    python main.py
    ```

## Commands

| Command | Alias | Description |
| :--- | :--- | :--- |
| `!summon` | `!join` | Summons the bot to your current voice channel. |
| `!leave` | `!disconnect` | Disconnects the bot from the voice channel. |
| `!play <name>` | | Plays a specific sound immediately (e.g., `!play wow`). |
| `!list` | | Lists all available sounds and their status (✅ Enabled / ❌ Disabled). |
| `!add` | | Attach an audio file (mp3, wav, ogg) to the message and use this command to upload it. |
| `!remove <name>` | `!delete` | Permanently deletes a sound file from the bot. |
| `!enable <name>` | | Enables a sound to be played in the random loop. |
| `!disable <name>` | | Disables a sound from the random loop (can still be played manually). |

## Adding Sounds

You can add sounds in two ways:
1.  **Via Discord**: Send a message with an audio attachment and the text `!add`.
2.  **Manually**: Drop `.mp3`, `.wav`, or `.ogg` files into the `sounds/` folder on your computer. (If using Docker, the folder is synced automatically).
