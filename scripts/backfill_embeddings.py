#!/usr/bin/env python3
"""
Backfill embeddings for existing chunks.

Phase 8 added automatic embedding at chunk creation time,
but existing chunks don't have embeddings yet. This script
retroactively generates and stores embeddings for all chunks.

Usage:
    python3 scripts/backfill_embeddings.py [--dry-run]
"""

import json
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from mcp_server.tools.embeddings import _get_cached_provider
from mcp_server.tools.vecstore import VectorStore


CONTEXT_DIR = ROOT / "context"
INDEX_FILE = CONTEXT_DIR / "index.json"
CHUNKS_DIR = CONTEXT_DIR / "chunks"


def extract_content(chunk_file: Path) -> str:
    """Extract content from a chunk file, skipping YAML header."""
    text = chunk_file.read_text(encoding="utf-8")
    lines = text.split("\n")
    content_start = 0
    in_header = False

    for i, line in enumerate(lines):
        if line.strip() == "---":
            if not in_header:
                in_header = True
            else:
                content_start = i + 1
                break

    return "\n".join(lines[content_start:])


def main():
    dry_run = "--dry-run" in sys.argv

    # Check provider
    provider = _get_cached_provider()
    if provider is None:
        print("ERROR: No embedding provider available.")
        print("Install with: pip install mcp-rlm-server[semantic]")
        sys.exit(1)

    print(f"Provider: {type(provider).__name__} (dim={provider.dim()})")

    # Load index
    if not INDEX_FILE.exists():
        print("ERROR: index.json not found")
        sys.exit(1)

    with open(INDEX_FILE, encoding="utf-8") as f:
        index = json.load(f)

    chunks = index["chunks"]
    print(f"Total chunks in index: {len(chunks)}")

    # Load existing vector store
    store = VectorStore()
    store.load()
    existing_ids = set(store.chunk_ids)
    print(f"Already embedded: {len(existing_ids)}")

    embedded = 0
    skipped = 0
    errors = 0

    for chunk_info in chunks:
        chunk_id = chunk_info["id"]
        chunk_file = CONTEXT_DIR / chunk_info["file"]

        # Skip if already embedded
        if chunk_id in existing_ids:
            skipped += 1
            continue

        if not chunk_file.exists():
            print(f"  SKIP {chunk_id}: file not found")
            errors += 1
            continue

        content = extract_content(chunk_file)
        if not content.strip():
            print(f"  SKIP {chunk_id}: empty content")
            skipped += 1
            continue

        if dry_run:
            print(f"  WOULD EMBED {chunk_id} ({len(content)} chars)")
            embedded += 1
            continue

        try:
            vec = provider.embed([content])[0]
            store.add(chunk_id, vec)
            embedded += 1
            if embedded % 10 == 0:
                print(f"  Embedded {embedded} chunks...")
        except Exception as e:
            print(f"  ERROR {chunk_id}: {e}")
            errors += 1

    # Save
    if not dry_run and embedded > 0:
        store.save()
        print(f"\nSaved to {store.path}")

    # Summary
    mode = "[DRY RUN] " if dry_run else ""
    print(f"\n{mode}Backfill complete:")
    print(f"  Embedded: {embedded}")
    print(f"  Skipped (already embedded or empty): {skipped}")
    print(f"  Errors: {errors}")
    print(f"  Total in store: {len(store.chunk_ids)}")


if __name__ == "__main__":
    main()
