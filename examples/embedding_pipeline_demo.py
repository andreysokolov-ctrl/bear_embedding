"""Offline wiring demo: real TXT parsing/chunking and clearly mocked HTTP inference.

Run from the repository root after editable installation. No model quality claims.
"""

import json
from dataclasses import asdict
from pathlib import Path

import httpx
from bear_text_beta.chunking import ChunkingService
from bear_text_beta.embedding_pipeline import EmbeddingPipeline, MemoryVectorCache
from bear_text_beta.embeddings import InfinityEmbeddingProvider
from bear_text_beta.models import DocumentContext, EmbeddingProfile, ProcessingProfile
from bear_text_beta.parsing import TXTParser
from chonkie.tokenizer import CharacterTokenizer


class DemoCounter:
    """Test-only character counter, never use with actual inference or Qdrant."""

    def __init__(self, profile):
        self.profile = profile
        self.tokenizer = CharacterTokenizer()

    def count(self, text):
        return len(text)

    def full_count(self, text, purpose="document"):
        return len(self.profile.prefix(purpose) + text) + 2


def main():
    profile = EmbeddingProfile(model_id="MOCK-NOT-A-REAL-MODEL", model_revision="demo",
                               tokenizer_revision="demo", vector_dimension=4)
    counter = DemoCounter(profile)
    requests = []

    def mock_infinity(request):
        payload = json.loads(request.content)
        requests.append(payload)
        return httpx.Response(200, json={"data": [
            {"index": index, "embedding": [3, 4, 0, 0]}
            for index in reversed(range(len(payload["input"])))
        ]})

    client = httpx.Client(base_url="http://mock-infinity/v1/", transport=httpx.MockTransport(mock_infinity))
    provider = InfinityEmbeddingProvider("", profile, counter, client=client)
    events = []
    with EmbeddingPipeline(provider, counter, profile, max_tokens=480,
                           cache=MemoryVectorCache(), on_event=events.append) as pipeline:
        context = DocumentContext("demo-tenant", "demo-space", "ssl-guide", 1, "ssl.txt")
        text = Path(__file__).with_name("ssl.txt").read_bytes()
        document = TXTParser().parse(text, context)
        result = ChunkingService(counter, pipeline, profile).process(document, ProcessingProfile(mode="token"))
        embedded = pipeline.vectorize_chunks(result)
        query = pipeline.vectorize_query("  Как\n настроить SSL?  ")
        pipeline.embed("Как настроить SSL?")  # Same prepared text; cache hit.
        print(json.dumps({
            "mode": "MOCK: contract demo, not retrieval quality",
            "chunks": len(embedded), "dimension": len(query.vector),
            "original_query": query.query.original, "prepared_query": query.query.text,
            "sample_embedded_chunk": asdict(embedded[0]),
            "events": [asdict(event) for event in events], "http_requests": len(requests),
        }, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
