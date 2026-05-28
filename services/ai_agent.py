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
import json
import logging
import re
from typing import Dict, Generator

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
        if not api_key:
            raise ValueError("Google api key is missing")
        
        # Initialize the genai client with API key
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self._disabled = False
        logger.info(f"AI Agent initialized with model: {model_name}")
    
    def generate_response(
        self,
        query: str,
        context: str,
        conversation_history: str = "",
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 1000,
        audience_level: str = "intermediate",
        tone: str = "friendly"
    ) -> Generator[str, None, None]:
        """
        Generate a streaming response to a query using provided context.
        
        This method:
        1. Builds a system prompt based on audience and tone
        2. Calls Google Gemini API with stream=True
        3. Yields text chunks as they arrive
        
        Args:
            query (str): User's question
            context (str): Retrieved document chunks (from ChromaDB)
            conversation_history (str): Recent chat turns for continuity
            temperature (float): Creativity level (0.0-2.0). Higher = more creative. Default 0.7
            top_p (float): Diversity (0.0-1.0). Controls response variety. Default 0.9
            max_tokens (int): Maximum response length. Default 1000
            audience_level (str): beginner, intermediate, or expert
            tone (str): formal, casual, technical, or friendly
            
        Yields:
            str: Text chunks from the response
            
        TODO: Add retry logic for failed requests
        TODO: Add safety checks (content filtering)
        TODO: Handle context that exceeds token limits
        """
        if self._disabled:
            yield from self._yield_chunks(
                self._fallback_response(query, context, conversation_history, audience_level, tone)
            )
            return

        try:
            # Step 1: Build the system prompt based on settings
            system_prompt = self._build_system_prompt(audience_level, tone)
            logger.info(f"Built system prompt for audience={audience_level}, tone={tone}")
            
            conversation_block = conversation_history.strip() or "No previous turns yet."

            # Step 2: Build the full message (system + history + context + question)
            full_message = f"""{system_prompt}

CONVERSATION SO FAR:
{conversation_block}

CONTEXT (from document):
{context}

QUESTION:
{query}

Answer in a friendly, conversational way. Use the document context as the primary source, but keep continuity with the earlier conversation when it helps. If the context does not support the answer, say so clearly and briefly."""
            
            # Step 3: Call Google Gemini API 
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_message,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    top_p=top_p,
                    max_output_tokens=max_tokens,
                ),
            )
            
            # Step 5: Return the response text as a generator
            if hasattr(response, 'text'):
                text = response.text
                if text:
                    for start in range(0, len(text), 160):
                        yield text[start:start + 160]
                else:
                    yield from self._yield_chunks(self._fallback_response(query, context, conversation_history, audience_level, tone))
            else:
                yield from self._yield_chunks(self._fallback_response(query, context, conversation_history, audience_level, tone))
                    
            logger.info("Response generation completed")
            
        except Exception as e:
            if self._is_fatal_auth_error(e):
                self._disabled = True
                logger.warning(f"AI provider disabled after auth failure: {str(e)}")
            else:
                logger.error(f"Error generating response: {str(e)}")
            yield from self._yield_chunks(
                self._fallback_response(query, context, conversation_history, audience_level, tone)
            )
    
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
        
        return (
            "You are a helpful, friendly, conversational AI assistant. "
            f"{audience_instruction} {tone_instruction} "
            "Keep replies grounded in the provided document and keep the thread of the conversation intact."
        )

    @staticmethod
    def _yield_chunks(text: str, chunk_size: int = 160) -> Generator[str, None, None]:
        """Yield text in small chunks so the UI can update progressively."""
        if not text:
            return

        for start in range(0, len(text), chunk_size):
            yield text[start:start + chunk_size]

    @staticmethod
    def _fallback_response(
        query: str,
        context: str,
        conversation_history: str,
        audience_level: str,
        tone: str,
    ) -> str:
        """Build a local fallback response so chat still works if the API is unavailable."""
        intro_map = {
            "formal": "Here is a concise answer based on the document.",
            "casual": "Here’s the short version.",
            "technical": "Here is a technical summary from the available context.",
            "friendly": "Here’s what I can tell you from the document.",
        }
        intro = intro_map.get(tone, intro_map["friendly"])

        context_text = (context or "").strip()
        if context_text:
            snippet = context_text[:600].rstrip()
            if len(context_text) > 600:
                snippet += "..."
            answer = f"{intro} {snippet}"
        else:
            answer = (
                f"{intro} I could not find matching document context for that question, "
                "but I can still help if you rephrase it or ask about another part of the document."
            )

        if conversation_history.strip():
            answer += " I am keeping the earlier part of our conversation in mind so the thread stays connected."

        answer += " If you want, send a follow-up and I will continue from here."
        return answer

    @staticmethod
    def _is_fatal_auth_error(error: Exception) -> bool:
        """Detect provider auth failures that should switch the agent to fallback mode."""
        message = str(error).lower()
        return 'api_key_invalid' in message or 'api key expired' in message or 'invalid api key' in message
    
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
        
        Args:
            context (str): Document text to generate cards from
            num_cards (int): Number of cards to generate
            audience_level (str): Target audience
            
        Returns:
            list: Validated flashcard dictionaries with 'question' and 'answer' keys
        """
        prompt = f"""You are an expert tutor. Create exactly {num_cards} flashcards using ONLY the document context below.
