#!/usr/bin/env python3
"""
RLM MCP Server - Recursive Language Models for Claude Code

A Model Context Protocol server that provides tools for infinite memory
and context management, inspired by MIT CSAIL's RLM paper.

Phase 1: Memory tools (remember, recall)
Phase 2: Navigation tools (peek, grep, chunk)
Phase 3: Sub-agent tools (sub_query)

Usage:
    python server.py              # Run with stdio (for Claude Code)
    python server.py --http       # Run with HTTP (for testing)
"""

from mcp.server.fastmcp import FastMCP
from tools.memory import remember, recall, forget, memory_status

# Initialize the MCP server
mcp = FastMCP("RLM Server")


# =============================================================================
# MEMORY TOOLS
# =============================================================================

@mcp.tool()
def rlm_remember(
    content: str,
    category: str = "general",
    importance: str = "medium",
    tags: str = ""
) -> str:
    """
    Save an important insight to persistent memory.

    Use this to remember key decisions, facts, user preferences, or technical
    findings that should be preserved across the conversation.

    Args:
        content: The insight or fact to remember (be concise but complete)
        category: Type of insight - one of: decision, fact, preference, finding, todo, general
        importance: Priority level - one of: low, medium, high, critical
        tags: Comma-separated keywords for easier retrieval (e.g., "odoo,bug,migration")

    Returns:
        Confirmation with insight ID
    """
    tags_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    result = remember(content, category, importance, tags_list)
    return f"✓ {result['message']} (total: {result['total_insights']})"


@mcp.tool()
def rlm_recall(
    query: str = "",
    category: str = "",
    importance: str = "",
    limit: int = 10
) -> str:
    """
    Retrieve insights from memory.

    Use this to find information discussed earlier, review decisions,
    check user preferences, or get context before answering questions.

    Args:
        query: Search term to filter insights (searches in content and tags)
        category: Filter by type - one of: decision, fact, preference, finding, todo, general
        importance: Filter by priority - one of: low, medium, high, critical
        limit: Maximum number of insights to return (default: 10)

    Returns:
        List of matching insights with their details
    """
    result = recall(
        query=query if query else None,
        category=category if category else None,
        importance=importance if importance else None,
        limit=limit
    )

    if result["count"] == 0:
        return f"No insights found. Total in memory: {result['total_in_memory']}"

    output_lines = [f"Found {result['count']} insights (total: {result['total_in_memory']}):\n"]

    for i, insight in enumerate(result["insights"], 1):
        tags_str = f" [{', '.join(insight['tags'])}]" if insight.get("tags") else ""
        output_lines.append(
            f"{i}. [{insight['id']}] ({insight['category']}/{insight['importance']}){tags_str}\n"
            f"   {insight['content']}\n"
            f"   — {insight['created_at'][:16]}"
        )

    return "\n\n".join(output_lines)


@mcp.tool()
def rlm_forget(insight_id: str) -> str:
    """
    Remove an insight from memory.

    Args:
        insight_id: The ID of the insight to remove (8-character hex)

    Returns:
        Confirmation of removal
    """
    result = forget(insight_id)
    if result["status"] == "not_found":
        return f"✗ {result['message']}"
    return f"✓ {result['message']} ({result['remaining_insights']} remaining)"


@mcp.tool()
def rlm_status() -> str:
    """
    Get current status of the RLM memory system.

    Returns statistics about stored insights, categories, and importance levels.
    """
    result = memory_status()

    categories_str = ", ".join(f"{k}: {v}" for k, v in result["by_category"].items()) or "none"
    importance_str = ", ".join(f"{k}: {v}" for k, v in result["by_importance"].items()) or "none"

    return (
        f"RLM Memory Status (v{result['version']})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Total insights: {result['total_insights']}\n"
        f"By category: {categories_str}\n"
        f"By importance: {importance_str}\n"
        f"Created: {result['created_at'][:16] if result['created_at'] else 'N/A'}\n"
        f"Last updated: {result['last_updated'][:16] if result['last_updated'] else 'never'}"
    )


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys

    if "--http" in sys.argv:
        # HTTP mode for testing
        mcp.run(transport="streamable-http")
    else:
        # Default: stdio for Claude Code
        mcp.run()
