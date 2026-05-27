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
            # Step 1: Parse request — support both JSON body and form data
            if request.is_json:
                data = request.get_json()
                query = data.get('query', '').strip()
                document_id = data.get('document_id')
            else:
                query = request.form.get('query', '').strip()
                document_id = request.form.get('document_id')

            # Validate inputs
            if not query:
                return jsonify({'error': 'Query is required'}), 400
            if not document_id:
                return jsonify({'error': 'document_id is required'}), 400

            document_id = int(document_id)

            # Step 2: Load settings from database
            settings = Settings.query.first()
            if settings is None:
                # Fall back to defaults if no settings row exists yet
                settings = Settings()

            temperature = settings.temperature or 0.7
            top_p = settings.top_p or 0.9
            audience_level = settings.audience_level or 'intermediate'
            tone = settings.tone or 'friendly'
            max_tokens = settings.max_tokens_per_response or 1000

            # Step 3: Retrieve relevant context chunks from ChromaDB
            context = ""
            if app.embeddings_service:
                try:
                    context = app.embeddings_service.retrieve_context(
                        query=query,
                        doc_id=document_id,
                        top_k=3
                    )
                    logger.info(f"Retrieved context: {len(context)} characters for doc {document_id}")
                except Exception as e:
                    logger.warning(f"Could not retrieve context for doc {document_id}: {str(e)}")
                    # Fall back to empty context — AI will note it has no context
            else:
                logger.warning("Embeddings service unavailable; proceeding without context")

            # Step 4: Generate AI response
            if app.ai_agent is None:
                return jsonify({'error': 'AI service is not available. Check your GOOGLE_API_KEY.'}), 503

            result = app.ai_agent.generate_response(
                query=query,
                context=context,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                audience_level=audience_level,
                tone=tone
            )

            response_text = result.get('text', '')
            tokens_input = result.get('tokens_input', 0)
            tokens_output = result.get('tokens_output', 0)
            tokens_total = result.get('tokens_total', 0)

            # Step 5: Save ChatMessage to database
            chat_message = ChatMessage(
                document_id=document_id,
                query=query,
                response=response_text,
                tokens_used=tokens_total,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                temperature=temperature,
                top_p=top_p
            )
            db.session.add(chat_message)
            db.session.commit()
            logger.info(f"Saved ChatMessage {chat_message.id} for doc {document_id}")

            # Step 6: Log usage with UsageTracker
            UsageTracker.log_usage(
                model_name=settings.model_choice or 'gemini-2.5-flash',
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                request_type='chat'
            )

            # Step 7: Return JSON response
            return jsonify({
                'response': response_text,
                'tokens_used': tokens_total,
                'tokens_input': tokens_input,
                'tokens_output': tokens_output,
                'message_id': chat_message.id
            }), 200

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
            # Parse request — support form data (from settings_panel.html)
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form

            # Step 1: Get or create the single Settings row (id=1)
            settings = Settings.query.first()
            if settings is None:
                settings = Settings()
                db.session.add(settings)

            # Step 2: Extract and validate temperature (0.0 – 2.0)
            if 'temperature' in data:
                try:
                    temperature = float(data['temperature'])
                    temperature = max(0.0, min(2.0, temperature))   # clamp
                    settings.temperature = temperature
                except (ValueError, TypeError):
                    logger.warning(f"Invalid temperature value: {data['temperature']}")

            # Step 3: Extract and validate top_p (0.0 – 1.0)
            if 'top_p' in data:
                try:
                    top_p = float(data['top_p'])
                    top_p = max(0.0, min(1.0, top_p))              # clamp
                    settings.top_p = top_p
                except (ValueError, TypeError):
                    logger.warning(f"Invalid top_p value: {data['top_p']}")

            # Step 4: Audience level
            valid_audience = {'beginner', 'intermediate', 'expert'}
            if 'audience_level' in data and data['audience_level'] in valid_audience:
                settings.audience_level = data['audience_level']

            # Step 5: Tone
            valid_tones = {'formal', 'casual', 'technical', 'friendly'}
            if 'tone' in data and data['tone'] in valid_tones:
                settings.tone = data['tone']

            # Step 6: Max tokens (100 – 4000)
            if 'max_tokens_per_response' in data:
                try:
                    max_tokens = int(data['max_tokens_per_response'])
                    max_tokens = max(100, min(4000, max_tokens))    # clamp
                    settings.max_tokens_per_response = max_tokens
                except (ValueError, TypeError):
                    logger.warning(f"Invalid max_tokens value: {data['max_tokens_per_response']}")

            # Step 7: Save
            db.session.commit()
            logger.info(f"Settings updated: temp={settings.temperature}, top_p={settings.top_p}, "
                        f"audience={settings.audience_level}, tone={settings.tone}")

            # Return JSON if client asked for it, otherwise redirect
            if request.is_json:
                return jsonify({'success': True, 'settings': settings.to_dict()}), 200

            return redirect(url_for('dashboard'))

        except Exception as e:
            logger.error(f"Error updating settings: {str(e)}")
            db.session.rollback()
            if request.is_json:
                return jsonify({'error': str(e)}), 500
            return redirect(url_for('dashboard'))

    @app.route('/get-usage-stats', methods=['GET'])
    def get_usage_stats():
        """
        Return current usage statistics as JSON.

        Response JSON:
            {
                "total_requests": int,
                "total_tokens_input": int,
                "total_tokens_output": int,
                "total_tokens": int,
                "avg_tokens_per_request": int
            }

        Used by the usage dashboard to refresh numbers without a full page reload.
        """
        try:
            stats = UsageTracker.get_total_usage()
            recent = UsageTracker.get_recent_usage(limit=5)

            recent_list = [
                {
                    'model': log.model_name,
                    'request_type': log.request_type,
                    'tokens_input': log.tokens_input,
                    'tokens_output': log.tokens_output,
                    'created_at': log.created_at.isoformat()
                }
                for log in recent
            ]

            return jsonify({
                **stats,
                'recent': recent_list
            }), 200

        except Exception as e:
            logger.error(f"Error fetching usage stats: {str(e)}")
            return jsonify({'error': str(e)}), 500

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
