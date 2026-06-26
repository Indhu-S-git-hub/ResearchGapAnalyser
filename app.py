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
topic_modeler = TopicModeler(n_topics=2)
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
    print("STEP 1 - Upload request received", flush=True)

    try:
        if 'files' not in request.files:
            print("STEP 2 - No files found", flush=True)
            return jsonify({"error": "No files uploaded"}), 400

        files = request.files.getlist('files')
        print(f"STEP 3 - Number of files: {len(files)}", flush=True)

        uploaded_paper_ids = []

        for file in files:

            print(f"STEP 4 - Processing {file.filename}", flush=True)

            if file.filename == '':
                continue

            if file and file.filename.lower().endswith(".pdf"):

                filename = secure_filename(file.filename)
                saved_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                print("STEP 5 - Saving PDF", flush=True)
                file.save(saved_path)

                print("STEP 6 - Creating Paper record", flush=True)
                paper_record = Paper(
                    user_id=current_user.id,
                    filename=filename
                )

                db.session.add(paper_record)
                db.session.commit()

                print("STEP 7 - Database saved", flush=True)

                try:

                    print("STEP 8 - PDF Extraction", flush=True)
                    extractor = PDFExtractor(saved_path)

                    print("STEP 9 - Metadata", flush=True)
                    meta = extractor.extract_metadata()

                    print("STEP 10 - Preprocessing", flush=True)
                    raw_text = meta["raw_text"][:20000]   # only first 20,000 characters
                    cleaned = preprocessor.clean_text(raw_text)

                    print("STEP 11 - Summary", flush=True)
                    summary_data = summarizer.generate_individual_summary(raw_text, meta)

                    print("STEP 12 - Keywords", flush=True)
                    keywords_data = keyword_extractor.extract_keywords(cleaned, raw_text)
                    raw_text = meta["raw_text"][:20000]
                    cleaned = raw_text
                    summary_data = "{}"
                    keywords_data = "[]"
                    print("STEP 13 - Save Details", flush=True)

                    details = PaperDetails(
                        paper_id=paper_record.id,
                        title=meta["title"],
                        authors=meta["authors"],
                        abstract=meta["abstract"],
                        publication_year=meta["publication_year"],
                        conclusion=meta["conclusion"],
                        references=meta["references"],
                        total_pages=meta["total_pages"],
                        raw_text=cleaned
                    )

                    summary_row = PaperSummary(
                        paper_id=paper_record.id,
                        individual_summary=summary_data
                    )

                    keyword_row = PaperKeywords(
                    paper_id=paper_record.id,
                        keywords_list=keywords_data
                    )

                    db.session.add(details)
                    db.session.add(summary_row)
                    db.session.add(keyword_row)

                    db.session.commit()

                    print("STEP 14 - Saved Successfully", flush=True)

                    uploaded_paper_ids.append(paper_record.id)

                except Exception as e:

                    print("UPLOAD PIPELINE ERROR", flush=True)
                    print(str(e), flush=True)

                    db.session.rollback()

                    return jsonify({
                        "error": str(e)
                    }), 500

                finally:

                    if os.path.exists(saved_path):
                        os.remove(saved_path)

        print("STEP 15 - Topic Modeling", flush=True)

        all_user_papers = Paper.query.filter_by(
            user_id=current_user.id
        ).all()

        if len(all_user_papers) > 0:

            corpus = [
                p.details.raw_text
                for p in all_user_papers
                if p.details
            ]

            for p in all_user_papers:
                if p.topics:
                    db.session.delete(p.topics)

            db.session.commit()

            assignments = topic_modeler.fit_predict_topics(corpus)

            target_papers = [
                p for p in all_user_papers
                if p.details
            ]

            for i, assignment in enumerate(assignments):

                if i >= len(target_papers):
                    break

                topic = PaperTopics(
                    paper_id=target_papers[i].id,
                    dominant_topic=assignment["dominant_topic"],
                    topic_distribution=assignment["distribution"]
                )

                db.session.add(topic)

            db.session.commit()

        print("STEP 16 - Upload Finished", flush=True)

        return jsonify({
            "success": True,
            "processed_count": len(uploaded_paper_ids)
        })

    except Exception as e:

        print("FATAL ERROR", flush=True)
        print(str(e), flush=True)

        db.session.rollback()

        return jsonify({
            "error": str(e)
        }), 500
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