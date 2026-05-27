"""
AI Agent service module.

Handles interaction with Google GenAI API for generating responses.

Uses the Google Generative AI library to generate responses based on context.
Supports streaming responses for real-time display.

PHASE 1:  generate_response() — already implemented by Person B
PHASE 2:  generate_flashcards(), generate_quiz(), review_code(),
          analyze_architecture(), analyze_control_flow() — implemented here
          by Person C.
"""

from google import genai
from google.genai import types
import logging
import json
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


class AIAgent:
    """
    Orchestrates interaction with Google GenAI API.

    Handles:
    - Model initialization
    - Response generation with streaming
    - Token counting
    - Parameter management
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """
        Initialize the AI Agent.

        Args:
            api_key (str): Google GenAI API key
            model_name (str): Model to use (default: gemini-2.5-flash)
        """
        if not api_key:
            raise ValueError("Google api key is missing")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        try:
            self.client.models.generate_content(
                model=self.model_name,
                contents="test"
            )
        except Exception as e:
            raise RuntimeError("Model failed to initialize") from e
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

        Args:
            query (str): User's question
            context (str): Retrieved document chunks (from ChromaDB)
            temperature (float): Creativity level (0.0-2.0)
            top_p (float): Diversity (0.0-1.0)
            max_tokens (int): Maximum response length
            audience_level (str): beginner, intermediate, or expert
            tone (str): formal, casual, technical, or friendly

        Returns:
            dict: {
                'text': str,
                'tokens_input': int,
                'tokens_output': int,
                'tokens_total': int
            }
        """
        try:
            system_prompt = self._build_system_prompt(audience_level, tone)
            logger.info(f"Built system prompt for audience={audience_level}, tone={tone}")

            full_message = f"""{system_prompt}

CONTEXT (from document):
{context}

QUESTION:
{query}

Please answer the question using ONLY the context provided above. If the answer is not in the context, say so."""

            tokens_input = self._count_tokens(full_message)
            logger.info(f"Input message: {tokens_input} tokens")

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_message,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    top_p=top_p,
                    max_output_tokens=max_tokens,
                )
            )

            response_text = response.text
            logger.info(f"Received response: {len(response_text)} characters")

            tokens_output = self._count_tokens(response_text)
            logger.info(f"Output message: {tokens_output} tokens")

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

    # =========================================================================
    # PHASE 2 — Person C's implementations
    # =========================================================================

    def generate_flashcards(
        self,
        context: str,
        num_cards: int = 5,
        audience_level: str = "intermediate"
    ) -> List[dict]:
        """
        Generate flashcard QA pairs from document context.

        Calls Gemini with a strict JSON prompt so we can parse the output
        directly into { question, answer } pairs.

        Args:
            context (str): Document text to generate cards from
            num_cards (int): Number of cards to generate
            audience_level (str): Target audience (beginner/intermediate/expert)

        Returns:
            List[dict]: List of { "question": str, "answer": str } dicts
        """
        audience_hints = {
            'beginner': "Use simple language, short sentences, and avoid technical jargon.",
            'intermediate': "Balance clarity with some technical detail.",
            'expert': "Use precise technical language and assume deep domain knowledge.",
        }
        audience_note = audience_hints.get(audience_level, audience_hints['intermediate'])

        prompt = f"""You are an expert tutor creating study flashcards from the document content below.
{audience_note}

Generate exactly {num_cards} flashcard question-answer pairs that cover the most important concepts.
Each answer should be concise (1-3 sentences).

Return ONLY a valid JSON array. No preamble, no markdown fences, no extra text.
Format:
[
  {{"question": "...", "answer": "..."}},
  ...
]

DOCUMENT CONTENT:
{context}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,    # moderate creativity for flashcards
                    max_output_tokens=2000,
                )
            )

            raw = response.text.strip()
            # Strip any accidental markdown fences
            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)

            cards = json.loads(raw)
            if not isinstance(cards, list):
                raise ValueError("Expected a JSON array of flashcards")

            logger.info(f"Generated {len(cards)} flashcards")
            return cards

        except Exception as e:
            logger.error(f"Error generating flashcards: {str(e)}")
            # Return a minimal fallback so the route doesn't crash
            return [{"question": "Could not generate flashcards.", "answer": str(e)}]

    def generate_quiz(
        self,
        context: str,
        num_questions: int = 10,
        audience_level: str = "intermediate"
    ) -> List[dict]:
        """
        Generate quiz questions from document context.

        Mix of multiple-choice and short-answer questions.
        Returns structured JSON so the route can save them to the DB directly.

        Args:
            context (str): Document text to generate questions from
            num_questions (int): Number of questions to generate
            audience_level (str): Target audience

        Returns:
            List[dict]: Each dict has:
                question (str), type (str), correct_answer (str),
                options (list|None), explanation (str)
        """
        audience_hints = {
            'beginner': "Use simple language. Prefer multiple-choice questions.",
            'intermediate': "Mix of multiple-choice and short-answer questions.",
            'expert': "Use technical, precise questions. Include short-answer questions.",
        }
        audience_note = audience_hints.get(audience_level, audience_hints['intermediate'])

        mc_count = max(1, round(num_questions * 0.7))   # 70% multiple choice
        sa_count = num_questions - mc_count              # 30% short answer

        prompt = f"""You are an expert educator creating a quiz from the document content below.
{audience_note}

Generate {mc_count} multiple-choice questions and {sa_count} short-answer questions.

