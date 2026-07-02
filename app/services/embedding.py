import httpx
import re
import zlib
from fastapi import HTTPException
from app.config import settings

class EmbeddingService:
    def __init__(self):
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {settings.DIGITALOCEAN_BGE_KEY}",
                "Content-Type": "application/json"
            },
            timeout=15.0
        )

    def _generate_local_sparse_vector(self, text: str) -> dict[int, float]:
        """
        Generates a highly efficient lexical sparse vector using term-frequency token hashing.
        Runs in pure Python with zero memory footprint—perfect for Python 3.14 compatibility.
        """
        # Extract alphanumeric lowercase word tokens
        words = re.findall(r'\w+', text.lower())
        if not words:
            return {0: 1.0}
        
        counts = {}
        for word in words:
            # Generate a stable, positive 32-bit integer ID for the exact word string
            word_hash = zlib.crc32(word.encode('utf-8')) & 0x7FFFFFFF
            counts[word_hash] = counts.get(word_hash, 0.0) + 1.0
            
        # Normalize term-frequency weights by document word count
        total_words = len(words)
        return {int(k): float(v / total_words) for k, v in counts.items()}

    async def get_hybrid_embeddings(self, text: str) -> tuple[list[float], dict[int, float]]:
        """
        Fetches the dense vector from DigitalOcean's Inference Gateway using OpenAI-compatible specs,
        and couples it with a localized lexical sparse vector for perfect hybrid retrieval accuracy.
        """
        try:
            # Match DigitalOcean's serverless inference format exactly
            payload = {
                "model": "bge-m3",
                "input": [text],
                "encoding_format": "float"
            }
            
            response = await self.client.post(
                settings.DIGITALOCEAN_BGE_URL,
                json=payload
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=502, 
                    detail=f"DigitalOcean BGE API error: {response.status_code}: {response.text}"
                )
            
            data = response.json()
            
            # Extract standard OpenAI-compatible embedding array (1024 dimensions)
            dense_vector = data["data"][0]["embedding"]
            
            # Generate the companion token keyword sparse vector locally
            sparse_vector = self._generate_local_sparse_vector(text)
            
            return dense_vector, sparse_vector
            
        except KeyError:
            raise HTTPException(status_code=502, detail="Unexpected response structure from DigitalOcean endpoint.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Embedding Inference failure: {str(e)}")

    async def close(self):
        await self.client.aclose()

embedding_service = EmbeddingService()