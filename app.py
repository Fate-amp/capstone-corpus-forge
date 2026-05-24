"""
Flask application factory and main entry point.

Creates and configures the Flask app, sets up routes, and initializes services.

Usage:
    python app.py

PHASE 1 Routes to implement (Days 1-5):
    GET /                           → Dashboard (documents, chat, settings, usage)
    POST /upload                    → Upload document
    POST /delete/<doc_id>           → Delete document
    POST /chat                      → Chat with AI (streaming response)
    POST /update-settings           → Update user settings

PHASE 2 Routes to implement (Days 6-11):
    GET /flashcards/<doc_id>        → Study flashcards
    POST /generate-flashcards       → Generate flashcards from document
    GET /quiz/<quiz_id>             → Take quiz
    POST /generate-quiz             → Generate quiz from document
    POST /submit-answer             → Submit quiz answer
    GET /quiz-results/<quiz_id>     → View quiz results
    POST /analyze-code/<doc_id>     → Generate code analysis

TODO: Add error handling middleware
TODO: Add logging configuration
TODO: Add request/response validation
TODO: Add security headers (CORS, CSRF, CSP)
"""

import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from pathlib import Path

from config import config
from models import db, Document, ChatMessage, Settings
from services.document_processor import (
    extract_text_by_file_type,
    get_preview_text,
)
from services.ai_agent import AIAgent
from services.embeddings import EmbeddingsService
from services.usage_tracker import UsageTracker
from utils.helpers import allowed_file, get_file_type, get_secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(config_name='development'):
    """
    Application factory function.
    
    Args:
        config_name (str): Configuration environment (development, testing, production)
        
    Returns:
        Flask: Configured Flask application
        
    TODO: Add error handlers
    TODO: Add before_request/after_request hooks
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize services (these will be available in request context)
    app.ai_agent = None
    app.embeddings_service = None
    
    # Register hooks to initialize services on first request
    @app.before_request
    def init_services():
        """Initialize AI services if not already done."""
        if app.ai_agent is None:
            try:
                app.ai_agent = AIAgent(
                    api_key=app.config.get('GOOGLE_API_KEY'),
                    model_name=app.config.get('DEFAULT_MODEL')
                )
                app.embeddings_service = EmbeddingsService(
                    chromadb_path=app.config.get('CHROMADB_PATH'),
                    api_key=app.config.get('GOOGLE_API_KEY')
                )
                logger.info("Services initialized")
            except Exception as e:
                logger.error(f"Error initializing services: {str(e)}")
    
    # Create upload folder
    with app.app_context():
        Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
        Path(app.config['CHROMADB_PATH']).mkdir(parents=True, exist_ok=True)
        
        # Create database tables
        db.create_all()
    
    # Register routes
    register_routes(app)
    
    return app


def register_routes(app):
    """
    Register all Flask routes.
    
    Args:
        app: Flask application
        
    TODO: Organize routes into blueprints for better modularity
    """
    
    # ========================================================================
    # PHASE 1: Core Chat Loop (Days 1-5)
    # ========================================================================
    
    @app.route('/', methods=['GET'])
    def dashboard():
        """
        Render main dashboard.
        
        Displays:
        - Document sidebar (list of uploaded documents)
        - Chat box (conversation history + input)
        - Settings panel (model parameters)
        - Usage dashboard (token statistics)
        
        TODO: Add error handling if database is unavailable
        TODO: Add pagination for large document lists
        """
        try:
            documents = Document.query.all()
            settings = Settings.query.first() or Settings()
            usage_stats = UsageTracker.get_total_usage()
            recent_usage = UsageTracker.get_recent_usage(limit=5)
            
            return render_template(
                'dashboard.html',
                documents=documents,
                settings=settings,
                usage_stats=usage_stats,
                recent_usage=recent_usage
            )
        except Exception as e:
            logger.error(f"Error rendering dashboard: {str(e)}")
            return render_template('error.html', error=str(e)), 500
    
    @app.route('/upload', methods=['POST'])
    def upload_document():
        """
        Handle document upload, extract text, embed, and store in DB
        """
        from werkzeug.utils import secure_filename
        import os
        from services.document_processor import extract_text_from_pdf
        from services.embeddings import EmbeddingsService
        
        try:
            # Step 1: Validate file upload
            if 'file' not in request.files:
                logger.warning("Upload attempt with no file")
                return jsonify({'error': 'No file uploaded'}), 400
            
            file = request.files['file']
            if file.filename == '':
                logger.warning("Upload attempt with empty filename")
                return jsonify({'error': 'No file selected'}), 400
            
            # Step 2: Check file extension
            if not allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
                logger.warning(f"Upload attempt with disallowed extension: {file.filename}")
                return jsonify({'error': 'File type not allowed'}), 400
            
            # Step 3: Save file to disk
            filename = secure_filename(file.filename)
            upload_folder = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            logger.info(f"Saved file: {filepath}")
            
            # Step 4: Extract text from file
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext == '.pdf':
                text = extract_text_from_pdf(filepath)
            else:
                # For TXT and code files
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        text = f.read()
                except:
                    with open(filepath, 'r', encoding='latin-1') as f:
                        text = f.read()
            
            logger.info(f"Extracted {len(text)} characters from {filename}")
            
            # Step 5: Create Document in database
            preview = text[:200] + "..." if len(text) > 200 else text
            title = os.path.splitext(filename)[0]  # Filename without extension
            doc = Document(
                filename=filename,
                title=title,
                file_path=filepath,
                file_type=file_ext,
                content_preview=preview
            )
            db.session.add(doc)
            db.session.commit()
            logger.info(f"Created document in DB: id={doc.id}, filename={filename}")
            
            # Step 6: Generate embeddings
            try:
                api_key = os.getenv('GOOGLE_API_KEY')
                embeddings = EmbeddingsService(api_key=api_key)
                embeddings.embed_document(doc_id=doc.id, document_text=text)
                logger.info(f"Embedded document {doc.id} in ChromaDB")
            except Exception as e:
                logger.error(f"Error embedding document {doc.id}: {str(e)}")
                # Continue anyway - embeddings can fail without blocking upload
            
            logger.info(f"Successfully uploaded document: {filename}")
            return jsonify({
                'success': True,
                'document_id': doc.id,
                'message': f'Document "{filename}" uploaded successfully'
            }), 201
        
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            return jsonify({'error': f'Upload failed: {str(e)}'}), 500
            logger.error(f"Error uploading document: {str(e)}")
            return redirect(url_for('dashboard'))
    
    @app.route('/delete/<int:doc_id>', methods=['POST'])
    def delete_document(doc_id):
        """
        Delete a document.
        
        Workflow:
        1. Find document in database
        2. Delete file from static/uploads/
        3. Delete embeddings from ChromaDB
        4. Delete Document entry from database (cascade delete ChatMessage)
        5. Redirect to dashboard
        
        Args:
            doc_id (int): Document ID to delete
            
        TODO: Add confirmation dialog on frontend
        TODO: Add soft delete option (archive instead of delete)
        
        Day 2 Implementation Checklist:
        □ Query Document by id
        □ Delete file at document.file_path
        □ Delete embeddings from ChromaDB
        □ Delete Document from database
        □ Commit transaction
        □ Redirect to GET /
        """
        try:
            # TODO: Day 2 Implementation goes here
            
            logger.info(f"Deleted document {doc_id}")
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {str(e)}")
            return redirect(url_for('dashboard'))
    
    @app.route('/chat', methods=['POST'])
    def chat():
        """
        Handle chat request (query about a document).
        
        Workflow:
        1. Extract query, document_id, and settings from request
        2. Retrieve context from ChromaDB using embeddings
        3. Generate AI response (streaming)
        4. Save ChatMessage to database
        5. Log usage (tokens consumed)
        6. Stream response back to client
        
        Form data (JSON):
        - query: User's question
        - document_id: Which document to query
        - temperature: Model creativity (optional)
        - top_p: Model diversity (optional)
        
        Response:
        - Streaming text chunks (for real-time display)
        
        TODO: Add query validation
        TODO: Add rate limiting
        TODO: Add error recovery
        
        Day 4 Implementation Checklist:
        □ Get query and document_id from request
        □ Get Settings for temperature, top_p, audience, tone
        □ Retrieve context from ChromaDB
        □ Call AIAgent.generate_response() to get generator
        □ Create streaming response
        □ For each chunk yielded:
          □ Send to client
        □ After streaming completes:
          □ Get token counts from generator return
          □ Create ChatMessage entry
          □ Log usage with UsageTracker
          □ Commit to database
        """
        try:
            # TODO: Day 4 Implementation goes here
            
            return jsonify({'status': 'ok'})
        
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/update-settings', methods=['POST'])
    def update_settings():
        """
        Update user settings and preferences.
        
        Form data (JSON):
        - temperature: 0.0-2.0
        - top_p: 0.0-1.0
        - audience_level: beginner/intermediate/expert
        - tone: formal/casual/technical/friendly
        - model_choice: AI model to use
        - max_tokens_per_response: Max response length
        
        TODO: Add input validation
        TODO: Add constraints checking
        
        Day 5 Implementation Checklist:
        □ Get or create Settings entry (id=1)
        □ Update fields from request
        □ Validate ranges (temp 0-2, top_p 0-1)
        □ Save to database
        □ Return success response or redirect
        """
        try:
            # TODO: Day 5 Implementation goes here
            
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            logger.error(f"Error updating settings: {str(e)}")
            return redirect(url_for('dashboard'))
    
    # ========================================================================
    # PHASE 2: Extended Features (Days 6-11)
    # ========================================================================
    # Routes for flashcards, quizzes, and code analysis will be added here
    # See plan.md for detailed implementation specs
    
    @app.route('/generate-flashcards', methods=['POST'])
    def generate_flashcards():
        """PHASE 2: Generate flashcards from a document."""
        # TODO: Implement in Days 6-7
        return jsonify({'error': 'Not implemented'}), 501
    
    @app.route('/generate-quiz', methods=['POST'])
    def generate_quiz():
        """PHASE 2: Generate quiz from a document."""
        # TODO: Implement in Days 8-9
        return jsonify({'error': 'Not implemented'}), 501
    
    @app.route('/analyze-code/<int:doc_id>', methods=['POST'])
    def analyze_code(doc_id):
        """PHASE 2: Generate code analysis."""
        # TODO: Implement in Day 10
        return jsonify({'error': 'Not implemented'}), 501
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return render_template('error.html', error='Page not found'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        db.session.rollback()
        logger.error(f"Internal server error: {str(error)}")
        return render_template('error.html', error='Internal server error'), 500


if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
