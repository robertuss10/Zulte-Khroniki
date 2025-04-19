import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging
import requests
from datetime import datetime, timedelta

from config import TOKEN, COMMAND_PREFIX, PERSONALITIES, COLORS, API_BASE_URL
from quotes_manager import QuotesManager
from models import Quote, Personality, Command, Vote

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# Create quotes manager
quotes_manager = QuotesManager()

@bot.event
async def on_ready():
    """Event called when the bot is ready"""
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Error syncing commands: {e}")
        
    logger.info(f'Bot {bot.user.name} is connected and ready!')
    await bot.change_presence(activity=discord.Game(name="Zulte Kroniki | /random"))

async def send_quote_embed(interaction, quote):
    """Send an embed with a quote"""
    if quote is None:
        embed = discord.Embed(
            title="Błąd",
            description="Nie znaleziono cytatu.",
            color=int(COLORS['accent'].replace('#', ''), 16)
        )
        await interaction.followup.send(embed=embed)
        return
    
    personality_name = quote.personality.name
    
    embed = discord.Embed(
        title=f"{personality_name} #{quote.number}",
        description=quote.content,
        color=int(COLORS['primary'].replace('#', ''), 16)
    )
    
    embed.set_footer(text=f"👍 {quote.upvotes} | 👎 {quote.downvotes} | Użyto {quote.use_count} razy")
    
    # Record command usage
    quotes_manager.record_command(
        user_id=str(interaction.user.id),
        command=interaction.command.name,
        quote_id=quote.id
    )
    
    message = await interaction.followup.send(embed=embed)
    
    # Add reactions for voting
    await message.add_reaction('✅')
    await message.add_reaction('❌')
    
    # Create a check for the reaction event
    def check(reaction, user):
        return (
            user.id == interaction.user.id and 
            reaction.message.id == message.id and 
            str(reaction.emoji) in ['✅', '❌']
        )
    
    # Wait for reaction
    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
        
        # Record vote
        vote_value = 1 if str(reaction.emoji) == '✅' else -1
        quotes_manager.record_vote(str(user.id), quote.id, vote_value)
        
        # Update embed with new vote count
        session = quotes_manager.Session()
        updated_quote = session.query(Quote).get(quote.id)
        
        if updated_quote:
            embed.set_footer(text=f"👍 {updated_quote.upvotes} | 👎 {updated_quote.downvotes} | Użyto {updated_quote.use_count} razy")
            await message.edit(embed=embed)
        
        session.close()
        
    except asyncio.TimeoutError:
        # Reaction timeout, no action needed
        pass
    except Exception as e:
        logger.error(f"Error processing reaction: {e}")

@bot.tree.command(name="random", description="Losowy cytat z dowolnej osobowości")
async def random_quote(interaction: discord.Interaction):
    """Get a random quote from any personality"""
    await interaction.response.defer()
    
    # Check cooldown
    if not quotes_manager.check_cooldown(str(interaction.user.id), "random"):
        await interaction.followup.send("Spokojnie! Odczekaj chwilę przed użyciem komendy ponownie.", ephemeral=True)
        return
    
    quote = quotes_manager.get_random_quote()
    await send_quote_embed(interaction, quote)

# Create command for each personality individually
# This is a factory function approach to avoid the closure issue with the loop
def create_personality_command(personality_file_name, personality_name):
    @bot.tree.command(name=personality_file_name, description=f"Losowy cytat od {personality_name}")
    async def personality_quote_command(interaction: discord.Interaction, number: int = None):
        """Get a quote from a specific personality, optionally by number"""
        await interaction.response.defer()
        
        if number is not None:
            # Check specific quote cooldown
            can_use, minutes_left = quotes_manager.check_specific_quote_cooldown(
                str(interaction.user.id),
                f"{personality_file_name}_{number}"
            )
            
            if not can_use:
                await interaction.followup.send(
                    f"Możesz poprosić o konkretny cytat dopiero za {minutes_left} minut.", 
                    ephemeral=True
                )
                return
            
            quote = quotes_manager.get_specific_quote(personality_file_name, number)
            if quote is None:
                await interaction.followup.send(
                    f"Nie znaleziono cytatu #{number} dla {personality_name}.", 
                    ephemeral=True
                )
                return
        else:
            # Check normal cooldown
            if not quotes_manager.check_cooldown(str(interaction.user.id), personality_file_name):
                await interaction.followup.send(
                    "Spokojnie! Odczekaj chwilę przed użyciem komendy ponownie.", 
                    ephemeral=True
                )
                return
            
            quote = quotes_manager.get_random_quote(personality_file_name)
        
        await send_quote_embed(interaction, quote)
    
    # We need to return the command function to keep a reference
    return personality_quote_command

# Create commands for each personality
personality_commands = {}
for file_name, name in PERSONALITIES.items():
    personality_commands[file_name] = create_personality_command(file_name, name)

