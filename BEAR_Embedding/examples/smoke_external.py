"""Opt-in real service smoke test; creates and removes its own Qdrant collection."""

import argparse
import json
import os
import tempfile
import time
from pathlib import Path
from uuid import uuid4

from bear_text_beta.models import DocumentContext, ProcessingProfile
from bear_text_beta.parsing import TXTParser
from bear_text_beta.runtime import Services


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, required=True)
    args = parser.parse_args()
    collection = "bear_embedding_smoke_" + uuid4().hex
    old_collection = os.environ.get("BEAR_QDRANT_COLLECTION")
    os.environ["BEAR_QDRANT_COLLECTION"] = collection
    runtime = None
    try:
        with tempfile.TemporaryDirectory(prefix="bear-embedding-smoke-") as directory:
            runtime = Services(directory, args.model_dir)
            # This verifies the embedding boundary without needing an external Dedoc server.
            runtime.parser.parsers[".txt"] = TXTParser()
            if runtime.embeddings.health().get("ready") is not True:
                raise RuntimeError("Infinity is not ready or served model ID does not match")
            context = DocumentContext("smoke-tenant", "smoke-space", "ssl", 1, "ssl.txt")
            result = runtime.process(Path(__file__).with_name("ssl.txt").read_bytes(), context,
                                     ProcessingProfile(mode="token"))
            indexed = runtime.indexer.index(result)
            started = time.perf_counter()
            hits = runtime.indexer.search("Как настроить SSL в nginx?", "smoke-tenant", "smoke-space", 50)
            elapsed_ms = (time.perf_counter() - started) * 1000
            if not hits or hits[0].payload["document_id"] != "ssl":
                raise RuntimeError("Indexed document was not retrieved")
            print(json.dumps({"mode": "REAL external-service smoke (not a benchmark)", "index": indexed,
                              "collection": collection, "query_total_ms": elapsed_ms,
                              "hit_ids": [hit.id for hit in hits]}, ensure_ascii=False, indent=2))
    finally:
        try:
            if runtime:
                # The name is generated above; never target the user's existing collection.
                if runtime.vectors._collection_ready:
                    runtime.vectors.request("DELETE", "collections/" + collection)
        finally:
            if runtime:
                runtime.close()
            if old_collection is None:
                os.environ.pop("BEAR_QDRANT_COLLECTION", None)
            else:
                os.environ["BEAR_QDRANT_COLLECTION"] = old_collection


if __name__ == "__main__":
    main()
