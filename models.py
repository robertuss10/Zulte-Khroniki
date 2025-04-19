from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Personality(Base):
    __tablename__ = 'personalities'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    file_name = Column(String(50), nullable=False)
    quotes_count = Column(Integer, default=0)
    
    quotes = relationship("Quote", back_populates="personality")
    
    def __repr__(self):
        return f"<Personality {self.name}>"

class Quote(Base):
    __tablename__ = 'quotes'
    
    id = Column(Integer, primary_key=True)
    personality_id = Column(Integer, ForeignKey('personalities.id'), nullable=False)
    number = Column(Integer, nullable=False)  # Quote number in the original file
    content = Column(String(1000), nullable=False)
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    use_count = Column(Integer, default=0)
    
    personality = relationship("Personality", back_populates="quotes")
    
    @property
    def score(self):
        return self.upvotes - self.downvotes
    
    def __repr__(self):
        return f"<Quote {self.personality.name} #{self.number}>"

class Command(Base):
    __tablename__ = 'commands'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False)
    command = Column(String(50), nullable=False)
    quote_id = Column(Integer, ForeignKey('quotes.id'), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Command {self.command} by {self.user_id} at {self.timestamp}>"

class Vote(Base):
    __tablename__ = 'votes'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False)
    quote_id = Column(Integer, ForeignKey('quotes.id'), nullable=False)
    vote = Column(Integer, nullable=False)  # 1 for upvote, -1 for downvote
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Vote {self.vote} by {self.user_id} for quote {self.quote_id}>"

class Stats(Base):
    __tablename__ = 'stats'
    
    id = Column(Integer, primary_key=True)
    personality_id = Column(Integer, ForeignKey('personalities.id'), nullable=False)
    total_quotes_used = Column(Integer, default=0)
    total_upvotes = Column(Integer, default=0)
    total_downvotes = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    personality = relationship("Personality")
    
    def __repr__(self):
        return f"<Stats for {self.personality.name}>"