@bot.tree.command(name="stats", description="Statystyki cytatów")
async def stats(interaction: discord.Interaction):
    """Show quote statistics"""
    await interaction.response.defer()
    
    stats = quotes_manager.get_statistics()
    
    embed = discord.Embed(
        title="Statystyki Zulte Kroniki",
        color=int(COLORS['primary'].replace('#', ''), 16)
    )
    
    embed.add_field(name="Łączna liczba cytatów", value=stats.get('total_quotes', 0), inline=False)
    embed.add_field(name="Użycia komend", value=stats.get('total_commands', 0), inline=True)
    embed.add_field(name="Oddane głosy", value=stats.get('total_votes', 0), inline=True)
    
    # Add personality stats
    for p_stats in stats.get('personality_stats', []):
        embed.add_field(
            name=p_stats['name'],
            value=f"Cytaty: {p_stats['quotes_count']}\n"
                  f"Użyto: {p_stats['total_quotes_used']}\n"
                  f"👍 {p_stats['total_upvotes']} | 👎 {p_stats['total_downvotes']}",
            inline=True
        )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="top", description="Najlepsze cytaty")
async def top_quotes(interaction: discord.Interaction, limit: int = 5):
    """Show top quotes"""
    await interaction.response.defer()
    
    if limit > 10:
        limit = 10  # Cap at 10 to avoid too long messages
    
    top_quotes = quotes_manager.get_top_quotes(limit)
    
    if not top_quotes:
        await interaction.followup.send("Nie ma jeszcze żadnych głosów na cytaty.")
        return
    
    embed = discord.Embed(
        title="Najlepsze Cytaty",
        color=int(COLORS['primary'].replace('#', ''), 16)
    )
    
    for i, quote in enumerate(top_quotes, 1):
        embed.add_field(
            name=f"{i}. {quote.personality.name} #{quote.number} (Score: {quote.score})",
            value=f"{quote.content[:100]}..." if len(quote.content) > 100 else quote.content,
            inline=False
        )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="szukaj", description="Szukaj cytatów po treści")
async def search(interaction: discord.Interaction, query: str, personality: str = None):
    """Search quotes by content"""
    await interaction.response.defer()
    
    personality_file_name = None
    if personality and personality in PERSONALITIES:
        personality_file_name = personality
    
    results = quotes_manager.search_quotes(query, personality_file_name)
    
    if not results:
        await interaction.followup.send(f"Nie znaleziono cytatów zawierających '{query}'.")
        return
    
    if len(results) > 10:
        embed = discord.Embed(
            title=f"Znaleziono {len(results)} cytatów dla '{query}'",
            description="Wyświetlanie pierwszych 10 wyników:",
            color=int(COLORS['accent'].replace('#', ''), 16)
        )
        results = results[:10]
    else:
        embed = discord.Embed(
            title=f"Znaleziono {len(results)} cytatów dla '{query}'",
            color=int(COLORS['accent'].replace('#', ''), 16)
        )
    
    for quote in results:
        embed.add_field(
            name=f"{quote.personality.name} #{quote.number}",
            value=f"{quote.content[:100]}..." if len(quote.content) > 100 else quote.content,
            inline=False
        )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="reload", description="Przeładuj bazę cytatów (tylko dla administratorów)")
@app_commands.checks.has_permissions(administrator=True)
async def reload(interaction: discord.Interaction):
    """Reload quote database (admin only)"""
    await interaction.response.defer(ephemeral=True)
    
    success = quotes_manager.reload_quotes()
    
    if success:
        await interaction.followup.send("Baza cytatów została pomyślnie przeładowana!", ephemeral=True)
    else:
        await interaction.followup.send("Wystąpił błąd podczas przeładowywania bazy cytatów.", ephemeral=True)

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"Spokojnie! Odczekaj {error.retry_after:.1f}s przed użyciem komendy ponownie.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignore command not found errors
    else:
        logger.error(f"Command error: {error}")

@bot.event
async def on_reaction_add(reaction, user):
    """Handle reactions to quote messages"""
    if user.bot:
        return  # Ignore bot reactions
    
    message = reaction.message
    
    # Check if message is from bot and has an embed
    if message.author != bot.user or not message.embeds:
        return
    
    # Check if reaction is valid for voting
    if str(reaction.emoji) not in ['✅', '❌']:
        return
    
    embed = message.embeds[0]
    
    # Extract quote information from embed title
    title_parts = embed.title.split(' #')
    if len(title_parts) != 2:
        return
    
    personality_name, number_str = title_parts
    try:
        number = int(number_str)
    except ValueError:
        return
    
    # Find personality by name
    personality_file_name = None
    for file_name, name in PERSONALITIES.items():
        if name == personality_name:
            personality_file_name = file_name
            break
    
    if not personality_file_name:
        return
    
    # Get quote
    session = quotes_manager.Session()
    personality = session.query(Personality).filter_by(name=personality_name).first()
    if not personality:
        session.close()
        return
    
    quote = session.query(Quote).filter_by(
        personality_id=personality.id,
        number=number
    ).first()
    session.close()
    
    if not quote:
        return
    
    # Record vote
    vote_value = 1 if str(reaction.emoji) == '✅' else -1
    quotes_manager.record_vote(str(user.id), quote.id, vote_value)
    
    # Update embed with new vote count
    session = quotes_manager.Session()
    updated_quote = session.query(Quote).get(quote.id)
    
    if updated_quote:
        embed.set_footer(text=f"👍 {updated_quote.upvotes} | 👎 {updated_quote.downvotes} | Użyto {updated_quote.use_count} razy")
        await message.edit(embed=embed)
    
    session.close()

def run_bot():
    """Run the Discord bot"""
    bot.run(TOKEN)

if __name__ == "__main__":
    run_bot()
