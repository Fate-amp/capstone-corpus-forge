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

import google.generativeai as genai
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
        genai.configure(api_key=api_key)
        
        # Initialize ChromaDB client (in-process)
        self.client = chromadb.Client(
            chromadb.config.Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=chromadb_path,
                anonymized_telemetry=False,
            )
        )
        self.chromadb_path = chromadb_path
        logger.info(f"ChromaDB initialized at {chromadb_path}")
    
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
        try:
            # Step 1: Chunk the document
            chunks = self._chunk_text(document_text)
            logger.info(f"Document {doc_id}: Created {len(chunks)} chunks")
            
            # Step 2: Get or create ChromaDB collection for this document
            collection_name = f"doc_{doc_id}"
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"doc_id": doc_id}
            )
            
            # Step 3: Embed and store each chunk
            for chunk_idx, chunk in enumerate(chunks):
                try:
                    # Generate embedding
                    embedding_result = genai.embed_content(
                        model="models/embedding-001",
                        content=chunk,
                    )
                    embedding = embedding_result['embedding']
                    
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
                    logger.error(f"Error embedding chunk {chunk_idx}: {str(e)}")
                    # Continue with next chunk
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
        # Convert token size to character size (rough approximation)
        char_size = chunk_size * 4
        char_overlap = overlap * 4
        
        chunks = []
        current_pos = 0
        
        while current_pos < len(text):
            # Extract chunk
            chunk = text[current_pos:current_pos + char_size]
            
            # Try to end at a sentence boundary (if near the end)
            if current_pos + char_size < len(text):
                last_period = chunk.rfind('.')
                if last_period > len(chunk) * 0.8:  # If period is close to end
                    chunk = chunk[:last_period + 1]
            
            chunks.append(chunk)
            
            # Move position for next chunk (with overlap)
            current_pos += len(chunk) - char_overlap
        
        return [c for c in chunks if c.strip()]  # Remove empty chunks
    
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
            collection = self.client.get_collection(collection_name)
            
            # Query for similar chunks
            results = collection.query(
                query_texts=[query],
                n_results=top_k,
            )
            
            # Extract and concatenate chunks
            retrieved_chunks = []
            if results and results['documents']:
                for chunk in results['documents'][0]:
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
            self.client.delete_collection(name=collection_name)
            logger.info(f"Deleted embeddings for document {doc_id}")
            return True
        except Exception as e:
            logger.warning(f"Could not delete embeddings for doc {doc_id}: {str(e)}")
            return False