Audience level: {audience_level}.

Requirements:
- Return a JSON array only, no extra text or markdown fences.
- Each array item must be an object with keys: "question" and "answer".
- Keep each answer concise (1-3 short sentences).

DOCUMENT:
{context}"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    top_p=0.9,
                    max_output_tokens=2000,
                ),
            )

            # Extract text from response
            raw = response.text.strip() if hasattr(response, 'text') else ""
            
            if not raw:
                raise ValueError("Empty response from model")

            # Remove accidental markdown fences the model may include
            raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
            raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE)

            cards = json.loads(raw)
            if not isinstance(cards, list):
                raise ValueError("Expected a JSON array of flashcards")

            validated = []
            for item in cards:
                if not isinstance(item, dict):
                    continue
                q = item.get('question') or item.get('q')
                a = item.get('answer') or item.get('a')
                if not q or not a:
                    continue
                validated.append({
                    'question': str(q).strip(),
                    'answer': str(a).strip()
                })

            if not validated:
                raise ValueError("No valid flashcards found in model output")

            return validated

        except Exception as e:
            logger.error(f"Error generating flashcards: {str(e)}")
            return [{"question": "Could not generate flashcards.", "answer": str(e)}]
    
    def generate_quiz(
        self,
        context: str,
        num_questions: int = 10,
        audience_level: str = "intermediate"
    ):
        """
        Generate quiz questions from document context.
        
        Args:
            context (str): Document text to generate questions from
            num_questions (int): Number of questions to generate
            audience_level (str): Target audience
            
        Returns:
            list: Validated quiz question dictionaries with required keys for database storage
        """
        prompt = f"""You are an expert instructor. Create exactly {num_questions} quiz questions using ONLY the document context below.
Audience level: {audience_level}.

Output requirements:
- Return ONLY a JSON array (no explanation, no markdown fences).
- Each item must be an object with:
  - "question": string (the question text)
  - "options": array of strings (2-5 answer options)
  - "correct_index": integer (0-based index of correct answer in options array)
  - "explanation": string (brief explanation of why this answer is correct)
- Keep questions and each answer <= 2 short sentences.

DOCUMENT:
{context}"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    top_p=0.9,
                    max_output_tokens=2000,
                ),
            )

            # Extract text from response
            raw = response.text.strip() if hasattr(response, 'text') else ""
            
            if not raw:
                raise ValueError("Empty response from model")

            # Remove accidental markdown fences
            raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
            raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE)

            questions = json.loads(raw)
            if not isinstance(questions, list):
                raise ValueError("Expected a JSON array of quiz questions")

            validated = []
            for idx, item in enumerate(questions):
                if not isinstance(item, dict):
                    continue

                q = item.get('question') or item.get('q')
                opts = item.get('options') or item.get('answers') or item.get('choices')
                corr = item.get('correct_index')
                expl = item.get('explanation', '')

                if not q or not isinstance(opts, list) or len(opts) < 2:
                    continue

                # normalize options to strings
                opts_norm = [str(x).strip() for x in opts if x and str(x).strip()]
                if len(opts_norm) < 2:
                    continue

                # normalize correct index if present and valid
                correct_index = None
                correct_answer = ''
                try:
                    if corr is not None:
                        ci = int(corr)
                        if 0 <= ci < len(opts_norm):
                            correct_index = ci
                            correct_answer = opts_norm[ci]
                except Exception:
                    correct_index = None

                validated.append({
                    'question': str(q).strip(),
                    'type': 'multiple_choice',
                    'options': opts_norm,
                    'correct_answer': correct_answer,
                    'explanation': str(expl).strip() if expl else ''
                })

            if not validated:
                raise ValueError("No valid quiz questions found in model output")

            return validated

        except Exception as e:
            logger.error(f"Error generating quiz: {str(e)}")
            return [{"question": "Could not generate the quiz.", "type": "multiple_choice", "options": [str(e)], "correct_answer": "", "explanation": ""}]
        
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
        prompt = f"""