For multiple-choice:
  - 4 options labelled A, B, C, D
  - correct_answer must be exactly one of: "A", "B", "C", or "D"
  - options is a list of 4 strings (the option text, without the letter prefix)

For short-answer:
  - correct_answer is a concise expected answer (1-2 sentences)
  - options is null

Return ONLY a valid JSON array. No preamble, no markdown fences, no extra text.
Format:
[
  {{
    "question": "...",
    "type": "multiple_choice",
    "correct_answer": "A",
    "options": ["option text", "option text", "option text", "option text"],
    "explanation": "Why the correct answer is correct."
  }},
  {{
    "question": "...",
    "type": "short_answer",
    "correct_answer": "Expected answer text.",
    "options": null,
    "explanation": "Explanation of the concept."
  }}
]

DOCUMENT CONTENT:
{context}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=3000,
                )
            )

            raw = response.text.strip()
            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)

            questions = json.loads(raw)
            if not isinstance(questions, list):
                raise ValueError("Expected a JSON array of questions")

            logger.info(f"Generated {len(questions)} quiz questions")
            return questions

        except Exception as e:
            logger.error(f"Error generating quiz: {str(e)}")
            return [{
                "question": "Could not generate quiz.",
                "type": "short_answer",
                "correct_answer": "N/A",
                "options": None,
                "explanation": str(e)
            }]

    def review_code(self, code_text: str, audience_level: str = "intermediate") -> str:
        """
        Generate a code review report for uploaded code.

        Covers:
        - Bugs / potential errors
        - Code style and readability
        - Performance concerns
        - Security considerations
        - Suggested improvements

        Args:
            code_text (str): Source code to review
            audience_level (str): Determines depth of explanation

        Returns:
            str: Markdown-formatted code review report
        """
        audience_hints = {
            'beginner': "Explain issues in plain language with examples.",
            'intermediate': "Use standard programming terminology.",
            'expert': "Use precise technical language; skip basic explanations.",
        }
        audience_note = audience_hints.get(audience_level, audience_hints['intermediate'])

        prompt = f"""You are a senior software engineer performing a thorough code review.
{audience_note}

Review the code below and produce a well-structured Markdown report covering:

1. **Summary** — What the code does (1-2 sentences)
2. **Bugs & Errors** — Any bugs, edge cases, or runtime errors found
3. **Code Quality** — Readability, naming conventions, structure
4. **Performance** — Any inefficiencies or bottlenecks
5. **Security** — Potential security issues (if applicable)
6. **Suggestions** — Concrete improvements with brief code examples where helpful

CODE TO REVIEW:
```
{code_text[:8000]}
```
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,    # low temperature for factual review
                    max_output_tokens=2000,
                )
            )
            logger.info("Generated code review report")
            return response.text

        except Exception as e:
            logger.error(f"Error generating code review: {str(e)}")
            return f"Error generating code review: {str(e)}"

    def analyze_architecture(self, code_text: str) -> str:
        """
        Generate architecture analysis for uploaded code.

        Covers:
        - High-level structure (modules, classes, functions)
        - Design patterns used
        - Component responsibilities
        - Dependencies and coupling

        Args:
            code_text (str): Source code to analyze

        Returns:
            str: Markdown-formatted architecture analysis
        """
        prompt = f"""You are a software architect analyzing the structure and design of the following code.

Produce a well-structured Markdown report covering:

1. **High-Level Overview** — What this code does and its overall structure
2. **Components & Modules** — Key classes, functions, or modules and their responsibilities
3. **Design Patterns** — Any design patterns identified (e.g., singleton, factory, MVC)
4. **Dependencies** — Internal and external dependencies; tight/loose coupling
5. **Architecture Strengths** — What is well-designed
6. **Architecture Concerns** — Areas of concern (e.g., high coupling, missing abstractions)
7. **Recommendations** — Concrete suggestions to improve the architecture

CODE:
```
{code_text[:8000]}
```
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=2000,
                )
            )
            logger.info("Generated architecture analysis")
            return response.text

        except Exception as e:
            logger.error(f"Error generating architecture analysis: {str(e)}")
            return f"Error generating architecture analysis: {str(e)}"

    def analyze_control_flow(self, code_text: str) -> str:
        """
        Generate control flow analysis for uploaded code.

        Covers:
        - Execution path from entry points
        - Conditional branches and loops
        - Error handling paths
        - Potential dead code or unreachable paths

        Args:
            code_text (str): Source code to analyze

        Returns:
            str: Markdown-formatted control flow analysis
        """
        prompt = f"""You are a software engineer performing a control flow analysis on the following code.

Produce a well-structured Markdown report covering:

1. **Entry Points** — Where execution begins (main function, routes, event handlers)
2. **Key Execution Paths** — The main flow of execution step-by-step
3. **Branches & Conditionals** — Important if/else, switch, or try/except branches
4. **Loops** — Any loops, their purpose, and potential issues (infinite loops, off-by-one)
5. **Error Handling** — How errors and exceptions are handled
6. **Edge Cases** — Potential edge cases or unhandled paths
7. **Dead Code** — Any unreachable or unused code sections

CODE:
```
{code_text[:8000]}
```
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=2000,
                )
            )
            logger.info("Generated control flow analysis")
            return response.text

        except Exception as e:
            logger.error(f"Error generating control flow analysis: {str(e)}")
            return f"Error generating control flow analysis: {str(e)}"


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not set in .env file")
        exit(1)
    agent = AIAgent(api_key)
    print(f"✓ AIAgent initialized with model: {agent.model_name}")
    response = agent.generate_response("What is python?", "Python is a backend language")
    print(f"response: {response}")
