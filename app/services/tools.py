from typing import Optional


def execute_tool(tool_name: str, prompt: str, retrieval_results: list[dict]) -> Optional[str]:
    if tool_name == "search_docs":
        titles = ", ".join([d["title"] for d in retrieval_results[:3]])
        return f"Search results surfaced: {titles}" if titles else "No search results were found."
    if tool_name == "ticket_lookup":
        return "Ticket lookup adapter returned 2 matching operational tickets."
    if tool_name == "system_summary":
        return "System summary adapter inspected accessible documents and generated a bounded overview."
    if tool_name == "finance_export":
        return "Finance export adapter prepared a privileged export package."
    return None
