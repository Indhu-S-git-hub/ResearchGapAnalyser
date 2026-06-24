from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    papers = db.relationship('Paper', backref='uploader', lazy=True, cascade="all, delete-orphan")

class Paper(db.Model):
    __tablename__ = 'papers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships to child tables for structural modularity
    details = db.relationship('PaperDetails', backref='paper', uselist=False, cascade="all, delete-orphan")
    summary = db.relationship('PaperSummary', backref='paper', uselist=False, cascade="all, delete-orphan")
    keywords = db.relationship('PaperKeywords', backref='paper', uselist=False, cascade="all, delete-orphan")
    topics = db.relationship('PaperTopics', backref='paper', uselist=False, cascade="all, delete-orphan")

class PaperDetails(db.Model):
    __tablename__ = 'paper_details'
    id = db.Column(db.Integer, primary_key=True)
    paper_id = db.Column(db.Integer, db.ForeignKey('papers.id'), nullable=False)
    title = db.Column(db.Text, nullable=True)
    authors = db.Column(db.Text, nullable=True)
    abstract = db.Column(db.Text, nullable=True)
    publication_year = db.Column(db.Integer, nullable=True)
    conclusion = db.Column(db.Text, nullable=True)
    references = db.Column(db.Text, nullable=True)
    total_pages = db.Column(db.Integer, nullable=True)
    raw_text = db.Column(db.Text, nullable=True) # Held for running calculations downstream

class PaperSummary(db.Model):
    __tablename__ = 'paper_summaries'
    id = db.Column(db.Integer, primary_key=True)
    paper_id = db.Column(db.Integer, db.ForeignKey('papers.id'), nullable=False)
    individual_summary = db.Column(db.Text, nullable=False) # JSON structure or raw text detailing problem, method, results

class PaperKeywords(db.Model):
    __tablename__ = 'paper_keywords'
    id = db.Column(db.Integer, primary_key=True)
    paper_id = db.Column(db.Integer, db.ForeignKey('papers.id'), nullable=False)
    keywords_list = db.Column(db.Text, nullable=False) # Comma-separated or JSON string of top keywords

class PaperTopics(db.Model):
    __tablename__ = 'paper_topics'
    id = db.Column(db.Integer, primary_key=True)
    paper_id = db.Column(db.Integer, db.ForeignKey('papers.id'), nullable=False)
    dominant_topic = db.Column(db.String(255), nullable=False)
    topic_distribution = db.Column(db.Text, nullable=False) # JSON representation of distributions