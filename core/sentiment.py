"""Sentiment analysis service."""

import re
from typing import List, Tuple

from models import ChangelogEntry, EntryType, Gitmoji

GITMOJI_PATTERNS = {
    Gitmoji.SPARKLES: r"new|feature|idea|created|inspired|achievement",
    Gitmoji.BUG: r"bug|issue|problem|error|fix|solved",
    Gitmoji.BOOM: r"change|transform|pivot|shift|overhaul",
    Gitmoji.ROCKET: r"improve|faster|better|upgrade|progress",
    Gitmoji.MEMO: r"note|document|journal|reflect|think",
    Gitmoji.BULB: r"idea|thought|solution|concept|innovation",
    Gitmoji.HEART: r"love|thank|grateful|appreciate|happy",
    Gitmoji.ZAP: r"energy|power|motivation|drive|focus",
    Gitmoji.TADA: r"celebrate|finished|completed|victory|success",
    Gitmoji.FIRE: r"remove|delete|eliminate|stop|end",
    Gitmoji.LOCK: r"secure|private|protect|safe|careful",
    Gitmoji.CONSTRUCTION: r"work|progress|building|developing|creating",
    Gitmoji.RECYCLE: r"routine|repeat|habit|cycle|pattern",
    Gitmoji.WRENCH: r"adjust|configure|setup|organize|maintain",
    Gitmoji.BRAIN: r"mental|mind|thought|learn|understand|stress",
    Gitmoji.EYES: r"watch|observe|notice|see|look|discover",
}

# Default gitmojis for entry types
DEFAULT_GITMOJIS = {
    EntryType.HIGHLIGHT: Gitmoji.SPARKLES,
    EntryType.BUG: Gitmoji.BUG,
    EntryType.REFLECTION: Gitmoji.MEMO,
}


def analyze_content(entry: ChangelogEntry) -> List[Gitmoji]:
    """
    Analyze entry content and assign gitmojis.

    Parameters
    ----------
    entry : ChangelogEntry
        Entry to analyze

    Returns
    -------
    List[Gitmoji]
        List of assigned gitmojis
    """
    content = entry.content.lower()
    gitmojis = []

    default_gitmoji = DEFAULT_GITMOJIS.get(entry.entry_type)
    if default_gitmoji:
        gitmojis.append(default_gitmoji)

    for gitmoji, pattern in GITMOJI_PATTERNS.items():
        if re.search(pattern, content, re.IGNORECASE) and gitmoji not in gitmojis:
            gitmojis.append(gitmoji)

    return gitmojis[:3]


# TODO: Replace with actual sentiment analysis API call
def get_sentiment_score(text: str) -> float:
    """
    Get sentiment score for text.

    In a real implementation, this would call an external API like OpenAI.
    For demo purposes, this is a simple keyword-based implementation.

    Parameters
    ----------
    text : str
        Text to analyze

    Returns
    -------
    float
        Sentiment score between -1 (negative) and 1 (positive)
    """
    positive_words = [
        "great", "good", "happy", "joy", "excellent", "positive",
        "success", "win", "accomplish", "achieve", "grateful", "thankful",
        "excited", "love", "amazing", "wonderful", "progress", "improve"
    ]

    negative_words = [
        "bad", "sad", "unhappy", "disappointed", "negative", "fail",
        "problem", "issue", "struggle", "difficult", "hard", "worried",
        "stress", "anxiety", "frustrate", "annoyed", "angry", "tired"
    ]

    text = text.lower()

    pos_count = sum(1 for word in positive_words if word in text)
    neg_count = sum(1 for word in negative_words if word in text)

    total = pos_count + neg_count
    if total == 0:
        return 0

    return (pos_count - neg_count) / total  # Range -1 to 1


def enrich_entry(entry: ChangelogEntry) -> ChangelogEntry:
    """
    Enrich an entry with sentiment analysis and gitmojis.

    Parameters
    ----------
    entry : ChangelogEntry
        Entry to enrich

    Returns
    -------
    ChangelogEntry
        Enriched entry
    """
    if entry.sentiment_score is None:
        entry.sentiment_score = get_sentiment_score(entry.content)

    if not entry.gitmojis:
        entry.gitmojis = analyze_content(entry)

    return entry
