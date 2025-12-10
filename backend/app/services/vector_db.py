import faiss
import numpy as np
import pickle
import os
from typing import List, Tuple, Optional, Dict, Any
from sentence_transformers import SentenceTransformer
from app.config import settings
import logging
logger = logging.getLogger(__name__)
class VectorDatabase:
    """Vector database service using FAISS for semantic search"""
    
    def __init__(self):
        self.dimension = settings.VECTOR_DIMENSION
        self.index_path = os.path.join(settings.VECTOR_DB_PATH, "faiss.index")
        self.metadata_path = os.path.join(settings.VECTOR_DB_PATH, "metadata.pkl")
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        
        # Initialize or load FAISS index
        self.index = self._load_or_create_index()
        self.metadata = self._load_metadata()
        
        logger.info(f"Vector database initialized with {self.index.ntotal} vectors")
    
    def _load_or_create_index(self) -> faiss.Index:
        """Load existing FAISS index or create a new one"""
        if os.path.exists(self.index_path):
            try:
                logger.info(f"Loading existing FAISS index from {self.index_path}")
                return faiss.read_index(self.index_path)
            except Exception as e:
                logger.error(f"Error loading FAISS index: {e}")
                logger.info("Creating new FAISS index")
        
        # Create new index with L2 distance
        index = faiss.IndexFlatL2(self.dimension)
        return index
    
    def _load_metadata(self) -> List[Dict[str, Any]]:
        """Load metadata for stored vectors"""
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
        
        return []
    
    def _save_index(self):
        """Save FAISS index to disk"""
        try:
            faiss.write_index(self.index, self.index_path)
            logger.info(f"FAISS index saved to {self.index_path}")
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")
    
    def _save_metadata(self):
        """Save metadata to disk"""
        try:
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            logger.info(f"Metadata saved to {self.metadata_path}")
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for text
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as numpy array
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.astype('float32')
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts
            
        Returns:
            Matrix of embedding vectors
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.astype('float32')
    
    def add_documents(
        self,
        texts: List[str],
        patient_id: str,
        file_id: Optional[str] = None,
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[int]:
        """
        Add documents to the vector database
        
        Args:
            texts: List of text chunks to add
            patient_id: Patient ID
            file_id: Optional file ID
            metadata: Optional additional metadata for each chunk
            
        Returns:
            List of vector IDs
        """
        if not texts:
            return []
        
        # Generate embeddings
        embeddings = self.embed_texts(texts)
        
        # Get starting index
        start_idx = self.index.ntotal
        
        # Add to FAISS index
        self.index.add(embeddings)
        
        # Create metadata entries
        vector_ids = []
        for i, text in enumerate(texts):
            vector_id = start_idx + i
            vector_ids.append(vector_id)
            
            meta = {
                "vector_id": vector_id,
                "patient_id": patient_id,
                "file_id": file_id,
                "text": text,
                "chunk_index": i
            }
            
            # Add additional metadata if provided
            if metadata and i < len(metadata):
                meta.update(metadata[i])
            
            self.metadata.append(meta)
        
        # Save to disk
        self._save_index()
        self._save_metadata()
        
        logger.info(f"Added {len(texts)} documents to vector database")
        return vector_ids
    
    def search(
        self,
        query: str,
        patient_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            patient_id: Optional patient ID to filter results
            top_k: Number of results to return
            
        Returns:
            List of (metadata, similarity_score) tuples
        """
        if self.index.ntotal == 0:
            logger.warning("Vector database is empty")
            return []
        
        # Generate query embedding
        query_embedding = self.embed_text(query)
        query_embedding = query_embedding.reshape(1, -1)
        
        # Search in FAISS
        # Get more results if filtering by patient_id
        search_k = top_k * 10 if patient_id else top_k
        distances, indices = self.index.search(query_embedding, min(search_k, self.index.ntotal))
        
        # Collect results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):
                meta = self.metadata[idx]
                
                # Filter by patient_id if specified
                if patient_id and meta.get("patient_id") != patient_id:
                    continue
                
                # Convert L2 distance to similarity score (0-1)
                similarity = 1 / (1 + dist)
                results.append((meta, float(similarity)))
                
                if len(results) >= top_k:
                    break
        
        return results
    
    def delete_by_patient(self, patient_id: str) -> int:
        """
        Delete all documents for a patient
        
        Args:
            patient_id: Patient ID
            
        Returns:
            Number of documents deleted
        """
        # Filter metadata
        original_count = len(self.metadata)
        self.metadata = [m for m in self.metadata if m.get("patient_id") != patient_id]
        deleted_count = original_count - len(self.metadata)
        
        if deleted_count > 0:
            # Rebuild index without deleted vectors
            self._rebuild_index()
            logger.info(f"Deleted {deleted_count} documents for patient {patient_id}")
        
        return deleted_count
    
    def delete_by_file(self, file_id: str) -> int:
        """
        Delete all documents for a file
        
        Args:
            file_id: File ID
            
        Returns:
            Number of documents deleted
        """
        original_count = len(self.metadata)
        self.metadata = [m for m in self.metadata if m.get("file_id") != file_id]
        deleted_count = original_count - len(self.metadata)
        
        if deleted_count > 0:
            self._rebuild_index()
            logger.info(f"Deleted {deleted_count} documents for file {file_id}")
        
        return deleted_count
    
    def _rebuild_index(self):
        """Rebuild FAISS index from remaining metadata"""
        if not self.metadata:
            # Create empty index
            self.index = faiss.IndexFlatL2(self.dimension)
        else:
            # Re-embed all remaining texts
            texts = [m["text"] for m in self.metadata]
            embeddings = self.embed_texts(texts)
            
            # Create new index
            self.index = faiss.IndexFlatL2(self.dimension)
            self.index.add(embeddings)
            
            # Update vector IDs in metadata
            for i, meta in enumerate(self.metadata):
                meta["vector_id"] = i
        
        # Save updated index and metadata
        self._save_index()
        self._save_metadata()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector database statistics"""
        patient_counts = {}
        for meta in self.metadata:
            patient_id = meta.get("patient_id")
            if patient_id:
                patient_counts[patient_id] = patient_counts.get(patient_id, 0) + 1
        
        return {
            "total_vectors": self.index.ntotal,
            "total_metadata": len(self.metadata),
            "dimension": self.dimension,
            "patients": len(patient_counts),
            "patient_counts": patient_counts
        }
    
    def is_initialized(self) -> bool:
        """Check if vector database is initialized"""
        return self.index is not None and self.model is not None
# Create global vector database instance
vector_db = VectorDatabase()
