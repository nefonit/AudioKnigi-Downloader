from __future__ import annotations

"""Non-UI topic-selection logic for Help Center actions."""

from .help_content import ROUND55_TOPIC_DETAILS


def resolve_help_topic(language, topic_data, row):
    """Return the selected title and full topic body, or None for invalid rows.

    Preserves the existing details lookup, trailing whitespace removal and
    double-newline separator without importing or manipulating Qt widgets.
    """
    if not 0 <= row < len(topic_data):
        return None
    key, title, body = topic_data[row]
    detail = ROUND55_TOPIC_DETAILS.get(language, {}).get(key, "")
    if detail:
        body = body.rstrip() + "\n\n" + detail
    return title, body
