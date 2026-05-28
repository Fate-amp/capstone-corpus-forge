"""
Database models for Corpus Forge application.

Defines SQLAlchemy ORM models for:
- Document: uploaded files and their metadata
- ChatMessage: conversation history
- UsageLog: token and request tracking
- Settings: user preferences
- Flashcard: study cards (Phase 2)
- Quiz: quizzes (Phase 2)

TODO: Add database indexes for query performance
TODO: Add validation constraints (e.g., max file size in DB schema)
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, JSON
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy ORM
db = SQLAlchemy()


class Document(db.Model):
    """
    Represents an uploaded document (PDF, TXT, or code file).
    
    Attributes:
        id: Primary key
        filename: Original filename (e.g., 'research_paper.pdf')
        title: User-friendly document title
        content_preview: First 500 characters of extracted text (for display)
        file_path: Path to uploaded file (relative to UPLOAD_FOLDER)
        file_type: Document type (pdf, txt, code)
        created_at: Timestamp when document was uploaded
        updated_at: Timestamp of last modification
        
    TODO: Add document_hash to detect duplicate uploads
    TODO: Add file_size field to track storage usage
    TODO: Add tags/categories for document organization
    """
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    content_preview = Column(Text, nullable=True)
    full_content = Column(Text, nullable=True)  # Store full extracted text for quick retrieval
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)  # 'pdf', 'txt', 'py', 'js', etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    chat_messages = db.relationship('ChatMessage', backref='document', cascade='all, delete-orphan')
    flashcards = db.relationship('Flashcard', backref='document', cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='document', cascade='all, delete-orphan')
    code_analyses = db.relationship('CodeAnalysis', backref='document', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Document {self.id}: {self.filename}>'
    
    def to_dict(self):
        """
        Convert document to dictionary for JSON serialization.
        
        TODO: Add file_size, storage_used to response
        """
        return {
            'id': self.id,
            'filename': self.filename,
            'title': self.title,
            'content_preview': self.content_preview[:100] + '...' if self.content_preview else '',
            'file_type': self.file_type,
            'created_at': self.created_at.isoformat(),
        }


class ChatMessage(db.Model):
    """
    Represents a chat message (query + AI response) for a document.
    
    Attributes:
        id: Primary key
        document_id: Foreign key to Document
        query: User's question
        response: AI-generated answer
        tokens_used: Total tokens consumed (input + output)
        tokens_input: Tokens in the query + context
        tokens_output: Tokens in the response
        temperature: Temperature parameter used for this response
        top_p: Top-p parameter used for this response
        created_at: When the message was created
        
    TODO: Add response_quality rating (1-5) for prompt optimization analysis
    TODO: Add user_feedback field (was this response helpful?)
    TODO: Add retrieved_chunks to track which document chunks were used
    """
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, db.ForeignKey('documents.id'), nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    tokens_used = Column(Integer, default=0)
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    temperature = Column(Float, default=0.7)
    top_p = Column(Float, default=0.9)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<ChatMessage {self.id}: tokens={self.tokens_used}>'
    
    def to_dict(self):
        """Convert chat message to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'query': self.query,
            'response': self.response,
            'tokens_used': self.tokens_used,
            'created_at': self.created_at.isoformat(),
        }


class UsageLog(db.Model):
    """
    Logs AI API usage for tracking and analytics.
    
    Attributes:
        id: Primary key
        model_name: Name of AI model used (e.g., 'gemini-pro')
        tokens_input: Tokens used in prompt
        tokens_output: Tokens in response
        request_count: Number of requests in this log entry
        request_type: Type of request (chat, generate, embed, review, etc.)
        created_at: Timestamp
        
    TODO: Add cost tracking (tokens × cost_per_token)
    TODO: Add request_latency to track performance
    TODO: Add error_count to track API failures
    TODO: Add daily aggregation table for dashboard display
    """
    __tablename__ = 'usage_logs'
    
    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), default='gemini-pro', nullable=False)
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    request_count = Column(Integer, default=1)
    request_type = Column(String(50), nullable=False)  # 'chat', 'generate', 'embed', etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<UsageLog {self.id}: {self.tokens_input + self.tokens_output} tokens>'


