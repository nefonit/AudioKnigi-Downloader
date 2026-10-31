"""Local ranking of heterogeneous catalogue results, without network lookups.

Provider search engines may search descriptions, sidebars, or recommendations.
Only the visible book title/author/narrator is verified locally. A nonmatch is
*uncertain*, not necessarily irrelevant: anthology contents may not be present
in the result's short metadata. Such rows can be revealed separately in the UI.
"""
from __future__ import annotations

from difflib import SequenceMatcher
import re
import unicodedata

from ..models import SearchResult

_WORDS = re.compile(r"[^\W_]+", re.UNICODE)
_STOP = frozenset({"аудиокнига", "аудиокниги", "слушать", "онлайн", "book", "audiobook"})
# Frequent non-literal renderings of names are explicit rather than allowing
# broad edit-distance guesses that would bring irrelevant books back.
_NAME_ALIASES = {
    "harry": "garri", "гарри": "garri",
    "hermione": "germiona", "гермиона": "germiona",
    "christie": "kristi", "кристи": "kristi",
    "arthur": "artur", "артур": "artur",
}
_CYRILLIC = {
    "а":"a", "б":"b", "в":"v", "г":"g", "д":"d", "е":"e", "ё":"yo",
    "ж":"zh", "з":"z", "и":"i", "й":"y", "к":"k", "л":"l", "м":"m",
    "н":"n", "о":"o", "п":"p", "р":"r", "с":"s", "т":"t", "у":"u",
    "ф":"f", "х":"h", "ц":"ts", "ч":"ch", "ш":"sh", "щ":"shch",
    "ъ":"", "ы":"y", "ь":"", "э":"e", "ю":"yu", "я":"ya",
    "і":"i", "ї":"yi", "є":"ye", "ґ":"g",
}


def _normalize(text: str) -> str:
    text = str(text or "").casefold().replace("ё", "е")
    # Strip accent marks on Latin names, but preserve Cyrillic letters that
    # NFKD decomposes (й -> и + breve, ї -> і + diaeresis).
    decomposed = unicodedata.normalize("NFKD", text)
    decomposed = decomposed.replace("и\u0306", "й").replace("і\u0308", "ї")
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def _tokens(text: str) -> list[str]:
    return [t for t in _WORDS.findall(_normalize(text)) if t not in _STOP]


def _latin(token: str) -> str:
    return "".join(_CYRILLIC.get(ch, ch) for ch in token)


def _matching_token(wanted: str, candidate: str) -> bool:
    if wanted == candidate:
        return True
    if _NAME_ALIASES.get(wanted, wanted) == _NAME_ALIASES.get(candidate, candidate):
        return True
    if min(len(wanted), len(candidate)) >= 4 and (
        wanted.startswith(candidate) or candidate.startswith(wanted)
    ):
        return True
    # A Cyrillic-to-Latin match needs romanization before comparison.
    # Do not fuzzy-match two same-script words: 'Сон' and 'Слон' are different.
    if _latin(wanted) == wanted and _latin(candidate) == candidate:
        return False
    left, right = _latin(wanted), _latin(candidate)
    if left == right:
        return True
    # Latinized tokens can also use known spelling aliases (English Harry
    # versus Russian Гарри). Use only exact aliases, not broad fuzzy spellcheck.
    if _NAME_ALIASES.get(left, left) == _NAME_ALIASES.get(right, right):
        return True
    # Common transliteration differences: 'sherlock' / 'шерлок' and
    # 'holmes' / 'холмс'. Tolerate a single missing letter only after
    # transliteration, never a short/generic partial word.
    if min(len(left), len(right)) >= 5 and abs(len(left) - len(right)) <= 1:
        if left[:2] == right[:2] and SequenceMatcher(None, left, right).ratio() >= .85:
            return True
    return False


def _all_query_tokens_match(query: list[str], content: list[str]) -> bool:
    return bool(query and content) and all(
        any(_matching_token(token, word) for word in content) for token in query
    )


def search_relevance_rank(query: str, item: SearchResult) -> int:
    """0-3 verified relevance; 4 = possible match only (e.g. a story in an anthology).

    Matching the title is the preferred evidence; an author/narrator search is
    also valid. Do not infer full-text relevance from a provider's broad output.
    """
    wanted = _tokens(query)
    if not wanted:
        return 0
    title = _tokens(getattr(item, "title", ""))
    author = _tokens(getattr(item, "author", ""))
    narrator = _tokens(getattr(item, "narrator", ""))
    if _all_query_tokens_match(wanted, title):
        # Full book title match beats author-only or mixed-field matches.
        if len(wanted) == len(title) and all(_matching_token(x, y) for x, y in zip(wanted, title)):
            return 0
        return 1
    if _all_query_tokens_match(wanted, author) or _all_query_tokens_match(wanted, narrator):
        return 2
    if _all_query_tokens_match(wanted, title + author + narrator):
        return 3
    return 4


def search_relevance_sort_key(query: str, item: SearchResult):
    rank = search_relevance_rank(query, item)
    title = " ".join(_tokens(getattr(item, "title", "")))
    # Within equally relevant hits, shorter titles are usually more direct.
    return rank, len(title.split()), title


__all__ = ["search_relevance_rank", "search_relevance_sort_key"]
