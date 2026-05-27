"""
Vector embeddings and retrieval service module.

Handles:
- Document chunking (splitting large texts into manageable pieces)
- Embedding generation using Google GenAI API
- ChromaDB integration for vector storage and semantic search
- Context retrieval based on query similarity

TODO: Add caching layer for embeddings
TODO: Add configurable chunking strategy (token-based, sentence-based)
TODO: Add metadata filtering for more precise retrieval
TODO: Add re-ranking of retrieved chunks
"""

import os
from google import genai
import chromadb
import logging
from typing import List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """
    Manages document embeddings and vector search using ChromaDB.
    
    TODO: Add connection pooling if using persistent ChromaDB
    TODO: Add embedding model selection
    """
    
    def __init__(self, chromadb_path: str = "./.chromadb", api_key: str = None):
        """
        Initialize embeddings service.
        
        Args:
            chromadb_path (str): Path where ChromaDB stores data
            api_key (str): Google GenAI API key
            
        TODO: Validate chromadb_path exists and is writable
        """
        # Resolve API key: prefer explicit param, fallback to env var
        if not api_key:
            api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Google api key is missing")

        # Initialize GenAI client
        try:
            self.genai_client = genai.Client(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Google GenAI client: {e}")
            raise RuntimeError("Failed to initialize Google GenAI client") from e

        # Initialize ChromaDB persistent client (ensure path exists)
        self.chromadb_path = chromadb_path
        Path(chromadb_path).mkdir(parents=True, exist_ok=True)
        try:
            # Prefer PersistentClient if available in this chromadb version
            if hasattr(chromadb, 'PersistentClient'):
                self.chromadb_client = chromadb.PersistentClient(path=chromadb_path)
            else:
                # Fallback to Client with Settings (some versions expect settings)
                try:
                    settings = chromadb.config.Settings(persist_directory=chromadb_path)
                    self.chromadb_client = chromadb.Client(settings)
                except Exception:
                    # Last resort: plain Client()
                    self.chromadb_client = chromadb.Client()
            logger.info(f"ChromaDB initialized at {chromadb_path}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise RuntimeError("Failed to initialize ChromaDB client") from e
    
    def embed_document(self, doc_id: int, document_text: str, metadata: dict = None) -> str:
        """
        Process a document: chunk it, embed chunks, and store in ChromaDB.
        
        Args:
            doc_id (int): Document ID from database
            document_text (str): Full text of document
            metadata (dict): Additional metadata (filename, title, etc.)
            
        Returns:
            str: ChromaDB collection name (for reference)
            
        TODO: Add transaction handling
        TODO: Add progress reporting for large documents
        TODO: Add duplicate chunk detection
        """
        if doc_id < 1:
            raise ValueError("Invalid document id")

        if not document_text.strip():
            raise ValueError("Document is empty")
        
        try:
            # Step 1: Chunk the document
            chunks = self._chunk_text(document_text)
            logger.info(f"Document {doc_id}: Created {len(chunks)} chunks")
            
            # Step 2: Get or create ChromaDB collection for this document
            collection_name = f"doc_{doc_id}"
            collection = self.chromadb_client.get_or_create_collection(
                name=collection_name,
                metadata={"doc_id": doc_id}
            )
            
            # Step 3: Embed and store each chunk (simple retry on failure)
            for chunk_idx, chunk in enumerate(chunks):
                embedding = None
                last_exc = None
                # Try up to 2 times (initial attempt + one retry)
                for attempt in range(2):
                    try:
                        embedding_result = self.genai_client.models.embed_content(
                            model="models/embedding-001",
                            contents=chunk,
                        )
                        embedding = getattr(embedding_result, 'embedding', None)
                        break
                    except Exception as e:
                        last_exc = e
                        logger.warning(f"Embedding attempt {attempt+1} failed for chunk {chunk_idx}: {e}")

                if embedding is None:
                    logger.error(f"Error embedding chunk {chunk_idx}: {last_exc}")
                    # Continue with next chunk
                    continue

                try:
                    # Store in ChromaDB
                    collection.add(
                        ids=[f"{collection_name}_chunk_{chunk_idx}"],
                        documents=[chunk],
                        embeddings=[embedding],
                        metadatas=[{
                            "doc_id": doc_id,
                            "chunk_idx": chunk_idx,
                            "chunk_count": len(chunks),
                        }]
                    )
                except Exception as e:
                    logger.error(f"Error adding chunk {chunk_idx} to collection: {str(e)}")
                    continue
            
            logger.info(f"Document {doc_id} embedded and stored in ChromaDB")
            return collection_name
        
        except Exception as e:
            logger.error(f"Error embedding document {doc_id}: {str(e)}")
            raise
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """
        Split text into chunks for embedding.
        
        Uses a simple token-based approach (approximation: 1 token ≈ 4 characters).
        
        Args:
            text (str): Document text to chunk
            chunk_size (int): Target chunk size in tokens (~4 chars per token)
            overlap (int): Overlap between consecutive chunks in tokens
            
        Returns:
            List[str]: List of text chunks
            
        TODO: Implement proper token-based chunking (use tiktoken)
        TODO: Add sentence-aware chunking to avoid breaking mid-sentence
        TODO: Add configurable chunking strategy
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")

        if overlap < 0:
            raise ValueError("overlap cannot be negative")

        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        target_size = chunk_size * 4
        overlap_size = overlap * 4

        text = " ".join(text.split())

        if not text:
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + target_size, text_length)

            if end < text_length:
                boundary_window = text[start:end]

                split_idx = max(
                    boundary_window.rfind("\n\n"),
                    boundary_window.rfind(". "),
                    boundary_window.rfind("! "),
                    boundary_window.rfind("? "),
                    boundary_window.rfind(" ")
                )

                if split_idx > int(target_size * 0.6):
                    end = start + split_idx + 1

            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            start = max(start + 1, end - overlap_size)

        return chunks
    
    def retrieve_context(
        self,
        query: str,
        doc_id: int,
        top_k: int = 3,
        min_similarity: float = 0.0
    ) -> str:
        """
        Retrieve relevant document chunks for a query using semantic search.
        
        Args:
            query (str): User's question
            doc_id (int): Document ID to search within
            top_k (int): Number of chunks to retrieve
            min_similarity (float): Minimum similarity threshold (0.0-1.0)
            
        Returns:
            str: Concatenated relevant chunks (context for AI agent)
            
        TODO: Add re-ranking of results
        TODO: Add diversity in results (avoid redundant chunks)
        TODO: Add confidence scores to results
        """
        try:
            # Get collection for this document
            collection_name = f"doc_{doc_id}"
            collection = self.chromadb_client.get_collection(collection_name)

            # Query for similar chunks
            results = collection.query(
                query_texts=[query],
                n_results=top_k,
            )

            # Extract, filter by min_similarity (if distances provided), and deduplicate
            retrieved_chunks = []
            seen = set()

            if results and results.get('documents'):
                docs_list = results.get('documents')[0]
                metas_list = None
                dists_list = None
                if results.get('metadatas'):
                    metas_list = results.get('metadatas')[0]
                if results.get('distances'):
                    dists_list = results.get('distances')[0]

                for i, chunk in enumerate(docs_list):
                    # compute a best-effort similarity if distances present and in [0,1]
                    accept = True
                    if dists_list and i < len(dists_list):
                        try:
                            dist = float(dists_list[i])
                            # if distance looks normalized (0..1), convert to similarity
                            if 0.0 <= dist <= 1.0:
                                similarity = 1.0 - dist
                                if similarity < min_similarity:
                                    accept = False
                        except Exception:
                            # cannot interpret distance, do not filter
                            pass

                    if not accept:
                        continue

                    # deduplicate by chunk text
                    key = chunk.strip()
                    if not key or key in seen:
                        continue
                    seen.add(key)
                    retrieved_chunks.append(chunk)

            context = "\n\n".join(retrieved_chunks)
            logger.info(f"Retrieved {len(retrieved_chunks)} chunks for query in doc {doc_id}")

            return context
        
        except Exception as e:
            logger.error(f"Error retrieving context for doc {doc_id}: {str(e)}")
            return ""
    
    def delete_document_embeddings(self, doc_id: int) -> bool:
        """
        Delete all embeddings for a document when document is deleted.
        
        Args:
            doc_id (int): Document ID
            
        Returns:
            bool: True if successful
            
        TODO: Add error handling
        """
        try:
            collection_name = f"doc_{doc_id}"
            self.chromadb_client.delete_collection(name=collection_name)
            logger.info(f"Deleted embeddings for document {doc_id}")
            return True
        except Exception as e:
            logger.warning(f"Could not delete embeddings for doc {doc_id}: {str(e)}")
            return False
