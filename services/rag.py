import os
import logging
import numpy as np
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def _get_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
KB_DIR = Path(__file__).parent.parent / "knowledge_base"
TOP_K = 3
SIMILARITY_THRESHOLD = 0.40
MAX_CHUNK_WORDS = 200
OVERLAP_WORDS = 30


class RAGService:
    def __init__(self):
        self._chunks: list[dict] = []
        self._embeddings: np.ndarray | None = None
        self._ready = False

    def load(self) -> None:
        if self._ready:
            return

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("RAG: OPENAI_API_KEY não configurada — RAG desativado.")
            return

        md_files = sorted(KB_DIR.glob("*.md"))
        if not md_files:
            logger.warning("RAG: nenhum arquivo encontrado em %s — RAG desativado.", KB_DIR)
            return

        chunks: list[dict] = []
        for path in md_files:
            text = path.read_text(encoding="utf-8")
            chunks.extend(self._split(text, path.name))

        if not chunks:
            return

        try:
            client = _get_client()
            texts = [c["text"] for c in chunks]
            response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
            self._embeddings = np.array(
                [e.embedding for e in response.data], dtype=np.float32
            )
            self._chunks = chunks
            self._ready = True
            logger.info("RAG: %d chunks carregados de %d arquivos.", len(chunks), len(md_files))
        except Exception:
            logger.exception("RAG: falha ao gerar embeddings — RAG desativado.")

    def retrieve(self, query: str) -> list[str]:
        if not self._ready:
            return []

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return []

        try:
            client = _get_client()
            resp = client.embeddings.create(model=EMBEDDING_MODEL, input=[query])
            query_vec = np.array(resp.data[0].embedding, dtype=np.float32)
        except Exception:
            logger.exception("RAG: falha ao criar embedding da query.")
            return []

        norms = np.linalg.norm(self._embeddings, axis=1) * np.linalg.norm(query_vec)
        # evitar divisão por zero
        norms = np.where(norms == 0, 1e-9, norms)
        scores = (self._embeddings @ query_vec) / norms

        top_idx = np.argsort(scores)[-TOP_K:][::-1]
        return [
            self._chunks[i]["text"]
            for i in top_idx
            if scores[i] >= SIMILARITY_THRESHOLD
        ]

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------

    def _split(self, text: str, source: str) -> list[dict]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: list[dict] = []
        buffer: list[str] = []
        buffer_len = 0

        for para in paragraphs:
            words = para.split()
            if buffer_len + len(words) > MAX_CHUNK_WORDS and buffer:
                chunks.append({"text": " ".join(buffer), "source": source})
                # keep overlap from end of previous chunk
                buffer = buffer[-OVERLAP_WORDS:]
                buffer_len = len(buffer)
            buffer.extend(words)
            buffer_len += len(words)

        if buffer:
            chunks.append({"text": " ".join(buffer), "source": source})

        return chunks


rag_service = RAGService()
