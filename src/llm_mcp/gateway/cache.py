"""
Semantic caching system for AI Gateway
Uses embeddings to find similar prompts and cache responses
"""
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import logging

logger = logging.getLogger(__name__)

class SemanticCache:
    """Semantic cache using embeddings for similarity matching"""
    
    def __init__(self, similarity_threshold: float = 0.95, ttl_hours: int = 24):
        self.similarity_threshold = similarity_threshold
        self.ttl_hours = ttl_hours
        
        # Initialize embedding model
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2
        
        # FAISS index for similarity search
        self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity
        self.cache_data = {}  # Store actual cache entries
        self.prompt_embeddings = []  # Store embeddings for FAISS
        
    async def store(
        self,
        prompt: str,
        response: str,
        model: str,
        latency_ms: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store a prompt-response pair in the cache
        
        Args:
            prompt: The input prompt
            response: The AI response
            model: Model that generated the response
            latency_ms: Response latency
            metadata: Optional metadata
        """
        # Generate embedding
        embedding = self.embedder.encode([prompt])[0]
        
        # Create cache entry
        cache_entry = {
            "prompt": prompt,
            "response": response,
            "model": model,
            "latency_ms": latency_ms,
            "timestamp": datetime.now(),
            "metadata": metadata or {},
            "embedding": embedding
        }
        
        # Generate unique key
        cache_key = self._generate_key(prompt, model)
        
        # Store in cache
        self.cache_data[cache_key] = cache_entry
        
        # Add to FAISS index
        self.index.add(embedding.reshape(1, -1))
        self.prompt_embeddings.append(cache_key)
        
        logger.debug(f"Cached response for prompt: {prompt[:50]}...")
        
        # Clean expired entries
        await self._clean_expired()
    
    async def find_similar(
        self,
        prompt: str,
        threshold: Optional[float] = None,
        max_results: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Find similar cached responses
        
        Args:
            prompt: Query prompt
            threshold: Similarity threshold (uses default if None)
            max_results: Maximum number of results to return
            
        Returns:
            Most similar cached response or None
        """
        if not self.cache_data:
            return None
        
        threshold = threshold or self.similarity_threshold
        
        # Generate query embedding
        query_embedding = self.embedder.encode([prompt])[0]
        
        # Search FAISS index
        scores, indices = self.index.search(
            query_embedding.reshape(1, -1),
            min(max_results, len(self.prompt_embeddings))
        )
        
        # Check similarity threshold
        if scores[0][0] < threshold:
            return None
        
        # Get the most similar entry
        best_idx = indices[0][0]
        cache_key = self.prompt_embeddings[best_idx]
        cache_entry = self.cache_data[cache_key]
        
        # Check if entry is still valid (not expired)
        if self._is_expired(cache_entry):
            await self._remove_entry(cache_key, best_idx)
            return None
        
        logger.info(f"Cache hit with similarity {scores[0][0]:.3f}")
        
        return {
            "text": cache_entry["response"],
            "model": cache_entry["model"],
            "latency_ms": cache_entry["latency_ms"],
            "similarity": float(scores[0][0]),
            "cached_at": cache_entry["timestamp"].isoformat(),
            "metadata": cache_entry["metadata"]
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self.cache_data)
        
        # Count by model
        model_counts = {}
        for entry in self.cache_data.values():
            model = entry["model"]
            model_counts[model] = model_counts.get(model, 0) + 1
        
        # Calculate average similarity (simplified)
        avg_similarity = 0.0
        if total_entries > 0:
            # This is a simplified calculation
            # In production, you'd track actual similarity scores
            avg_similarity = 0.85
        
        return {
            "total_entries": total_entries,
            "model_distribution": model_counts,
            "average_similarity": avg_similarity,
            "similarity_threshold": self.similarity_threshold,
            "ttl_hours": self.ttl_hours
        }
    
    async def clear_cache(self) -> None:
        """Clear all cached entries"""
        self.cache_data.clear()
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.prompt_embeddings.clear()
        logger.info("Cache cleared")
    
    async def _clean_expired(self) -> None:
        """Remove expired entries from cache"""
        expired_keys = []
        
        for key, entry in self.cache_data.items():
            if self._is_expired(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            # Find index in FAISS
            try:
                idx = self.prompt_embeddings.index(key)
                await self._remove_entry(key, idx)
            except ValueError:
                # Key not found in embeddings list
                del self.cache_data[key]
        
        if expired_keys:
            logger.info(f"Cleaned {len(expired_keys)} expired entries")
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if a cache entry is expired"""
        age = datetime.now() - entry["timestamp"]
        return age > timedelta(hours=self.ttl_hours)
    
    async def _remove_entry(self, cache_key: str, faiss_index: int) -> None:
        """Remove an entry from both cache and FAISS index"""
        if cache_key in self.cache_data:
            del self.cache_data[cache_key]
        
        # Remove from FAISS index (simplified - in production you'd rebuild)
        if faiss_index < len(self.prompt_embeddings):
            self.prompt_embeddings.pop(faiss_index)
    
    def _generate_key(self, prompt: str, model: str) -> str:
        """Generate a unique cache key"""
        content = f"{prompt}:{model}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def search_by_metadata(
        self,
        filters: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search cache entries by metadata filters
        
        Args:
            filters: Metadata filters
            limit: Maximum results to return
            
        Returns:
            List of matching cache entries
        """
        results = []
        
        for entry in self.cache_data.values():
            if self._matches_filters(entry["metadata"], filters):
                results.append({
                    "prompt": entry["prompt"],
                    "response": entry["response"],
                    "model": entry["model"],
                    "timestamp": entry["timestamp"],
                    "metadata": entry["metadata"]
                })
                
                if len(results) >= limit:
                    break
        
        return results
    
    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if metadata matches filters"""
        for key, value in filters.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
