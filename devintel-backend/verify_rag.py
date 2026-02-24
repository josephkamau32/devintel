import os
# Override database URL for host execution - MUST BE BEFORE IMPORTS
os.environ["DATABASE_URL"] = "postgresql+asyncpg://devintel:devintel@localhost:5432/devintel_db"

import asyncio
from uuid import UUID
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.services.chat import ChatService
from app.repositories.embedding import EmbeddingRepository
from app.models.embedding import Embedding

async def verify_context_expansion():
    print("🚀 Verifying Context Expansion...")
    chat_service = ChatService()
    
    async with AsyncSessionLocal() as db:
        embedding_repo = EmbeddingRepository(db)
        
        # Find any repo with embeddings
        result = await db.execute(select(Embedding).limit(1))
        emb = result.scalars().first()
        
        if not emb:
            print("❌ No embeddings found in database. Please index a repository first.")
            return

        print(f"Found sample embedding in file: {emb.file_path} (Index {emb.chunk_index})")
        
        # Test retrieval with expansion
        # We'll use a dummy question but focus on the expansion logic
        results = await chat_service.retrieve_relevant_chunks(
            repo_id=emb.repo_id,
            question="dummy",
            embedding_repo=embedding_repo,
            top_k=1,
            expand_context=True
        )
        
        print(f"Retrieved {len(results)} chunks (expected 2 or 3 if neighbors exist)")
        for n, sim in results:
            print(f"  - Chunk {n.chunk_index} (Similarity: {sim:.4f})")
            
        if len(results) > 1:
            print("✅ Context expansion successful!")
        else:
            print("⚠️ Only 1 chunk retrieved. This might be because the file only has one chunk.")

if __name__ == "__main__":
    asyncio.run(verify_context_expansion())
