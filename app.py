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
    GET  /get-usage-stats           → Return usage data as JSON

PHASE 2 Routes to implement (Days 6-11):
    GET /flashcards/<doc_id>        → Study flashcards
    POST /generate-flashcards       → Generate flashcards from document
    GET /quiz/<quiz_id>             → Take quiz
    POST /generate-quiz             → Generate quiz from document
    POST /submit-answer             → Submit quiz answer
    GET /quiz-results/<quiz_id>     → View quiz results
    POST /analyze-code/<doc_id>     → Generate code analysis
"""

import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from pathlib import Path

from config import config
from models import db, Document, ChatMessage, Settings, Flashcard, Quiz, QuizQuestion, QuizResult, CodeAnalysis
from services.document_processor import (
    extract_text_by_file_type,
    extract_text_from_pdf,
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
        if app.embeddings_service is None:
            try:
                app.embeddings_service = EmbeddingsService(
                    chromadb_path=app.config.get('CHROMADB_PATH'),
                    api_key=app.config.get('GOOGLE_API_KEY')
                )
                logger.info("Embeddings service initialized")
            except Exception as e:
                logger.error(f"Error initializing embeddings service: {str(e)}")

        if app.ai_agent is None:
            try:
                app.ai_agent = AIAgent(
                    api_key=app.config.get('GOOGLE_API_KEY'),
                    model_name=app.config.get('DEFAULT_MODEL')
                )
                logger.info("AI agent initialized")
            except Exception as e:
                logger.warning(f"AI agent unavailable, fallback mode enabled: {str(e)}")

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
        Handle document upload, extract text, embed, and store in DB.

        DAY 2: File validation, saving, DB creation.
        DAY 3: Embeddings wired in.
        """
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
                return jsonify({'error': 'File type not allowed. Accepted: PDF, TXT, and code files.'}), 400

            # Step 3: Save file to disk with a secure name
            filename = secure_filename(file.filename)
            upload_folder = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)

            # Handle duplicate filenames by appending a counter
            base, ext = os.path.splitext(filename)
            counter = 1
            filepath = os.path.join(upload_folder, filename)
            while os.path.exists(filepath):
                filename = f"{base}_{counter}{ext}"
                filepath = os.path.join(upload_folder, filename)
                counter += 1

            file.save(filepath)
            logger.info(f"Saved file: {filepath}")

            # Step 4: Extract text from file
            file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
            text = extract_text_by_file_type(filepath, file_ext)
            logger.info(f"Extracted {len(text)} characters from {filename}")

            # Step 5: Create Document in database
            preview = get_preview_text(text, max_chars=500)
            title = os.path.splitext(filename)[0]   # filename without extension as title
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

            # Step 6: Generate embeddings (DAY 3 — wired in)
            try:
                if app.embeddings_service:
                    app.embeddings_service.embed_document(doc_id=doc.id, document_text=text)
                    logger.info(f"Embedded document {doc.id} into ChromaDB")
                else:
                    logger.warning("Embeddings service not available; skipping embedding step")
            except Exception as e:
                logger.error(f"Error embedding document {doc.id}: {str(e)}")
                # Non-fatal: upload succeeds even if embedding fails

            logger.info(f"Successfully uploaded document: {filename}")
            return jsonify({
                'success': True,
                'document_id': doc.id,
                'message': f'Document "{filename}" uploaded successfully'
            }), 201

        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            return jsonify({'error': f'Upload failed: {str(e)}'}), 500

    # -------------------------------------------------------------------------
    # DAY 2 — Person C's main task: delete_document()
    # -------------------------------------------------------------------------
    @app.route('/delete/<int:doc_id>', methods=['POST'])
    def delete_document(doc_id):
        """
        Delete a document.

        Workflow:
        1. Find document in database
        2. Delete file from static/uploads/
        3. Delete embeddings from ChromaDB   (DAY 3)
        4. Delete Document entry from database (cascade delete ChatMessage)
        5. Redirect to dashboard

        Args:
            doc_id (int): Document ID to delete
        """
        try:
            # Step 1: Query document by ID
            doc = Document.query.get(doc_id)
            if not doc:
                logger.warning(f"Attempted to delete non-existent document: {doc_id}")
                return redirect(url_for('dashboard'))

            # Step 2: Delete file from disk
            file_path = Path(doc.file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file from disk: {file_path}")
            else:
                logger.warning(f"File not found on disk (already deleted?): {file_path}")

            # Step 3: Delete embeddings from ChromaDB (DAY 3 — wired in)
            try:
                if app.embeddings_service:
                    app.embeddings_service.delete_document_embeddings(doc_id)
                    logger.info(f"Deleted ChromaDB embeddings for document {doc_id}")
            except Exception as e:
                logger.warning(f"Could not delete embeddings for doc {doc_id}: {str(e)}")
                # Non-fatal: proceed with DB deletion even if ChromaDB cleanup fails

            # Step 4: Delete Document from database (cascade deletes ChatMessages, Flashcards, etc.)
            db.session.delete(doc)
            db.session.commit()

            logger.info(f"Successfully deleted document {doc_id}")
            return redirect(url_for('dashboard'))

        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {str(e)}")
            db.session.rollback()
            return redirect(url_for('dashboard'))

    # -------------------------------------------------------------------------
    # DAY 4 — Person C's main task: chat()
    # -------------------------------------------------------------------------
    def _format_conversation_history(document_id, limit=6):
        """Format recent chat turns so follow-up questions keep their context."""
        recent_messages = (
            db.session.query(ChatMessage)
            .filter(ChatMessage.document_id == document_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )

        if not recent_messages:
            return ""

        lines = []
        for message in reversed(recent_messages):
            lines.append(f"User: {message.query}")
            lines.append(f"Assistant: {message.response}")

        return "\n".join(lines)

    @app.route('/chat', methods=['POST'])
    def chat():
        """
        Handle chat request (query about a document).

        Workflow:
        1. Extract query, document_id from request (JSON or form data)
        2. Load Settings from database (temperature, top_p, audience_level, tone)
        3. Retrieve relevant context from ChromaDB
        4. Generate AI response using AIAgent
        5. Save ChatMessage to database
        6. Log usage with UsageTracker
        7. Return JSON response

        Request JSON:
            { "query": "...", "document_id": 1 }

        Response JSON:
            { "response": "...", "tokens_used": 123 }
        """
        try:
            # Get query and document_id from request (handle both JSON and form data)
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form
            
            query = data.get('query', '').strip()
            document_id = data.get('document_id', None)
            
            # Convert document_id to int if it's a string
            if document_id:
                try:
                    document_id = int(document_id)
                except (ValueError, TypeError):
                    document_id = None
            
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
            model_name = settings.model_choice or app.config.get('DEFAULT_MODEL', 'gemini-2.5-flash')
            if model_name in {'gemini-pro', 'gemini-pro-vision'}:
                model_name = 'gemini-2.5-flash'

            if app.ai_agent is None or app.ai_agent.model_name != model_name:
                try:
                    app.ai_agent = AIAgent(
                        api_key=app.config.get('GOOGLE_API_KEY'),
                        model_name=model_name
                    )
                except Exception as e:
                    logger.warning(f"AI service fallback will be used: {str(e)}")

            conversation_history = _format_conversation_history(document_id, limit=6)
            
            # Retrieve context from ChromaDB
            try:
                if app.embeddings_service is not None:
                    context = app.embeddings_service.retrieve_context(
                        query=query,
                        doc_id=document_id,
                        top_k=3
                    )
                else:
                    context = ""
                if not context.strip():
                    logger.warning(f"No context retrieved for document {document_id}")
                    context = "No relevant context found in the selected document."
            except Exception as e:
                logger.error(f"Error retrieving context: {str(e)}")
                context = ""

            if not context.strip():
                context = "No document context was available for this turn."
            
            # Call AIAgent.generate_response() to get generator
            try:
                if app.ai_agent is not None:
                    response_generator = app.ai_agent.generate_response(
                        query=query,
                        context=context,
                        conversation_history=conversation_history,
                        temperature=settings.temperature,
                        top_p=settings.top_p,
                        max_tokens=settings.max_tokens_per_response,
                        audience_level=settings.audience_level,
                        tone=settings.tone
                    )
                else:
                    response_generator = AIAgent._yield_chunks(
                        AIAgent._fallback_response(
                            query=query,
                            context=context,
                            conversation_history=conversation_history,
                            audience_level=settings.audience_level,
                            tone=settings.tone,
                        )
                    )
            except Exception as e:
                logger.error(f"Error initializing response generator: {str(e)}")
                response_generator = AIAgent._yield_chunks(
                    AIAgent._fallback_response(
                        query=query,
                        context=context,
                        conversation_history=conversation_history,
                        audience_level=settings.audience_level,
                        tone=settings.tone,
                    )
                )
            
            # Create streaming response
            def generate_stream():
                full_response = ""
                
                try:
                    # Collect all chunks from the generator
                    for chunk in response_generator:
                        if not chunk:
                            continue
                        full_response += chunk
                        # Send chunk to client in Server-Sent Events format
                        # Format: "data: <message>\n\n"
                        yield f"data: {chunk}\n\n"
                    
                    # After streaming completes, save to database using explicit app context
                    if full_response:
                        try:
                            history_tokens = len(conversation_history.split()) * 2
                            context_tokens = len(context.split()) * 2
                            tokens_input = len(query.split()) * 2 + history_tokens + context_tokens
                            tokens_output = len(full_response.split()) * 2

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

                            UsageTracker.log_usage(
                                model_name=model_name,
                                tokens_input=tokens_input,
                                tokens_output=tokens_output,
                                request_type='chat'
                            )

                            db.session.commit()
                            logger.info(
                                f"Chat message saved: {tokens_input + tokens_output} tokens, response length: {len(full_response)}"
                            )
                        except Exception as e:
                            logger.error(f"Error saving chat message: {str(e)}")
                    
                except GeneratorExit:
                    logger.info("Client disconnected from chat stream")
                except Exception as e:
                    logger.error(f"Error during streaming: {str(e)}")
                    yield f"data: [ERROR] {str(e)}\n\n"
            
            return generate_stream(), 200, {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return jsonify({'error': str(e)}), 500

    # -------------------------------------------------------------------------
    # DAY 5 — Person C's main tasks: update_settings() and get_usage_stats()
    # -------------------------------------------------------------------------
    @app.route('/update-settings', methods=['POST'])
    def update_settings():
        """
        Update user settings and preferences.

        Accepts both JSON and form-data (the settings_panel.html uses a <form>).

        Fields:
            temperature          : float 0.0–2.0
            top_p                : float 0.0–1.0
            audience_level       : beginner | intermediate | expert
            tone                 : formal | casual | technical | friendly
            max_tokens_per_response : int 100–4000
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
    # PHASE 2: Extended Features (Days 6-11) — Person C's backend routes
    # ========================================================================

    # -------------------------------------------------------------------------
    # DAY 6-7: Flashcard Generator
    # -------------------------------------------------------------------------
    @app.route('/generate-flashcards', methods=['POST'])
    def generate_flashcards():
        """
        Generate flashcards from a document.

        Request JSON:
            { "document_id": 1, "num_cards": 5 }

        Response JSON:
            { "flashcards": [ { "id": ..., "question": ..., "answer": ... }, ... ] }
        """
        try:
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form

            document_id = int(data.get('document_id', 0))
            num_cards = int(data.get('num_cards', 5))

            # Validate document exists
            doc = Document.query.get(document_id)
            if not doc:
                return jsonify({'error': f'Document {document_id} not found'}), 404

            if app.ai_agent is None:
                return jsonify({'error': 'AI service unavailable'}), 503

            # Load settings for audience level
            settings = Settings.query.first() or Settings()
            audience_level = settings.audience_level or 'intermediate'

            # Get document context from ChromaDB (use full document if no embeddings)
            context = ""
            if app.embeddings_service:
                try:
                    context = app.embeddings_service.retrieve_context(
                        query="key concepts and definitions",
                        doc_id=document_id,
                        top_k=10    # grab more chunks for flashcard generation
                    )
                except Exception as e:
                    logger.warning(f"Could not retrieve context for flashcards: {str(e)}")

            if not context and doc.content_preview:
                context = doc.content_preview

            # Generate flashcards using AI agent
            cards_data = app.ai_agent.generate_flashcards(
                context=context,
                num_cards=num_cards,
                audience_level=audience_level
            )

            # Save flashcards to database
            saved_cards = []
            for card in (cards_data or []):
                flashcard = Flashcard(
                    document_id=document_id,
                    question=card.get('question', ''),
                    answer=card.get('answer', '')
                )
                db.session.add(flashcard)
                saved_cards.append(flashcard)

            db.session.commit()

            # Log usage
            UsageTracker.log_usage(
                model_name=settings.model_choice or 'gemini-2.5-flash',
                tokens_input=0,
                tokens_output=0,
                request_type='generate_flashcards'
            )

            logger.info(f"Generated {len(saved_cards)} flashcards for doc {document_id}")

            return jsonify({
                'success': True,
                'document_id': document_id,
                'flashcards': [
                    {'id': fc.id, 'question': fc.question, 'answer': fc.answer}
                    for fc in saved_cards
                ]
            }), 201

        except Exception as e:
            logger.error(f"Error generating flashcards: {str(e)}")
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/flashcards/<int:doc_id>', methods=['GET'])
    def view_flashcards(doc_id):
        """
        Render the flashcard study page for a document.

        Args:
            doc_id (int): Document ID
        """
        try:
            doc = Document.query.get(doc_id)
            if not doc:
                return render_template('error.html', error='Document not found'), 404

            flashcards = Flashcard.query.filter_by(document_id=doc_id).all()
            return render_template('flashcards.html', document=doc, flashcards=flashcards)

        except Exception as e:
            logger.error(f"Error loading flashcards for doc {doc_id}: {str(e)}")
            return render_template('error.html', error=str(e)), 500

    # -------------------------------------------------------------------------
    # DAY 8-9: Quiz Generator
    # -------------------------------------------------------------------------
    @app.route('/generate-quiz', methods=['POST'])
    def generate_quiz():
        """
        Generate a quiz from a document.

        Request JSON:
            { "document_id": 1, "num_questions": 10 }

        Response JSON:
            { "quiz_id": 1, "title": "...", "questions": [...] }
        """
        try:
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form

            document_id = int(data.get('document_id', 0))
            num_questions = int(data.get('num_questions', 10))

            # Validate document
            doc = Document.query.get(document_id)
            if not doc:
                return jsonify({'error': f'Document {document_id} not found'}), 404

            if app.ai_agent is None:
                return jsonify({'error': 'AI service unavailable'}), 503

            # Load settings
            settings = Settings.query.first() or Settings()
            audience_level = settings.audience_level or 'intermediate'

            # Retrieve context
            context = ""
            if app.embeddings_service:
                try:
                    context = app.embeddings_service.retrieve_context(
                        query="main topics, definitions, and key points",
                        doc_id=document_id,
                        top_k=10
                    )
                except Exception as e:
                    logger.warning(f"Could not retrieve context for quiz: {str(e)}")

            if not context and doc.content_preview:
                context = doc.content_preview

            # Generate quiz questions using AI agent
            questions_data = app.ai_agent.generate_quiz(
                context=context,
                num_questions=num_questions,
                audience_level=audience_level
            )

            # Create Quiz record
            quiz = Quiz(
                document_id=document_id,
                title=f"Quiz: {doc.title}",
                description=f"Auto-generated quiz from {doc.filename}"
            )
            db.session.add(quiz)
            db.session.flush()  # Get quiz.id before committing

            # Save questions
            saved_questions = []
            for q in (questions_data or []):
                question = QuizQuestion(
                    quiz_id=quiz.id,
                    question_text=q.get('question', ''),
                    question_type=q.get('type', 'multiple_choice'),
                    correct_answer=q.get('correct_answer', ''),
                    options=q.get('options', []),
                    explanation=q.get('explanation', '')
                )
                db.session.add(question)
                saved_questions.append(question)

            db.session.commit()

            # Log usage
            UsageTracker.log_usage(
                model_name=settings.model_choice or 'gemini-2.5-flash',
                tokens_input=0,
                tokens_output=0,
                request_type='generate_quiz'
            )

            logger.info(f"Generated quiz {quiz.id} with {len(saved_questions)} questions for doc {document_id}")

            return jsonify({
                'success': True,
                'quiz_id': quiz.id,
                'title': quiz.title,
                'questions': [
                    {
                        'id': q.id,
                        'question': q.question_text,
                        'type': q.question_type,
                        'options': q.options
                    }
                    for q in saved_questions
                ]
            }), 201

        except Exception as e:
            logger.error(f"Error generating quiz: {str(e)}")
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/quiz/<int:quiz_id>', methods=['GET'])
    def view_quiz(quiz_id):
        """
        Render the quiz-taking page.

        Args:
            quiz_id (int): Quiz ID
        """
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return render_template('error.html', error='Quiz not found'), 404

            questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).all()
            return render_template('quiz.html', quiz=quiz, questions=questions)

        except Exception as e:
            logger.error(f"Error loading quiz {quiz_id}: {str(e)}")
            return render_template('error.html', error=str(e)), 500

    @app.route('/submit-answer', methods=['POST'])
    def submit_answer():
        """
        Submit answers for an entire quiz and calculate score.

        Request JSON:
            {
                "quiz_id": 1,
                "answers": { "question_id": "user_answer", ... }
            }

        Response JSON:
            { "result_id": ..., "score": 7, "total": 10, "percentage": 70 }
        """
        try:
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()

            quiz_id = int(data.get('quiz_id', 0))
            user_answers = data.get('answers', {})

            # Validate quiz
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return jsonify({'error': f'Quiz {quiz_id} not found'}), 404

            # Fetch all questions
            questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).all()
            total = len(questions)

            # Score answers (case-insensitive comparison)
            score = 0
            for question in questions:
                q_id_str = str(question.id)
                submitted = str(user_answers.get(q_id_str, '')).strip().lower()
                correct = str(question.correct_answer).strip().lower()
                if submitted == correct:
                    score += 1

            # Save result
            result = QuizResult(
                quiz_id=quiz_id,
                user_answers=user_answers,
                score=score,
                total_questions=total
            )
            db.session.add(result)
            db.session.commit()

            logger.info(f"Quiz {quiz_id} submitted: score={score}/{total}")

            return jsonify({
                'success': True,
                'result_id': result.id,
                'score': score,
                'total': total,
                'percentage': round((score / total * 100) if total > 0 else 0, 1)
            }), 200

        except Exception as e:
            logger.error(f"Error submitting quiz answers: {str(e)}")
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/quiz-results/<int:quiz_id>', methods=['GET'])
    def quiz_results(quiz_id):
        """
        Render the quiz results page.

        Args:
            quiz_id (int): Quiz ID
        """
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return render_template('error.html', error='Quiz not found'), 404

            # Get most recent result for this quiz
            result = QuizResult.query.filter_by(quiz_id=quiz_id)\
                .order_by(QuizResult.created_at.desc()).first()

            questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).all()

            return render_template(
                'quiz_results.html',
                quiz=quiz,
                result=result,
                questions=questions
            )

        except Exception as e:
            logger.error(f"Error loading quiz results for {quiz_id}: {str(e)}")
            return render_template('error.html', error=str(e)), 500

    # -------------------------------------------------------------------------
    # DAY 10: Code Analysis
    # -------------------------------------------------------------------------
    @app.route('/analyze-code/<int:doc_id>', methods=['POST'])
    def analyze_code(doc_id):
        """
        Generate code analysis for an uploaded code file.

        Supported analysis types (from request param 'analysis_type'):
            - review           : Code quality review, bugs, improvements
            - architecture     : High-level design and structure
            - control_flow     : Execution flow and logic paths

        Request JSON:
            { "analysis_type": "review" }   (optional — defaults to all three)

        Response JSON:
            { "analyses": [ { "type": ..., "report": ... }, ... ] }
        """
        try:
            # Validate document
            doc = Document.query.get(doc_id)
            if not doc:
                return jsonify({'error': f'Document {doc_id} not found'}), 404

            if app.ai_agent is None:
                return jsonify({'error': 'AI service unavailable'}), 503

            # Read code text from the file on disk
            try:
                with open(doc.file_path, 'r', encoding='utf-8', errors='replace') as f:
                    code_text = f.read()
            except Exception as e:
                return jsonify({'error': f'Could not read file: {str(e)}'}), 500

            # Load settings
            settings = Settings.query.first() or Settings()
            audience_level = settings.audience_level or 'intermediate'

            # Determine which analysis type(s) to run
            if request.is_json:
                data = request.get_json() or {}
            else:
                data = request.form

            requested_type = data.get('analysis_type', 'all')

            analysis_types = ['review', 'architecture', 'control_flow'] \
                if requested_type == 'all' else [requested_type]

            analyses = []
            for a_type in analysis_types:
                try:
                    if a_type == 'review':
                        report = app.ai_agent.review_code(code_text, audience_level)
                    elif a_type == 'architecture':
                        report = app.ai_agent.analyze_architecture(code_text)
                    elif a_type == 'control_flow':
                        report = app.ai_agent.analyze_control_flow(code_text)
                    else:
                        logger.warning(f"Unknown analysis type: {a_type}")
                        continue

                    # Save analysis result to database
                    analysis_record = CodeAnalysis(
                        document_id=doc_id,
                        analysis_type=a_type,
                        report_text=report or ''
                    )
                    db.session.add(analysis_record)
                    analyses.append({'type': a_type, 'report': report})

                except Exception as e:
                    logger.error(f"Error running {a_type} analysis: {str(e)}")
                    analyses.append({'type': a_type, 'error': str(e)})

            db.session.commit()

            # Log usage
            UsageTracker.log_usage(
                model_name=settings.model_choice or 'gemini-2.5-flash',
                tokens_input=0,
                tokens_output=0,
                request_type='code_analysis'
            )

            logger.info(f"Completed {len(analyses)} code analyses for doc {doc_id}")
            return jsonify({'success': True, 'analyses': analyses}), 200

        except Exception as e:
            logger.error(f"Error in analyze_code for doc {doc_id}: {str(e)}")
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # -------------------------------------------------------------------------
    # Error handlers
    # -------------------------------------------------------------------------
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
