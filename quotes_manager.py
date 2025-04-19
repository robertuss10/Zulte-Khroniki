import os
import random
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models import Base, Personality, Quote, Command, Vote, Stats
from config import PERSONALITIES, DATABASE_URL, QUOTES_DIRECTORY, COOLDOWN_TIME, SPECIFIC_QUOTE_COOLDOWN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuotesManager:
    def __init__(self):
        """Initialize the quotes manager with database connection"""
        db_url = os.environ.get('DATABASE_URL', DATABASE_URL)
        self.engine = create_engine(db_url, connect_args={"sslmode": "require"})
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.personalities = PERSONALITIES
        self.setup_database()
        self.user_cooldowns = {}  # {user_id: {command: last_used_timestamp}}
        self.user_specific_cooldowns = {}  # {user_id: {personality_number: last_used_timestamp}}
        
    def setup_database(self):
        """Initialize database with personalities and load quotes from files"""
        session = self.Session()
        
        # Create personalities if they don't exist
        for file_name, name in self.personalities.items():
            if not session.query(Personality).filter_by(file_name=file_name).first():
                personality = Personality(name=name, file_name=file_name)
                session.add(personality)
                session.commit()
                
                # Create stats entry for this personality
                stats = Stats(personality_id=personality.id)
                session.add(stats)
                session.commit()
                
                # Load quotes for this personality
                self.load_quotes_from_file(personality.id, file_name)
        
        session.close()
    
    def load_quotes_from_file(self, personality_id, file_name):
        """Load quotes from a file into the database"""
        session = self.Session()
        file_path = os.path.join(QUOTES_DIRECTORY, f"{file_name}.txt")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for i, line in enumerate(file, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):  # Skip empty lines and comments
                        # Each line is a quote, use line number as quote number
                        quote = Quote(
                            personality_id=personality_id,
                            number=i,
                            content=line
                        )
                        session.add(quote)
            
            session.commit()
            
            # Update quotes count in personality
            personality = session.query(Personality).get(personality_id)
            if personality:
                personality.quotes_count = session.query(Quote).filter_by(personality_id=personality_id).count()
                session.commit()
                logger.info(f"Loaded {personality.quotes_count} quotes for {personality.name}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error loading quotes from {file_path}: {e}")
        finally:
            session.close()
    
    def reload_quotes(self):
        """Reload all quotes from files"""
        session = self.Session()
        
        try:
            # Clear existing quotes
            session.query(Quote).delete()
            session.commit()
            
            # Reset quotes count for all personalities
            for personality in session.query(Personality).all():
                personality.quotes_count = 0
                session.commit()
                
                # Reload quotes for this personality
                self.load_quotes_from_file(personality.id, personality.file_name)
            
            logger.info("All quotes reloaded successfully")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error reloading quotes: {e}")
            return False
        finally:
            session.close()
    
    def get_random_quote(self, personality_file_name=None):
        """Get a random quote, optionally from a specific personality"""
        session = self.Session()
        
        try:
            if personality_file_name:
                personality = session.query(Personality).filter_by(file_name=personality_file_name).first()
                if not personality:
                    return None
                
                quotes = session.query(Quote).filter_by(personality_id=personality.id).all()
                if not quotes:
                    return None
                
                quote = random.choice(quotes)
            else:
                quotes = session.query(Quote).all()
                if not quotes:
                    return None
                
                quote = random.choice(quotes)
            
            # Update usage statistics
            quote.last_used = datetime.utcnow()
            quote.use_count += 1
            
            # Update personality stats
            stats = session.query(Stats).filter_by(personality_id=quote.personality_id).first()
            if stats:
                stats.total_quotes_used += 1
                
            session.commit()
            return quote
        except Exception as e:
            session.rollback()
            logger.error(f"Error getting random quote: {e}")
            return None
        finally:
            session.close()
    
    def get_specific_quote(self, personality_file_name, number):
        """Get a specific quote by personality and number"""
        session = self.Session()
        
        try:
            personality = session.query(Personality).filter_by(file_name=personality_file_name).first()
            if not personality:
                return None
            
            quote = session.query(Quote).filter_by(
                personality_id=personality.id, 
                number=number
            ).first()
            
            if quote:
                # Update usage statistics
                quote.last_used = datetime.utcnow()
                quote.use_count += 1
                
                # Update personality stats
                stats = session.query(Stats).filter_by(personality_id=quote.personality_id).first()
                if stats:
                    stats.total_quotes_used += 1
                    
                session.commit()
            
            return quote
        except Exception as e:
            session.rollback()
            logger.error(f"Error getting specific quote: {e}")
            return None
        finally:
            session.close()
    
    def record_command(self, user_id, command, quote_id=None):
        """Record command usage"""
        session = self.Session()
        
        try:
            command_record = Command(
                user_id=user_id,
                command=command,
                quote_id=quote_id
            )
            session.add(command_record)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording command: {e}")
        finally:
            session.close()
    
    def record_vote(self, user_id, quote_id, vote_value):
        """Record a vote (1 for upvote, -1 for downvote)"""
        session = self.Session()
        
        try:
            # Check if user already voted for this quote
            existing_vote = session.query(Vote).filter_by(
                user_id=user_id,
                quote_id=quote_id
            ).first()
            
            if existing_vote:
                # Update existing vote
                if existing_vote.vote != vote_value:
                    old_vote = existing_vote.vote
                    existing_vote.vote = vote_value
                    existing_vote.timestamp = datetime.utcnow()
                    
                    # Update quote and stats
                    quote = session.query(Quote).get(quote_id)
                    if quote:
                        # Remove the old vote
                        if old_vote == 1:
                            quote.upvotes -= 1
                            session.query(Stats).filter_by(personality_id=quote.personality_id).update(
                                {"total_upvotes": Stats.total_upvotes - 1})
                        else:
                            quote.downvotes -= 1
                            session.query(Stats).filter_by(personality_id=quote.personality_id).update(
                                {"total_downvotes": Stats.total_downvotes - 1})
                        
                        # Add the new vote
                        if vote_value == 1:
                            quote.upvotes += 1
                            session.query(Stats).filter_by(personality_id=quote.personality_id).update(
                                {"total_upvotes": Stats.total_upvotes + 1})
                        else:
                            quote.downvotes += 1
                            session.query(Stats).filter_by(personality_id=quote.personality_id).update(
                                {"total_downvotes": Stats.total_downvotes + 1})
            else:
                # Create new vote
                new_vote = Vote(
                    user_id=user_id,
                    quote_id=quote_id,
                    vote=vote_value
                )
                session.add(new_vote)
                
                # Update quote and stats
                quote = session.query(Quote).get(quote_id)
                if quote:
                    if vote_value == 1:
                        quote.upvotes += 1
                        session.query(Stats).filter_by(personality_id=quote.personality_id).update(
                            {"total_upvotes": Stats.total_upvotes + 1})
                    else:
                        quote.downvotes += 1
                        session.query(Stats).filter_by(personality_id=quote.personality_id).update(
                            {"total_downvotes": Stats.total_downvotes + 1})
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording vote: {e}")
            return False
        finally:
            session.close()
    
    def get_top_quotes(self, limit=10):
        """Get top quotes by score (upvotes - downvotes)"""
        session = self.Session()
        
        try:
            top_quotes = session.query(Quote).\
                order_by((Quote.upvotes - Quote.downvotes).desc()).\
                limit(limit).all()
            return top_quotes
        except Exception as e:
            logger.error(f"Error getting top quotes: {e}")
            return []
        finally:
            session.close()
    
    def search_quotes(self, query, personality_file_name=None):
        """Search quotes by content, optionally from a specific personality"""
        session = self.Session()
        
        try:
            search_query = f"%{query}%"
            if personality_file_name:
                personality = session.query(Personality).filter_by(file_name=personality_file_name).first()
                if not personality:
                    return []
                
                results = session.query(Quote).filter(
                    Quote.personality_id == personality.id,
                    Quote.content.like(search_query)
                ).all()
            else:
                results = session.query(Quote).filter(
                    Quote.content.like(search_query)
                ).all()
            
            return results
        except Exception as e:
            logger.error(f"Error searching quotes: {e}")
            return []
        finally:
            session.close()
    
    def get_statistics(self):
        """Get general statistics"""
        session = self.Session()
        
        try:
            stats = {
                'total_quotes': session.query(func.count(Quote.id)).scalar(),
                'total_commands': session.query(func.count(Command.id)).scalar(),
                'total_votes': session.query(func.count(Vote.id)).scalar(),
                'personality_stats': []
            }
            
            for personality in session.query(Personality).all():
                p_stats = session.query(Stats).filter_by(personality_id=personality.id).first()
                personality_data = {
                    'name': personality.name,
                    'quotes_count': personality.quotes_count,
                    'total_quotes_used': p_stats.total_quotes_used if p_stats else 0,
                    'total_upvotes': p_stats.total_upvotes if p_stats else 0,
                    'total_downvotes': p_stats.total_downvotes if p_stats else 0
                }
                stats['personality_stats'].append(personality_data)
            
            return stats
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
        finally:
            session.close()
    
    def check_cooldown(self, user_id, command):
        """Check if user is in cooldown for a command"""
        if user_id not in self.user_cooldowns:
            self.user_cooldowns[user_id] = {}
        
        current_time = datetime.now()
        if command in self.user_cooldowns[user_id]:
            last_used = self.user_cooldowns[user_id][command]
            if (current_time - last_used).total_seconds() < COOLDOWN_TIME:
                return False
        
        self.user_cooldowns[user_id][command] = current_time
        return True
    
    def check_specific_quote_cooldown(self, user_id, personality_number):
        """Check if user is in cooldown for a specific quote"""
        cooldown_key = f"{personality_number}"
        if user_id not in self.user_specific_cooldowns:
            self.user_specific_cooldowns[user_id] = {}
        
        current_time = datetime.now()
        if cooldown_key in self.user_specific_cooldowns[user_id]:
            last_used = self.user_specific_cooldowns[user_id][cooldown_key]
            if (current_time - last_used).total_seconds() < SPECIFIC_QUOTE_COOLDOWN:
                time_left = SPECIFIC_QUOTE_COOLDOWN - (current_time - last_used).total_seconds()
                return False, int(time_left // 60) + 1  # Return minutes left
        
        self.user_specific_cooldowns[user_id][cooldown_key] = current_time
        return True, 0
