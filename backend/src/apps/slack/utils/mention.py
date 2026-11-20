"""Slack app mention event helpers."""

import re

USER_MENTION_PATTERN = re.compile(r"<@[UW][A-Z0-9]+(?:\|[^>]*)?>")


def get_query(event: dict) -> str:
    """Return the question asked in an app mention event, without user mentions."""
    query = " ".join(get_rich_text(event.get("blocks", [])).split())
    if query:
        return query

    return " ".join(USER_MENTION_PATTERN.sub("", event.get("text", "")).split())


def get_rich_text(elements: list) -> str:
    """Return the text and links of nested rich text elements, skipping everything else."""
    parts = []
    for element in elements:
        match element.get("type"):
            case "text":
                parts.append(element.get("text", ""))
            case "link":
                url = element.get("url", "")
                label = element.get("text")
                is_url_label = element.get("truncated") or (
                    label and label.rstrip("/") == url.split("://", 1)[-1].rstrip("/")
                )
                parts.append(f"{label} ({url})" if label and not is_url_label else url)
            case _ if nested := element.get("elements"):
                parts.append(f"{get_rich_text(nested)}\n")
    return "".join(parts)
