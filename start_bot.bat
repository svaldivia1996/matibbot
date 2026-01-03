@echo off
echo Checking for sound_config.json...
if not exist sound_config.json (
    echo {} > sound_config.json
    echo Created empty sound_config.json
)

echo Starting Matibbot with Docker Compose...
docker-compose up -d --build

echo.
echo Bot is running in the background!
echo To view logs, run: docker-compose logs -f
echo To stop, run: docker-compose down
pause
