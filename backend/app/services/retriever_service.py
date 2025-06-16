from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from qdrant_client.models import Filter, SearchRequest, PointStruct, SearchParams
from typing import List

class RetrieverService:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "therapy_knowledge_base",
        embedding_model_name: str = "all-MiniLM-L6-v2"
    ):
        self.qdrant = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self.model = SentenceTransformer(embedding_model_name)

    def search(self, query: str, top_k: int = 3) -> List[str]:
        """
        Search Qdrant for chunks similar to the user query.
        Returns a list of relevant text chunks.
        """
        query_vector = self.model.encode(query).tolist()

        results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            search_params=SearchParams(hnsw_ef=128)
        )

        return [hit.payload["text"] for hit in results if "text" in hit.payload]
