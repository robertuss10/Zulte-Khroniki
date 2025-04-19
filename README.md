# Zulte Kroniki - Discord Quote Bot & Web Dashboard

A Polish Discord bot that manages and displays quotes from 7 personalities with an aesthetic yellow-themed interface, voting system, and web dashboard.

## Features

- **Discord Bot**: Access quotes via Discord commands
- **Web Dashboard**: Manage quotes, view statistics, and browse the database
- **Multiple personalities**: Contains quotes from 7 personalities
- **Voting system**: Users can upvote/downvote quotes
- **Stats tracking**: Track popularity of quotes overall and by personality
- **Anti-spam protection**: Cooldowns on commands to prevent abuse

## Discord Commands

- `/random` - Get a random quote from any personality
- `/wgg [number]` - Get a quote from Weterani Gier Gacha (optional specific number)
- `/wriu [number]` - Get a quote from Wriu (optional specific number)
- `/zultan [number]` - Get a quote from Zultan (optional specific number)
- `/arizonka [number]` - Get a quote from Arizonka (optional specific number)
- `/arrow [number]` - Get a quote from Arrow (optional specific number)
- `/aruel [number]` - Get a quote from Aruel (optional specific number)
- `/murzyn [number]` - Get a quote from Murzyn (optional specific number)
- `/stats` - Show quote statistics
- `/top [limit]` - Show top quotes (default limit: 5)
- `/szukaj <query> [personality]` - Search quotes by content (optional filter by personality)
- `/reload` - Reload quote database (admin only)

## Running the Application

### Web Dashboard Only

```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

### Discord Bot Only

```bash
python start_bot.py
```

### Both Together

```bash
python run.py
```

## Environment Variables

The application requires the following environment variables:

- `DISCORD_TOKEN` - Discord bot token
- `DATABASE_URL` - PostgreSQL database connection string
- `SESSION_SECRET` - Secret key for Flask sessions

## Database Structure

- **Personalities**: Information about each quote source
- **Quotes**: The actual quotes with voting stats
- **Commands**: Record of command usage
- **Votes**: Record of user votes
- **Stats**: General statistics for personalities

## Quote Files

Quote files are stored in the `attached_assets` directory with one quote per line.

## Project Structure

- `app.py` - Web dashboard application
- `bot.py` - Discord bot application
- `config.py` - Configuration settings
- `models.py` - Database models
- `quotes_manager.py` - Manages quote loading, retrieval, and voting
- `main.py` - Entry point for Gunicorn
- `run.py` - Runs both web dashboard and Discord bot
- `start_bot.py` - Runs only the Discord bot
- `templates/` - HTML templates for web dashboard
- `static/` - CSS, JS, and other static files
- `attached_assets/` - Quote text files

## Author

This application was created for managing quotes from 7 personalities in a Discord community.