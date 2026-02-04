"""
Tests for RLM Phase 9: Chunking Typé (chunk_type parameter).

Tests cover:
- Valid chunk types (snapshot, session, debug) accepted and persisted
- Default chunk_type is "session"
- Invalid chunk_type rejected with error
- "insight" type redirects to rlm_remember()
- chunk_type stored in YAML frontmatter
- chunk_type stored in index.json
- Backward compatibility with chunks lacking chunk_type
"""

import json

import pytest


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def chunk_context(temp_context_dir, monkeypatch):
    """Set up context with navigation module patched."""
    import mcp_server.tools.navigation as navigation
    import mcp_server.tools.sessions as sessions

    monkeypatch.setattr(navigation, "CONTEXT_DIR", temp_context_dir)
    monkeypatch.setattr(navigation, "CHUNKS_DIR", temp_context_dir / "chunks")
    monkeypatch.setattr(navigation, "INDEX_FILE", temp_context_dir / "index.json")

    # Patch sessions module paths
    monkeypatch.setattr(sessions, "CONTEXT_DIR", temp_context_dir)
    monkeypatch.setattr(sessions, "SESSIONS_FILE", temp_context_dir / "sessions.json")

    return temp_context_dir


# =============================================================================
# TESTS: Validation
# =============================================================================


class TestChunkTypeValidation:
    """Tests for chunk_type parameter validation."""

    def test_valid_types_accepted(self, chunk_context):
        """snapshot, session, debug should all be accepted."""
        from mcp_server.tools.navigation import chunk

        for ctype in ("snapshot", "session", "debug"):
            result = chunk(f"Content for {ctype} test", chunk_type=ctype, tags=["test"])
            assert result["status"] == "created", f"Type '{ctype}' should be accepted"

    def test_default_type_is_session(self, chunk_context):
        """Without explicit chunk_type, default should be 'session'."""
        from mcp_server.tools.navigation import chunk

        result = chunk("Content without explicit type", tags=["test"])
        assert result["status"] == "created"

        # Verify in index
        index = json.loads((chunk_context / "index.json").read_text())
        created_chunk = next(c for c in index["chunks"] if c["id"] == result["chunk_id"])
        assert created_chunk["chunk_type"] == "session"

    def test_invalid_type_rejected(self, chunk_context):
        """Invalid chunk_type should return error."""
        from mcp_server.tools.navigation import chunk

        result = chunk("This should fail", chunk_type="foobar")
        assert result["status"] == "error"
        assert "foobar" in result["message"]
        assert "snapshot" in result["message"]  # Lists valid types

    def test_insight_redirects(self, chunk_context):
        """chunk_type='insight' should redirect to rlm_remember()."""
        from mcp_server.tools.navigation import chunk

        result = chunk("This is a permanent fact", chunk_type="insight")
        assert result["status"] == "redirect"
        assert "rlm_remember" in result["message"]

    def test_insight_does_not_create_chunk(self, chunk_context):
        """Insight redirect should NOT create a chunk file."""
        from mcp_server.tools.navigation import chunk

        chunk("Should not be saved", chunk_type="insight")

        index = json.loads((chunk_context / "index.json").read_text())
        assert len(index["chunks"]) == 0


# =============================================================================
# TESTS: Persistence
# =============================================================================


class TestChunkTypePersistence:
    """Tests for chunk_type storage in YAML frontmatter and index."""

    def test_chunk_type_in_yaml_frontmatter(self, chunk_context):
        """chunk_type should appear in the YAML frontmatter of .md file."""
        from mcp_server.tools.navigation import chunk

        result = chunk("Debug content", chunk_type="debug", tags=["test"])
        chunk_id = result["chunk_id"]

        chunk_file = chunk_context / "chunks" / f"{chunk_id}.md"
        content = chunk_file.read_text()

        assert "chunk_type: debug" in content

    def test_chunk_type_in_index(self, chunk_context):
        """chunk_type should be stored in index.json metadata."""
        from mcp_server.tools.navigation import chunk

        result = chunk("Snapshot content", chunk_type="snapshot", tags=["test"])
        chunk_id = result["chunk_id"]

        index = json.loads((chunk_context / "index.json").read_text())
        created_chunk = next(c for c in index["chunks"] if c["id"] == chunk_id)
        assert created_chunk["chunk_type"] == "snapshot"

    def test_each_type_persists_correctly(self, chunk_context):
        """Each valid type should persist its own value."""
        from mcp_server.tools.navigation import chunk

        types_created = {}
        for ctype in ("snapshot", "session", "debug"):
            result = chunk(f"Content {ctype}", chunk_type=ctype, tags=["test"])
            types_created[result["chunk_id"]] = ctype

        index = json.loads((chunk_context / "index.json").read_text())
        for idx_chunk in index["chunks"]:
            expected = types_created.get(idx_chunk["id"])
            if expected:
                assert idx_chunk["chunk_type"] == expected


# =============================================================================
# TESTS: Backward Compatibility
# =============================================================================


class TestChunkTypeBackwardCompat:
    """Tests for backward compatibility with pre-Phase 9 chunks."""

    def test_old_chunks_without_type_readable(self, chunk_context):
        """Chunks without chunk_type in index should still be readable via peek."""
        from mcp_server.tools.navigation import peek

        # Create a legacy chunk (no chunk_type in index or YAML)
        chunks_dir = chunk_context / "chunks"
        legacy_file = chunks_dir / "legacy_001.md"
        legacy_file.write_text("""---
summary: Legacy chunk without type
tags: legacy, test
created: 2026-01-15T10:00:00
---

This is a legacy chunk from before Phase 9.
""")

        index = json.loads((chunk_context / "index.json").read_text())
        index["chunks"].append({
            "id": "legacy_001",
            "file": "chunks/legacy_001.md",
            "summary": "Legacy chunk without type",
            "tags": ["legacy", "test"],
            "tokens_estimate": 15,
            "access_count": 0,
            "created_at": "2026-01-15T10:00:00",
        })
        (chunk_context / "index.json").write_text(json.dumps(index, indent=2))

        result = peek("legacy_001")
        assert result["status"] == "success"
        assert "legacy chunk" in result["content"].lower()
