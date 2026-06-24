import os
import sys

# Forces Python path routing lookup engines to accurately recognize local module spaces
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import json

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Blueprint components loading natively from module environment directory space
from modules.models import db, User, Paper, PaperDetails, PaperSummary, PaperKeywords, PaperTopics
from modules.pdf_extractor import PDFExtractor
from modules.preprocessor import TextPreprocessor
from modules.summarizer import PaperSummarizer
from modules.keyword_extractor import KeywordExtractor
from modules.topic_modeler import TopicModeler
from modules.similarity_analyzer import SimilarityAnalyzer
from modules.gap_detector import ResearchGapDetector
from modules.recommender import ProjectRecommender
from modules.opportunity_radar import OpportunityRadar
from modules.pitch_generator import PitchGenerator

app = Flask(__name__)

# Core Application Settings Configurations
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production-19283'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # Enforces safe 32MB maximum payload limit

# Guard and maintain runtime local filesystem storage requirements
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Connect persistent database and session engine handlers
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize Global Application Core Analytics Singletons
preprocessor = TextPreprocessor()
summarizer = PaperSummarizer()
keyword_extractor = KeywordExtractor()
topic_modeler = TopicModeler(n_topics=3)
similarity_analyzer = SimilarityAnalyzer()
gap_detector = ResearchGapDetector()
recommender = ProjectRecommender()
opportunity_radar = OpportunityRadar()
pitch_generator = PitchGenerator()

# --- AUTHENTICATION ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first() or User.query.filter_by(username=username).first():
            flash('Username or Email address already registered.', 'danger')
            return redirect(url_for('register'))
            
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password, method='scrypt')
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid login credentials. Please try again.', 'danger')
            return redirect(url_for('login'))
            
        login_user(user)
        return redirect(url_for('dashboard'))
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out cleanly.', 'info')
    return redirect(url_for('login'))

# --- INTERACTIVE WORKSPACE APPLICATION ENDPOINTS ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_papers = Paper.query.filter_by(user_id=current_user.id).order_by(Paper.upload_date.desc()).all()
    return render_template('dashboard.html', papers=user_papers)

@app.route('/upload', methods=['POST'])
@login_required
def upload_papers():
    if 'files' not in request.files:
        return jsonify({"error": "No file streams present inside request matrix."}), 400
        
    files = request.files.getlist('files')
    uploaded_paper_ids = []
    
    for file in files:
        if file.filename == '':
            continue
            
        if file and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            saved_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(saved_path)
            
            paper_record = Paper(user_id=current_user.id, filename=filename)
            db.session.add(paper_record)
            db.session.commit()
            
            try:
                extractor = PDFExtractor(saved_path)
                meta = extractor.extract_metadata()
                cleaned = preprocessor.clean_text(meta['raw_text'])
                summary_data = summarizer.generate_individual_summary(meta['raw_text'], meta)
                keywords_data = keyword_extractor.extract_keywords(cleaned, meta['raw_text'])
                
                details_record = PaperDetails(
                    paper_id=paper_record.id,
                    title=meta['title'],
                    authors=meta['authors'],
                    abstract=meta['abstract'],
                    publication_year=meta['publication_year'],
                    conclusion=meta['conclusion'],
                    references=meta['references'],
                    total_pages=meta['total_pages'],
                    raw_text=cleaned
                )
                
                summary_record = PaperSummary(paper_id=paper_record.id, individual_summary=summary_data)
                keywords_record = PaperKeywords(paper_id=paper_record.id, keywords_list=keywords_data)
                
                db.session.add_all([details_record, summary_record, keywords_record])
                db.session.commit()
                uploaded_paper_ids.append(paper_record.id)
                
            except Exception as pipeline_crash:
                db.session.delete(paper_record)
                db.session.commit()
                print(f"Pipeline failure on file {filename}: {str(pipeline_crash)}")
                return jsonify({"error": f"Failed running pipeline processing on {filename}."}), 500
            finally:
                if os.path.exists(saved_path):
                    os.remove(saved_path)

    all_user_papers = Paper.query.filter_by(user_id=current_user.id).all()
    if len(all_user_papers) > 0:
        corpus = [p.details.raw_text for p in all_user_papers if p.details]
        for p in all_user_papers:
            if p.topics:
                db.session.delete(p.topics)
        db.session.commit()
        
        topic_assignments = topic_modeler.fit_predict_topics(corpus)
        for idx, assignment in enumerate(topic_assignments):
            target_papers = [p for p in all_user_papers if p.details]
            if idx < len(target_papers):
                target_paper = target_papers[idx]
                topic_rec = PaperTopics(
                    paper_id=target_paper.id,
                    dominant_topic=assignment['dominant_topic'],
                    topic_distribution=assignment['distribution']
                )
                db.session.add(topic_rec)
        db.session.commit()

    return jsonify({"success": True, "processed_count": len(uploaded_paper_ids)})

@app.route('/analyze-collective')
@login_required
def analyze_collective():
    user_papers = Paper.query.filter_by(user_id=current_user.id).all()
    if len(user_papers) < 2:
        return jsonify({"error": "Please upload at least 2 papers to open collective metrics."}), 400

    corpus = [p.details.raw_text for p in user_papers if p.details]
    filenames = [p.filename for p in user_papers]
    summaries = [p.summary.individual_summary for p in user_papers if p.summary]

    if len(corpus) < 2:
        return jsonify({"error": "Insufficient text model entries compiled to generate analytics."}), 400

    similarity_json = similarity_analyzer.compute_similarity_matrix(corpus, filenames)
    combined_summary = summarizer.generate_combined_summary(summaries)
    
    aggregated_raw = " ".join(corpus)
    detected_gaps_json = gap_detector.detect_gaps(aggregated_raw, summaries[0] if summaries else "")
    
    latest_topic_dist = user_papers[-1].topics.topic_distribution if user_papers[-1].topics else "{}"
    recommendations_json = recommender.generate_recommendations(latest_topic_dist, detected_gaps_json)
    opportunities_json = opportunity_radar.generate_opportunities(latest_topic_dist, detected_gaps_json, similarity_json)
    pitch_text = pitch_generator.generate_pitch(combined_summary, filenames, latest_topic_dist)

    return jsonify({
        "similarity_matrix": json.loads(similarity_json),
        "combined_summary": combined_summary,
        "gap_analysis": json.loads(detected_gaps_json),
        "recommendations": json.loads(recommendations_json),
        "opportunities": json.loads(opportunities_json),
        "elevator_pitch": pitch_text
    })

@app.route('/delete-paper/<int:paper_id>', methods=['POST'])
@login_required
def delete_paper(paper_id):
    try:
        # Repaired SQLAlchemy lookup call from image source traces
        paper = Paper.query.get_or_404(paper_id)
        if paper.user_id != current_user.id:
            return jsonify({"error": "Unauthorized data alteration signatures identified."}), 403
            
        if hasattr(paper, 'details') and paper.details:
            db.session.delete(paper.details)
        if hasattr(paper, 'summary') and paper.summary:
            db.session.delete(paper.summary)
        if hasattr(paper, 'keywords') and paper.keywords:
            db.session.delete(paper.keywords)
        if hasattr(paper, 'topics') and paper.topics:
            db.session.delete(paper.topics)
            
        db.session.delete(paper)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# Executed manually from execution terminal spaces
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database tables initialized successfully inside database.db!")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='127.0.0.1', port=5000)