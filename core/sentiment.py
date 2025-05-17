"""Sentiment analysis service."""

import re
from typing import List

from models import ChangelogEntry, EntryType, Gitmoji
import nltk


GITMOJI_PATTERNS = {
    Gitmoji.SPARKLES: r"new|feature|idea|created|inspired|achievement|innovation|launch|debut|unveiled|introduce|breakthrough|novel|original",
    Gitmoji.BUG: r"bug|issue|problem|error|fix|solved|defect|glitch|trouble|malfunction|failure|resolved|debugging|patch|repair|corrected",
    Gitmoji.BOOM: r"change|transform|pivot|shift|overhaul|revamp|redesign|convert|transition|restructure|revolution|fundamental|reshape|alter",
    Gitmoji.ROCKET: r"improve|faster|better|upgrade|progress|enhance|optimize|boost|accelerate|efficiency|performance|streamline|speed|advance",
    Gitmoji.MEMO: r"note|document|journal|reflect|think|record|log|diary|write|transcript|minutes|notation|reminder|chronicle|archive|paper",
    Gitmoji.BULB: r"idea|thought|solution|concept|innovation|insight|inspiration|creative|brainstorm|vision|imagine|discover|clever|brilliant",
    Gitmoji.HEART: r"love|thank|grateful|appreciate|happy|adore|cherish|admire|fond|enjoy|delight|pleasure|devoted|affection|thankful|caring|mom|mother|family|care|support",
    Gitmoji.ZAP: r"energy|power|motivation|drive|focus|spark|intensity|force|vigor|strength|momentum|vitality|dynamic|impulse|enthusiasm",
    Gitmoji.TADA: r"celebrate|celebration|party|award|achievement|accomplishment|milestone|victory|win|championship|promotion|success|congratulations|graduated|honor",
    Gitmoji.FIRE: r"remove|delete|eliminate|stop|end|terminate|cancel|discard|abolish|discontinue|cease|halt|erase|destroy|purge|extinguish",
    Gitmoji.LOCK: r"secure|private|protect|safe|careful|guard|shield|defend|encrypt|confidential|safeguard|privacy|restrict|classified|caution",
    Gitmoji.CONSTRUCTION: r"work|progress|building|developing|creating|construct|fabricate|assemble|form|craft|establish|setup|prepare|foundation",
    Gitmoji.RECYCLE: r"routine|repeat|habit|cycle|pattern|loop|reuse|circular|recurring|regular|systematic|continual|periodic|iterative|constant",
    Gitmoji.WRENCH: r"adjust|configure|setup|organize|maintain|tune|calibrate|modify|tweak|customize|tool|fix|repair|arrangement|adapt|arrange",
    Gitmoji.BRAIN: r"mental|mind|thought|learn|understand|stress|cognitive|intellect|knowledge|wisdom|comprehend|intelligence|study|memory|think",
    Gitmoji.EYES: r"watch|observe|notice|see|look|discover|witness|perceive|spot|detect|view|monitor|inspect|examine|surveillance|recognize",
    Gitmoji.DIZZY: r"confused|dizzy|overwhelmed|disoriented|complicated|complex|challenging|difficult|puzzling|bewildered|lost|perplexed",
    Gitmoji.CHART: r"data|metrics|statistics|analyze|measurement|graph|trend|track|monitor|evaluate|assess|report|quantify|numbers|figures",
    Gitmoji.SEEDLING: r"grow|begin|start|initial|early|seed|embryonic|nascent|budding|emerging|sprouting|developing|young|commence|genesis",
    Gitmoji.GLOBE: r"world|global|international|earth|planet|worldwide|universal|abroad|foreign|everywhere|geographic|travel|culture|space",
    Gitmoji.ART: r"creative|design|artistic|beautiful|aesthetic|craft|style|visual|drawing|painting|illustration|composition|artwork|expressive",
    Gitmoji.BOOKMARK: r"save|remember|important|reference|bookmark|mark|highlight|notable|significant|key|crucial|essential|vital|critical",
    Gitmoji.HOURGLASS: r"time|wait|deadline|duration|period|schedule|patience|delay|temporary|timing|countdown|interval|pending|awaiting",
    Gitmoji.MUSCLE: r"strength|effort|hard|difficult|struggle|powerful|force|exertion|strenuous|tough|determined|persistence|resilience",
    Gitmoji.MONEY: r"finance|cost|expense|budget|payment|money|financial|economic|invest|fund|profit|income|revenue|cash|saving|price",
}

