"""
AI Agent service module.

Handles interaction with Google GenAI API for generating responses.

Uses the Google Generative AI library to generate responses based on context.
Supports streaming responses for real-time display.

TODO: Add retry logic for API failures
TODO: Add rate limiting to prevent quota exhaustion
TODO: Add caching for repeated queries
TODO: Add structured output parsing
"""

from google import genai
from google.genai import types
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class AIAgent:
    """
    Orchestrates interaction with Google GenAI API.
    
    Handles:
    - Model initialization
    - Response generation with streaming
    - Token counting
    - Parameter management
    
    TODO: Add support for multiple models
    TODO: Add fallback strategies if primary model fails
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """
        Initialize the AI Agent.
        
        Args:
            api_key (str): Google GenAI API key
            model_name (str): Model to use (default: gemini-2.5-flash)
            
        TODO: Validate API key on initialization
        TODO: Test model availability
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        logger.info(f"AI Agent initialized with model: {model_name}")
    
    def generate_response(
        self,
        query: str,
        context: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 1000,
        audience_level: str = "intermediate",
        tone: str = "friendly"
    ) -> dict:
        """
        Generate a response to a query using provided context.
        
        This method:
        1. Builds a system prompt based on audience and tone
        2. Calls Google Gemini API with the full message
        3. Returns the full response with token counts
        
        Args:
            query (str): User's question
            context (str): Retrieved document chunks (from ChromaDB)
            temperature (float): Creativity level (0.0-2.0). Higher = more creative. Default 0.7
            top_p (float): Diversity (0.0-1.0). Controls response variety. Default 0.9
            max_tokens (int): Maximum response length. Default 1000
            audience_level (str): beginner, intermediate, or expert
            tone (str): formal, casual, technical, or friendly
            
        Returns:
            dict: {
                'text': str - The AI response,
                'tokens_input': int - Tokens in the input message,
                'tokens_output': int - Tokens in the response,
                'tokens_total': int - Sum of input + output
            }
            
        Raises:
            Exception: If API call fails
            
        TODO: Add retry logic for failed requests
        TODO: Add safety checks (content filtering)
        TODO: Handle context that exceeds token limits
        """
        try:
            # Step 1: Build the system prompt based on settings
            system_prompt = self._build_system_prompt(audience_level, tone)
            logger.info(f"Built system prompt for audience={audience_level}, tone={tone}")
            
            # Step 2: Build the full message (system + context + question)
            full_message = f"""{system_prompt}

CONTEXT (from document):
{context}

QUESTION:
{query}

Please answer the question using ONLY the context provided above. If the answer is not in the context, say so."""
            
            # Step 3: Count input tokens (before calling API)
            tokens_input = self._count_tokens(full_message)
            logger.info(f"Input message: {tokens_input} tokens")
            
            # Step 4: Call Google Gemini API using the new genai.Client API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_message,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    top_p=top_p,
                    max_output_tokens=max_tokens,
                )
            )
            
            # Step 5: Extract response text
            response_text = response.text
            logger.info(f"Received response: {len(response_text)} characters")
            
            # Step 6: Count output tokens
            tokens_output = self._count_tokens(response_text)
            logger.info(f"Output message: {tokens_output} tokens")
            
            # Step 7: Return response with metadata
            return {
                'text': response_text,
                'tokens_input': tokens_input,
                'tokens_output': tokens_output,
                'tokens_total': tokens_input + tokens_output
            }
        
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                'text': f"Error: {str(e)}",
                'tokens_input': 0,
                'tokens_output': 0,
                'tokens_total': 0
            }
    
    def _build_system_prompt(self, audience_level: str, tone: str) -> str:
        """
        Build a system prompt based on audience and tone preferences.
        
        Args:
            audience_level (str): beginner, intermediate, or expert
            tone (str): formal, casual, technical, or friendly
            
        Returns:
            str: System prompt instruction
            
        TODO: Store prompt templates in config
        TODO: Allow custom system prompt override
        TODO: Add more audience levels and tones
        """
        audience_hints = {
            'beginner': "Explain concepts simply, avoid jargon. Use analogies and examples.",
            'intermediate': "Assume moderate knowledge. Balance clarity with technical depth.",
            'expert': "Use technical terminology. Assume deep domain knowledge.",
        }
        
        tone_hints = {
            'formal': "Use formal, professional language.",
            'casual': "Use conversational, friendly language.",
            'technical': "Use technical terminology and precision.",
            'friendly': "Be warm and encouraging.",
        }
        
        audience_instruction = audience_hints.get(audience_level, audience_hints['intermediate'])
        tone_instruction = tone_hints.get(tone, tone_hints['friendly'])
        
        return f"You are a helpful AI assistant. {audience_instruction} {tone_instruction}"
    
    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text using Google GenAI API.
        
        Args:
            text (str): Text to count tokens for
            
        Returns:
            int: Number of tokens
            
        TODO: Add error handling for token counting API
        TODO: Cache token counts for repeated text
        """
        try:
            response = self.client.models.count_tokens(
                model=self.model_name,
                contents=text
            )
            return response.total_tokens
        except Exception as e:
            logger.error(f"Error counting tokens: {str(e)}")
            # Estimate: ~4 characters per token
            return len(text) // 4
    
    def generate_flashcards(
        self,
        context: str,
        num_cards: int = 5,
        audience_level: str = "intermediate"
    ):
        """
        Generate flashcard QA pairs from document context.
        
        PHASE 2 TODO: Implement this function
        
        Args:
            context (str): Document text to generate cards from
            num_cards (int): Number of cards to generate
            audience_level (str): Target audience
            
        Yields:
            str: JSON-formatted QA pairs
        """
        pass
    
    def generate_quiz(
        self,
        context: str,
        num_questions: int = 10,
        audience_level: str = "intermediate"
    ):
        """
        Generate quiz questions from document context.
        
        PHASE 2 TODO: Implement this function
        
        Args:
            context (str): Document text to generate questions from
            num_questions (int): Number of questions to generate
            audience_level (str): Target audience
            
        Yields:
            str: JSON-formatted quiz questions with MC options
        """
        pass
    
    def review_code(self, code_text: str, audience_level: str = "intermediate") -> str:
        """
        Generate code review report for uploaded code.
        
        PHASE 2 TODO: Implement this function
        
        Args:
            code_text (str): Source code to review
            audience_level (str): Target audience
            
        Returns:
            str: Code review report
        """
        pass
    
    def analyze_architecture(self, code_text: str) -> str:
        """
        Generate architecture analysis for uploaded code.
        
        PHASE 2 TODO: Implement this function
        
        Args:
            code_text (str): Source code to analyze
            
        Returns:
            str: Architecture analysis report
        """
        pass
    
    def analyze_control_flow(self, code_text: str) -> str:
        """
        Generate control flow analysis for uploaded code.
        
        PHASE 2 TODO: Implement this function
        
        Args:
            code_text (str): Source code to analyze
            
        Returns:
            str: Control flow analysis report
        """
        pass

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Load .env file into environment variables
    load_dotenv()
    
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not set in .env file")
        exit(1)
    agent = AIAgent(api_key)
    print(f"✓ AIAgent initialized with model: {agent.model_name}")