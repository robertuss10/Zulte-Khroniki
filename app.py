import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker
from werkzeug.middleware.proxy_fix import ProxyFix
from models import Base, Personality, Quote, Command, Vote, Stats
from config import DATABASE_URL, SECRET_KEY, HOST, PORT, PERSONALITIES
from quotes_manager import QuotesManager

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", SECRET_KEY)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Initialize quotes manager and load personalities and quotes
quotes_manager = QuotesManager()
with app.app_context():
    # Make sure the database is properly set up with personalities and quotes
    quotes_manager.setup_database()

@app.route('/')
def index():
    """Dashboard homepage"""
    session = Session()
    
    try:
        stats = {
            'total_quotes': session.query(func.count(Quote.id)).scalar(),
            'total_commands': session.query(func.count(Command.id)).scalar(),
            'total_votes': session.query(func.count(Vote.id)).scalar(),
            'personalities': session.query(Personality).all()
        }
        
        # Get top 5 quotes
        top_quotes = session.query(Quote).\
            order_by((Quote.upvotes - Quote.downvotes).desc()).\
            limit(5).all()
        
        # Get recently used quotes
        recent_quotes = session.query(Quote).\
            filter(Quote.last_used != None).\
            order_by(Quote.last_used.desc()).\
            limit(5).all()
        
        # Get most used commands
        commands_stats = session.query(
            Command.command,
            func.count(Command.id).label('count')
        ).group_by(Command.command).order_by(desc('count')).limit(5).all()
        
        return render_template('dashboard.html', 
                               stats=stats, 
                               top_quotes=top_quotes, 
                               recent_quotes=recent_quotes,
                               commands_stats=commands_stats)
    except Exception as e:
        app.logger.error(f"Error loading dashboard: {e}")
        return render_template('dashboard.html', error=str(e))
    finally:
        session.close()

@app.route('/quotes')
def quotes():
    """Quotes management page"""
    session = Session()
    
    try:
        personality_name = request.args.get('personality')
        search_query = request.args.get('search')
        page = int(request.args.get('page', 1))
        per_page = 20
        
        # Base query
        query = session.query(Quote)
        
        # Apply filters
        if personality_name:
            personality = session.query(Personality).filter_by(file_name=personality_name).first()
            if personality:
                query = query.filter(Quote.personality_id == personality.id)
        
        if search_query:
            query = query.filter(Quote.content.like(f"%{search_query}%"))
        
        # Get total count for pagination
        total_count = query.count()
        total_pages = (total_count + per_page - 1) // per_page
        
        # Apply pagination
        quotes = query.order_by(Quote.personality_id, Quote.number).\
            offset((page - 1) * per_page).limit(per_page).all()
        
        # Get all personalities for filter dropdown
        personalities = session.query(Personality).all()
        
        return render_template('quotes.html', 
                               quotes=quotes, 
                               personalities=personalities,
                               current_personality=personality_name,
                               current_search=search_query,
                               current_page=page,
                               total_pages=total_pages)
    except Exception as e:
        app.logger.error(f"Error loading quotes page: {e}")
        return render_template('quotes.html', error=str(e))
    finally:
        session.close()

@app.route('/stats')
def stats():
    """Statistics page"""
    session = Session()
    
    try:
        # General stats with safe defaults
        try:
            total_quotes = session.query(func.count(Quote.id)).scalar() or 0
            total_commands = session.query(func.count(Command.id)).scalar() or 0
            total_votes = session.query(func.count(Vote.id)).scalar() or 0
        except Exception as e:
            app.logger.error(f"Error getting general stats: {e}")
            total_quotes = total_commands = total_votes = 0
            
        general_stats = {
            'total_quotes': total_quotes,
            'total_commands': total_commands,
            'total_votes': total_votes,
        }
        
        # Personality stats
        personality_stats = []
        try:
            personalities = session.query(Personality).all()
            for personality in personalities:
                try:
                    quote_count = session.query(func.count(Quote.id)).\
                        filter(Quote.personality_id == personality.id).scalar() or 0
                    
                    used_count = session.query(func.sum(Quote.use_count)).\
                        filter(Quote.personality_id == personality.id).scalar() or 0
                    
                    most_popular = session.query(Quote).\
                        filter(Quote.personality_id == personality.id).\
                        order_by((Quote.upvotes - Quote.downvotes).desc()).\
                        first()
                    
                    personality_stats.append({
                        'personality': personality,
                        'quote_count': quote_count,
                        'used_count': used_count,
                        'most_popular': most_popular
                    })
                except Exception as e:
                    app.logger.error(f"Error processing personality {personality.name}: {e}")
                    personality_stats.append({
                        'personality': personality,
                        'quote_count': 0,
                        'used_count': 0,
                        'most_popular': None
                    })
        except Exception as e:
            app.logger.error(f"Error getting personalities: {e}")
            
        # Command usage over time (last 7 days) with safe defaults
        command_usage = []
        try:
            for i in range(7):
                try:
                    date = (func.current_date() - i)
                    date_str = f"{date.compile().params[date.key]}" if hasattr(date, 'compile') else f"Day-{i}"
                    
                    count = session.query(func.count(Command.id)).\
                        filter(func.date(Command.timestamp) == date).scalar() or 0
                        
                    command_usage.append({'date': date_str, 'count': count})
                except Exception as e:
                    app.logger.error(f"Error getting command usage for day -{i}: {e}")
                    command_usage.append({'date': f"Day-{i}", 'count': 0})
            
            command_usage.reverse()
        except Exception as e:
            app.logger.error(f"Error processing command usage: {e}")
            # Provide default data for the chart
            command_usage = [{'date': f"Day-{i}", 'count': 0} for i in range(7)]
        
        return render_template('stats.html',
                               general_stats=general_stats,
                               personality_stats=personality_stats,
                               command_usage=command_usage)
    except Exception as e:
        app.logger.error(f"Error loading stats page: {e}")
        return render_template('stats.html', error=str(e))
    finally:
        session.close()