You are a senior software developer. Review the provided code and produce a concise, actionable review.
Audience level: {audience_level}.

Tasks:
- List bugs with file/line references and impact, sorted by severity.
- List missing edge cases and inputs not handled.
- Suggest improvements for performance, readability, and best practices with minimal code fixes.

Output requirements:
- Return ONLY valid JSON (no explanations, no markdown fences).
- JSON object schema: {"issues": [{{"id","severity","lines","title","description","fix"}}], "summary": "short text"}.

Base findings ONLY on the provided code.

CODE:
{code_text}
"""

        try:
            ai_resp = self.generate_response(
                prompt,
                code_text,
                temperature=0.2,
                top_p=0.3,
                max_tokens=2000,
                audience_level=audience_level,
            )

            # Consume the generator to get the full response
            raw = ""
            if isinstance(ai_resp, dict):
                raw = ai_resp.get('text', '')
            else:
                for chunk in ai_resp:
                    raw += chunk
            raw = raw.strip()

            # Remove accidental markdown fences
            raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
            raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE)

            try:
                parsed = json.loads(raw)
                return parsed
            except Exception:
                # If model didn't return JSON, return raw text under a key
                return {"report": raw}

        except Exception as e:
            logger.error(f"Error generating code review: {str(e)}")
            return {"error": str(e), "report": ""}
    
    def analyze_architecture(self, code_text: str, focus: str = None) -> Dict:
        """
        Generate architecture analysis for uploaded code.
        
        PHASE 2 TODO: Implement this function
        
        Args:
            code_text (str): Source code to analyze
            
        Returns:
            str: Architecture analysis report
        """
        prompt = f"""
You are a senior software architect. Analyze the system architecture in the provided code.
Audience: intermediate.

Focus: {focus or 'overall architecture and components'}.

Tasks:
- Identify top-level components/modules and their responsibilities.
- Describe data flow between components (inputs, outputs, major data structures).
- Describe control flow for critical paths (request handling, main algorithms).
- Note external dependencies, integration points, and likely runtime assumptions.
- Call out potential bottlenecks, concurrency concerns, and scaling notes.
- Provide a short list of prioritized recommendations (refactors, tests, observability).

Output requirements:
- Return ONLY valid JSON (no explanation, no markdown fences).
- JSON schema: {"components": [{"name","responsibility","interfaces"}], "data_flow": "short text", "control_flow": "short text", "dependencies": [], "assumptions": [], "recommendations": [], "summary": "short text"}

CODE:
{code_text}
"""

        try:
            ai_resp = self.generate_response(
                prompt,
                code_text,
                temperature=0.2,
                top_p=0.3,
                max_tokens=2000,
                audience_level='intermediate',
            )

            raw = (ai_resp.get('text') if isinstance(ai_resp, dict) else str(ai_resp)) or ""
            raw = raw.strip()

            # Remove accidental markdown fences
            raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
            raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE)

            try:
                parsed = json.loads(raw)
                return parsed
            except Exception:
                return {"report": raw}

        except Exception as e:
            logger.error(f"Error generating architecture analysis: {str(e)}")
            return {"error": str(e), "report": ""}
    
    def analyze_control_flow(self, code_text: str) -> Dict:
        """
        Generate control flow analysis for uploaded code.
        
        PHASE 2 TODO: Implement this function
        
        Args:
            code_text (str): Source code to analyze
            
        Returns:
            str: Control flow analysis report
        """
        # Delegate to analyze_architecture with a control-flow focus to avoid
        # duplicated functionality while preserving the public API.
        try:
            return self.analyze_architecture(code_text, focus='control_flow')
        except Exception as e:
            logger.error(f"Error running control flow analysis: {str(e)}")
            return {"error": str(e), "report": ""}

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
    response=agent.generate_response("What is python?","Python is a backend language")
    print(f"response: {response}")