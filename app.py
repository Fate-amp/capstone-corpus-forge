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
            # Check if file exists in request
            if 'file' not in request.files:
                logger.warning("Upload attempt with no file")
                return jsonify({'status': 'error', 'message': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                logger.warning("Upload attempt with empty filename")
                return jsonify({'status': 'error', 'message': 'Empty filename'}), 400
            
            # Check file extension
            if not allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
                logger.warning(f"Upload attempt with disallowed extension: {file.filename}")
                return jsonify({
                    'status': 'error', 
                    'message': f'File type not allowed. Allowed types: {", ".join(app.config["ALLOWED_EXTENSIONS"])}'
                }), 400
            
            # Create uploads directory if needed
            Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
            
            # Save file with secure filename
            secure_fname = get_secure_filename(file.filename)
            file_type = get_file_type(file.filename)
            file_path = Path(app.config['UPLOAD_FOLDER']) / secure_fname
            
            try:
                file.save(str(file_path))
                logger.info(f"Saved file to {file_path}")
            except Exception as e:
                logger.error(f"Error saving file: {str(e)}")
                return jsonify({'status': 'error', 'message': f'Error saving file: {str(e)}'}), 500
            
            # Extract text using document_processor
            try:
                extracted_text = extract_text_by_file_type(str(file_path), file_type)
                if not extracted_text or not extracted_text.strip():
                    logger.warning(f"No text extracted from {file.filename}")
                    return jsonify({'status': 'error', 'message': 'No text could be extracted from file'}), 400
                logger.info(f"Extracted {len(extracted_text)} characters from {file.filename}")
            except Exception as e:
                logger.error(f"Error extracting text: {str(e)}")
                # Clean up file on extraction failure
                try:
                    file_path.unlink()
                except:
                    pass
                return jsonify({'status': 'error', 'message': f'Error extracting text: {str(e)}'}), 500
            
            # Generate preview text
            try:
                preview_text = get_preview_text(extracted_text, max_chars=500)
            except Exception as e:
                logger.error(f"Error generating preview: {str(e)}")
                preview_text = extracted_text[:500]
            
            # Create Document model instance and save to database
            try:
                doc = Document(
                    filename=file.filename,
                    title=file.filename,
                    content_preview=preview_text,
                    file_path=str(file_path),
                    file_type=file_type
                )
                db.session.add(doc)
                db.session.commit()
                logger.info(f"Created Document entry: {doc.id} for {file.filename}")
            except Exception as e:
                logger.error(f"Error saving document to database: {str(e)}")
                db.session.rollback()
                # Clean up file on database failure
                try:
                    file_path.unlink()
                except:
                    pass
                return jsonify({'status': 'error', 'message': f'Error saving document: {str(e)}'}), 500
            
            # Generate embeddings and store in ChromaDB
            try:
                app.embeddings_service.embed_document(doc.id, extracted_text)
                logger.info(f"Generated embeddings for document {doc.id}")
            except Exception as e:
                logger.error(f"Error generating embeddings for document {doc.id}: {str(e)}")
                # Continue even if embeddings fail, document is still stored
            
            logger.info(f"Successfully uploaded document: {file.filename}")
            return jsonify({
                'status': 'success', 
                'message': f'Document "{file.filename}" uploaded successfully',
                'doc_id': doc.id,
                'redirect': url_for('dashboard')
            }), 200
        
        except Exception as e:
            logger.error(f"Unexpected error uploading document: {str(e)}")
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'Unexpected error: {str(e)}'}), 500
    
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
            # Get query and document_id from request
            data = request.get_json()
            query = data.get('query', '').strip()
            document_id = data.get('document_id', None)
            
            if not query:
                logger.warning("Chat request with empty query")
                return jsonify({'error': 'Query cannot be empty'}), 400
            
            if not document_id:
                logger.warning("Chat request with no document_id")
                return jsonify({'error': 'Document must be selected'}), 400
            
            # Verify document exists
            doc = Document.query.get(document_id)
            if not doc:
                logger.warning(f"Chat request for non-existent document {document_id}")
                return jsonify({'error': 'Document not found'}), 404
            
            # Get Settings for temperature, top_p, audience, tone
            settings = Settings.query.first() or Settings()
            
            # Retrieve context from ChromaDB
            try:
                context = app.embeddings_service.retrieve_context(
                    query=query,
                    doc_id=document_id,
                    top_k=3
                )
                if not context.strip():
                    logger.warning(f"No context retrieved for document {document_id}")
                    context = "No relevant context found. Please try rephrasing your question."
            except Exception as e:
                logger.error(f"Error retrieving context: {str(e)}")
                context = "Error retrieving document context. Please try again."
            
            # Call AIAgent.generate_response() to get generator
            try:
                response_generator = app.ai_agent.generate_response(
                    query=query,
                    context=context,
                    temperature=settings.temperature,
                    top_p=settings.top_p,
                    max_tokens=settings.max_tokens_per_response,
                    audience_level=settings.audience_level,
                    tone=settings.tone
                )
            except Exception as e:
                logger.error(f"Error initializing response generator: {str(e)}")
                return jsonify({'error': f'Failed to generate response: {str(e)}'}), 500
            
            # Create streaming response
            def generate_stream():
                full_response = ""
                
                try:
                    # Collect all chunks from the generator
                    for chunk in response_generator:
                        full_response += chunk
                        # Send chunk to client in Server-Sent Events format
                        # Format: "data: <message>\n\n"
                        yield f"data: {chunk}\n\n"
                    
                except GeneratorExit:
                    # Handle client disconnect
                    logger.info("Client disconnected from chat stream")
                except Exception as e:
                    logger.error(f"Error during streaming: {str(e)}")
                    yield f"data: [ERROR] {str(e)}\n\n"
                finally:
                    # After streaming completes, save to database
                    if full_response:
                        try:
                            # Estimate token counts based on response length
                            tokens_input = len(query.split()) * 2  # Rough estimate: ~2 tokens per word
                            tokens_output = len(full_response.split()) * 2
                            
                            # Create ChatMessage entry
                            chat_msg = ChatMessage(
                                document_id=document_id,
                                query=query,
                                response=full_response,
                                tokens_input=tokens_input,
                                tokens_output=tokens_output,
                                tokens_used=tokens_input + tokens_output,
                                temperature=settings.temperature,
                                top_p=settings.top_p
                            )
                            db.session.add(chat_msg)
                            
                            # Log usage with UsageTracker
                            UsageTracker.log_usage(
                                model_name=app.config.get('DEFAULT_MODEL', 'gemini-pro'),
                                tokens_input=tokens_input,
                                tokens_output=tokens_output,
                                request_type='chat'
                            )
                            
                            # Commit to database
                            db.session.commit()
                            logger.info(f"Chat message saved: {tokens_input + tokens_output} tokens, response length: {len(full_response)}")
                        except Exception as e:
                            logger.error(f"Error saving chat message: {str(e)}")
                            db.session.rollback()
            
            return generate_stream(), 200, {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        
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
            # Get or create Settings entry (id=1)
            settings = Settings.query.first()
            if not settings:
                settings = Settings(id=1)
                db.session.add(settings)
            
            # Extract form data from request (JSON or form data)
            data = request.get_json() if request.is_json else request.form
            
            # Update temperature field and validate range (0-2)
            if 'temperature' in data:
                temp = float(data['temperature'])
                if 0.0 <= temp <= 2.0:
                    settings.temperature = temp
                else:
                    logger.warning(f"Invalid temperature value: {temp}")
                    return jsonify({'error': 'Temperature must be between 0.0 and 2.0'}), 400
            
            # Update top_p field and validate range (0-1)
            if 'top_p' in data:
                top_p = float(data['top_p'])
                if 0.0 <= top_p <= 1.0:
                    settings.top_p = top_p
                else:
                    logger.warning(f"Invalid top_p value: {top_p}")
                    return jsonify({'error': 'Top-p must be between 0.0 and 1.0'}), 400
            
            # Update audience_level
            if 'audience_level' in data:
                audience = data['audience_level'].lower()
                if audience in ['beginner', 'intermediate', 'expert']:
                    settings.audience_level = audience
                else:
                    logger.warning(f"Invalid audience_level value: {audience}")
            
            # Update tone
            if 'tone' in data:
                tone = data['tone'].lower()
                if tone in ['formal', 'casual', 'technical', 'friendly']:
                    settings.tone = tone
                else:
                    logger.warning(f"Invalid tone value: {tone}")
            
            # Update model_choice
            if 'model_choice' in data:
                settings.model_choice = data['model_choice']
            
            # Update max_tokens_per_response
            if 'max_tokens_per_response' in data:
                try:
                    max_tokens = int(data['max_tokens_per_response'])
                    if max_tokens > 0:
                        settings.max_tokens_per_response = max_tokens
                except ValueError:
                    logger.warning(f"Invalid max_tokens_per_response value: {data['max_tokens_per_response']}")
            
            # Save to database
            db.session.commit()
            logger.info(f"Updated settings: temp={settings.temperature}, top_p={settings.top_p}, audience={settings.audience_level}, tone={settings.tone}")
            
            # Return success response or redirect
            if request.is_json:
                return jsonify({'status': 'success', 'settings': settings.to_dict()}), 200
            else:
                return redirect(url_for('dashboard'))
        
        except ValueError as e:
            logger.error(f"Invalid settings value: {str(e)}")
            if request.is_json:
                return jsonify({'error': f'Invalid settings value: {str(e)}'}), 400
            else:
                return redirect(url_for('dashboard'))
        
        except Exception as e:
            logger.error(f"Error updating settings: {str(e)}")
            db.session.rollback()
            if request.is_json:
                return jsonify({'error': str(e)}), 500
            else:
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