# API Endpoints
@app.route('/api/quotes/random', methods=['GET'])
def api_random_quote():
    """API endpoint for random quote"""
    session = Session()
    
    try:
        personality_name = request.args.get('personality')
        
        if personality_name and personality_name in PERSONALITIES:
            # Get random quote from specific personality
            personality = session.query(Personality).filter_by(file_name=personality_name).first()
            if not personality:
                return jsonify({'error': 'Personality not found'}), 404
            
            quote = session.query(Quote).filter_by(personality_id=personality.id).\
                order_by(func.random()).first()
        else:
            # Get random quote from any personality
            quote = session.query(Quote).order_by(func.random()).first()
        
        if not quote:
            return jsonify({'error': 'No quotes found'}), 404
        
        return jsonify({
            'id': quote.id,
            'personality': quote.personality.name,
            'number': quote.number,
            'content': quote.content,
            'upvotes': quote.upvotes,
            'downvotes': quote.downvotes,
            'score': quote.upvotes - quote.downvotes
        })
    except Exception as e:
        app.logger.error(f"API error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/quotes/<int:quote_id>/vote', methods=['POST'])
def api_vote_quote(quote_id):
    """API endpoint for voting on a quote"""
    session = Session()
    
    try:
        data = request.get_json()
        if not data or 'vote' not in data or 'user_id' not in data:
            return jsonify({'error': 'Missing vote or user_id in request'}), 400
        
        vote_value = data['vote']
        user_id = data['user_id']
        
        if vote_value not in [1, -1]:
            return jsonify({'error': 'Vote must be 1 (upvote) or -1 (downvote)'}), 400
        
        # Get quote
        quote = session.query(Quote).get(quote_id)
        if not quote:
            return jsonify({'error': 'Quote not found'}), 404
        
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
                
                # Remove the old vote
                if old_vote == 1:
                    quote.upvotes -= 1
                else:
                    quote.downvotes -= 1
                
                # Add the new vote
                if vote_value == 1:
                    quote.upvotes += 1
                else:
                    quote.downvotes += 1
        else:
            # Create new vote
            new_vote = Vote(
                user_id=user_id,
                quote_id=quote_id,
                vote=vote_value
            )
            session.add(new_vote)
            
            # Update quote
            if vote_value == 1:
                quote.upvotes += 1
            else:
                quote.downvotes += 1
        
        session.commit()
        
        return jsonify({
            'success': True,
            'quote_id': quote_id,
            'upvotes': quote.upvotes,
            'downvotes': quote.downvotes,
            'score': quote.upvotes - quote.downvotes
        })
    except Exception as e:
        session.rollback()
        app.logger.error(f"API error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """API endpoint for statistics"""
    session = Session()
    
    try:
        stats = {
            'total_quotes': session.query(func.count(Quote.id)).scalar(),
            'total_commands': session.query(func.count(Command.id)).scalar(),
            'total_votes': session.query(func.count(Vote.id)).scalar(),
            'personalities': []
        }
        
        for personality in session.query(Personality).all():
            p_stats = {
                'name': personality.name,
                'file_name': personality.file_name,
                'quotes_count': personality.quotes_count,
                'top_quotes': []
            }
            
            # Get top 3 quotes for this personality
            top_quotes = session.query(Quote).\
                filter(Quote.personality_id == personality.id).\
                order_by((Quote.upvotes - Quote.downvotes).desc()).\
                limit(3).all()
            
            for quote in top_quotes:
                p_stats['top_quotes'].append({
                    'id': quote.id,
                    'number': quote.number,
                    'content': quote.content,
                    'score': quote.upvotes - quote.downvotes
                })
            
            stats['personalities'].append(p_stats)
        
        return jsonify(stats)
    except Exception as e:
        app.logger.error(f"API error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

def run_app():
    """Run the Flask app"""
    app.run(host=HOST, port=PORT, debug=True)

if __name__ == '__main__':
    run_app()