SERIOUS_CONTEXT_WORDS = [
    r"mom|mother|dad|father|parent|family|passed away|died|death|illness|sick|hospital|grave|funeral|cancer|disease",
    r"love you|miss you|remembering|memory|memories|never forget|always remember|thinking of you|in my heart",
    r"sincere|deep|heartfelt|sorrow|grief|mourn|regret|sympathy|condolence|prayer|blessing|sacred|spiritual",
    r"anniversary|birthday|wedding|graduation|retirement|milestone|special day|important occasion"
]

CELEBRATORY_CONTEXT_WORDS = [
    r"party|celebrate|festival|award|prize|won|congratulation|cheer|hooray|yay|woohoo|awesome|amazing",
    r"birthday party|graduation ceremony|wedding celebration|promotion party|launch event|grand opening"
]

DEFAULT_GITMOJIS = {
    EntryType.HIGHLIGHT: Gitmoji.SPARKLES,
    EntryType.BUG: Gitmoji.BUG,
    EntryType.REFLECTION: Gitmoji.MEMO,
    EntryType.INSIGHT: Gitmoji.BULB,
    EntryType.CHALLENGE: Gitmoji.MUSCLE,
    EntryType.PROGRESS: Gitmoji.ROCKET,
    EntryType.QUESTION: Gitmoji.DIZZY,
}



def analyze_content(entry: ChangelogEntry) -> List[Gitmoji]:
    """
    Analyze entry content and assign gitmojis with tone awareness.

    Parameters
    ----------
    entry : str
        Content to analyze

    Returns
    -------
    List[Gitmoji]
        List of assigned gitmojis
    """
    content = entry.content.lower()
    gitmojis = []

    # Check for contextual tone first
    is_serious = any(
        re.search(pattern, content, re.IGNORECASE) for pattern in SERIOUS_CONTEXT_WORDS
    )
    is_celebratory = any(
        re.search(pattern, content, re.IGNORECASE)
        for pattern in CELEBRATORY_CONTEXT_WORDS
    )

    # First pass: check all patterns
    for gitmoji, pattern in GITMOJI_PATTERNS.items():
        if re.search(pattern, content, re.IGNORECASE) and gitmoji not in gitmojis:
            # Apply tone-based filtering
            if is_serious and gitmoji == Gitmoji.TADA and not is_celebratory:
                # Skip TADA for serious contexts unless explicitly celebratory
                continue

            gitmojis.append(gitmoji)

    if Gitmoji.HEART in gitmojis:
        # For heartfelt messages, prioritize these combinations
        if re.search(r"mom|mother|dad|father|parent|family", content, re.IGNORECASE):
            # For family-related heartfelt messages, add SEEDLING for nurturing relationships
            if Gitmoji.SEEDLING not in gitmojis:
                gitmojis.append(Gitmoji.SEEDLING)

        if re.search(r"thank|grateful|appreciate", content, re.IGNORECASE):
            # For gratitude messages, don't add TADA unless explicitly celebratory
            if Gitmoji.TADA in gitmojis and not is_celebratory:
                gitmojis.remove(Gitmoji.TADA)


    # If no gitmojis were found, use default
    if len(gitmojis) == 0:
        gitmojis.append(DEFAULT_GITMOJIS.get(EntryType.HIGHLIGHT))

    return gitmojis[:3]  # Return up to 3 gitmojis


def get_sentiment_score(text: str) -> float:
    """
    Get sentiment score for text using Vader.

    Parameters
    ----------
    text : str
        Text to analyze

    Returns
    -------
    float
        Sentiment score between -1 (negative) and 1 (positive)
    """

    nltk.download("vader_lexicon")
    from nltk.sentiment.vader import SentimentIntensityAnalyzer

    analyzer = SentimentIntensityAnalyzer()

    scores = analyzer.polarity_scores(text)
    return scores["compound"]  # Range -1 to 1


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
