from __future__ import annotations

"""GUI-independent multi-source search orchestration through SourceProvider."""

from dataclasses import dataclass, field, replace

from ..core import Cancelled, extract_extended_metadata_from_html, extract_metadata_from_html, get_http_session
from ..logging_utils import app_logger
from ..models import SearchResult
from ..providers import registered_providers
from ..providers.audioknigi_search import (
    SEARCH_URL,
    _audioknigi_page_metadata as _provider_audioknigi_page_metadata,
    parse_audioknigi_results,
    search_audioknigi,
)
from ..sources import normalize_supported_url


def _iter_completed_cancellable(futures, cancel_event=None):
    """Compatibility wrapper for archived regression suites."""
    from ..providers.audioknigi_search import _iter_completed_cancellable as implementation
    return implementation(futures, cancel_event)


def _matches_query(title: str, query: str, author: str = "", narrator: str = "") -> bool:
    """Compatibility wrapper for archived regression suites."""
    from ..providers.audioknigi_search import _matches_query as implementation
    return implementation(title, query, author=author, narrator=narrator)


@dataclass(slots=True)
class SearchOutcome:
    query: str
    results: list[SearchResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def source_count(self) -> int:
        return len({item.source for item in self.results if getattr(item, "source", "")})


def _audioknigi_page_metadata(result: SearchResult) -> SearchResult:
    """Compatibility wrapper around the provider-level metadata hydrator."""
    return _provider_audioknigi_page_metadata(
        result,
        session_factory=get_http_session,
        metadata_extractor=extract_metadata_from_html,
        extended_metadata_extractor=extract_extended_metadata_from_html,
    )


def search_all_sources(query: str, cancel_event=None, progress=None, sources=None) -> SearchOutcome:
    cleaned = str(query or "").strip()
    if len(cleaned) < 3:
        return SearchOutcome(cleaned, [], ["Введите минимум 3 символа для поиска."])

    def report(percent: int, message: str) -> None:
        if progress is None:
            return
        try:
            progress(max(0, min(100, int(percent))), str(message or ""))
        except Exception:
            app_logger.debug("Search progress callback failed", exc_info=True)

    report(5, "Поиск запущен")

    all_providers = registered_providers()
    requested = None if sources is None else {
        str(value).strip().casefold() for value in sources if str(value).strip()
    }
    providers = all_providers if requested is None else tuple(
        provider
        for provider in all_providers
        if provider.key.casefold() in requested or provider.display_name.casefold() in requested
    )
    if not providers:
        return SearchOutcome(cleaned, [], ["Выберите хотя бы один сайт для поиска."])

    results: list[SearchResult] = []
    errors: list[str] = []
    provider_count = max(1, len(providers))
    for provider_index, provider in enumerate(providers):
        if cancel_event is not None and cancel_event.is_set():
            raise Cancelled("Поиск отменён пользователем")
        stage_start = 8 + int((provider_index / provider_count) * 82)
        report(stage_start, f"Ищу на {provider.display_name}")
        try:
            provider_results = list(provider.search(cleaned, cancel_event=cancel_event) or [])
            provider_results = list(
                provider.enrich_search_results(provider_results, cancel_event=cancel_event) or []
            )
            results.extend(provider_results)
        except Cancelled:
            raise
        except Exception as exc:
            if cancel_event is not None and cancel_event.is_set():
                raise Cancelled("Поиск отменён пользователем") from exc
            app_logger.exception("Ошибка поискового провайдера %s", provider.display_name)
            errors.append(f"{provider.display_name}: {exc}")
        stage_end = 8 + int(((provider_index + 1) / provider_count) * 82)
        report(stage_end, f"Источник {provider.display_name} обработан")

    report(94, "Объединяю результаты")
    seen: set[str] = set()
    deduped: list[SearchResult] = []
    for result in results:
        if cancel_event is not None and cancel_event.is_set():
            raise Cancelled("Поиск отменён пользователем")
        canonical = normalize_supported_url(result.url) if result.url else ""
        identity = canonical or str(result.url or "").strip()
        if not identity or identity in seen:
            continue
        seen.add(identity)
        if canonical and result.url != canonical:
            result = replace(result, url=canonical)
        deduped.append(result)

    # 100% belongs to the GUI completion boundary, after SearchWorker has
    # actually returned and the modal operation dialog can be dismissed.
    # Reporting 100 here made a still-running worker look finished.
    report(99, "Завершаю поиск")
    return SearchOutcome(cleaned, deduped, errors)


__all__ = [
    "SEARCH_URL",
    "SearchOutcome",
    "parse_audioknigi_results",
    "search_audioknigi",
    "search_all_sources",
]