class Settings(db.Model):
    """
    User settings and preferences for AI interaction.
    
    Attributes:
        id: Primary key (only one row expected)
        temperature: Creativity level (0.0-2.0, default 0.7)
        top_p: Diversity of responses (0.0-1.0, default 0.9)
        audience_level: Target audience (beginner, intermediate, expert)
        tone: Response tone (formal, casual, technical, friendly)
        model_choice: Which AI model to use
        max_tokens_per_response: Cap on response length
        system_prompt_override: Custom system instruction (if provided)
        
    TODO: Add per-document settings (different audience for different docs)
    TODO: Add response_format preference (bullet points, paragraphs, code, etc.)
    TODO: Add language preference
    """
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True, default=1)
    temperature = Column(Float, default=0.7)
    top_p = Column(Float, default=0.9)
    audience_level = Column(String(50), default='intermediate')  # beginner, intermediate, expert
    tone = Column(String(50), default='friendly')  # formal, casual, technical, friendly
    model_choice = Column(String(100), default='gemini-2.5-flash')
    max_tokens_per_response = Column(Integer, default=1000)
    system_prompt_override = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert settings to dictionary for JSON serialization."""
        return {
            'temperature': self.temperature,
            'top_p': self.top_p,
            'audience_level': self.audience_level,
            'tone': self.tone,
            'model_choice': self.model_choice,
            'max_tokens_per_response': self.max_tokens_per_response,
        }


# ============================================================================
# PHASE 2 MODELS (Implement in Days 6-11)
# ============================================================================

class Flashcard(db.Model):
    """
    Represents a single flashcard (question + answer) for studying.
    
    Attributes:
        id: Primary key
        document_id: Foreign key to Document
        question: The question/prompt side
        answer: The answer/explanation side
        review_count: Number of times reviewed (for spaced repetition)
        correct_count: Number of times answered correctly
        created_at: When flashcard was generated
        
    TODO: Add difficulty_rating (auto-calculated based on review_count vs correct_count)
    TODO: Add tags for organizing flashcards
    TODO: Add source_chunks to trace back to document chunks used to generate this card
    """
    __tablename__ = 'flashcards'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, db.ForeignKey('documents.id'), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    review_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Flashcard {self.id}>'


class Quiz(db.Model):
    """
    Represents a quiz (collection of questions) for a document.
    
    Attributes:
        id: Primary key
        document_id: Foreign key to Document
        title: Quiz title
        description: Quiz description
        created_at: When quiz was generated
        
    TODO: Add quiz_type (diagnostic, reinforcement, assessment)
    TODO: Add difficulty_level (easy, medium, hard)
    TODO: Add passing_score (threshold for success)
    """
    __tablename__ = 'quizzes'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, db.ForeignKey('documents.id'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    questions = db.relationship('QuizQuestion', backref='quiz', cascade='all, delete-orphan')
    results = db.relationship('QuizResult', backref='quiz', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Quiz {self.id}: {self.title}>'


class QuizQuestion(db.Model):
    """
    Represents a single question in a quiz.
    
    Attributes:
        id: Primary key
        quiz_id: Foreign key to Quiz
        question_text: The question text
        question_type: Type of question ('multiple_choice' or 'short_answer')
        correct_answer: The correct answer
        options: JSON array of options (for multiple choice)
        explanation: Explanation of the correct answer
        
    TODO: Add difficulty_score (how many users got this wrong)
    TODO: Add source_chunks to track document chunks used to generate question
    """
    __tablename__ = 'quiz_questions'
    
    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)  # 'multiple_choice' or 'short_answer'
    correct_answer = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)  # For multiple choice: ['A', 'B', 'C', 'D']
    explanation = Column(Text, nullable=True)
    
    def __repr__(self):
        return f'<QuizQuestion {self.id}>'


class QuizResult(db.Model):
    """
    Tracks user's quiz attempt and score.
    
    Attributes:
        id: Primary key
        quiz_id: Foreign key to Quiz
        user_answers: JSON mapping of question_id -> user_answer
        score: Number of correct answers
        total_questions: Total questions in quiz
        created_at: When quiz was taken
        
    TODO: Add attempt_number (which attempt is this)
    TODO: Add time_spent (how long user spent on quiz)
    TODO: Add detailed_results (breakdown by topic/question_type)
    """
    __tablename__ = 'quiz_results'
    
    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, db.ForeignKey('quizzes.id'), nullable=False)
    user_answers = Column(JSON, nullable=False)
    score = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<QuizResult {self.id}: score={self.score}/{self.total_questions}>'


class CodeAnalysis(db.Model):
    """
    Stores AI-generated code analysis reports.
    
    Attributes:
        id: Primary key
        document_id: Foreign key to Document (must be code file)
        analysis_type: Type of analysis ('review', 'architecture', 'control_flow')
        report_text: Full analysis report
        created_at: When analysis was generated
        
    TODO: Add issues_found (structured data of identified problems)
    TODO: Add severity_levels (critical, high, medium, low)
    TODO: Add suggestions (actionable improvements)
    TODO: Add metrics (code complexity, function count, etc.)
    """
    __tablename__ = 'code_analyses'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, db.ForeignKey('documents.id'), nullable=False)
    analysis_type = Column(String(50), nullable=False)  # 'review', 'architecture', 'control_flow'
    report_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<CodeAnalysis {self.id}: {self.analysis_type}>'
