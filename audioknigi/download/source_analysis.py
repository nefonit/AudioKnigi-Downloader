from __future__ import annotations

from ..core import Cancelled
from ..logging_utils import app_logger
from ..providers import provider_for_key
from ..services.book_analysis_service import AnalysisOptions, BookAnalysisService
from ..knigavuhe import search as search_knigavuhe_books


class SourceAnalysisMixin:
    """Provider-backed source analysis used by the downloader facade."""

    def _knigavuhe_fallback_candidate(self, book):
        """Find the same title/author/narrator on knigavuhe.org."""
        title_hint, author_hint, narrator_hint = self._book_identity_hints(book)
        title_tokens = set(self._identity_tokens(title_hint))
        author_tokens = set(self._identity_tokens(author_hint))
        narrator_tokens = set(self._identity_tokens(narrator_hint))
        if not title_tokens:
            return None

        cancel_event = getattr(self, "cancel_event", None)
        try:
            results = list(search_knigavuhe_books(title_hint, cancel_event=cancel_event) or [])
        except Cancelled:
            raise
        except Exception:
            app_logger.debug("Knigavuhe fallback search failed", exc_info=True)
            return None

        candidates = []
        for result in results:
            result_title = set(self._identity_tokens(getattr(result, "title", "")))
            if not result_title:
                continue
            title_overlap = len(title_tokens & result_title) / max(1, len(title_tokens | result_title))
            if title_overlap < 0.60 and not (title_tokens <= result_title or result_title <= title_tokens):
                continue

            score = 6.0 + 4.0 * title_overlap
            result_author = set(self._identity_tokens(getattr(result, "author", "")))
            if author_tokens and result_author:
                author_overlap = len(author_tokens & result_author) / max(1, len(author_tokens | result_author))
                if author_overlap < 0.50:
                    continue
                score += 4.0 * author_overlap

            variants = [(getattr(result, "url", ""), getattr(result, "narrator", ""))]
            for variant in list(getattr(result, "narration_variants", []) or []):
                variants.append((getattr(variant, "url", ""), getattr(variant, "narrator", "")))
            seen_urls = set()
            for candidate_url, candidate_narrator in variants:
                candidate_url = str(candidate_url or "").strip()
                if not candidate_url or candidate_url in seen_urls:
                    continue
                seen_urls.add(candidate_url)
                candidate_score = score
                cand_narrator_tokens = set(self._identity_tokens(candidate_narrator))
                if narrator_tokens and cand_narrator_tokens:
                    narrator_overlap = len(narrator_tokens & cand_narrator_tokens) / max(1, len(narrator_tokens | cand_narrator_tokens))
                    if narrator_overlap >= 0.50:
                        candidate_score += 5.0 * narrator_overlap
                    else:
                        candidate_score -= 2.0
                candidates.append((candidate_score, candidate_url))

        for _score, candidate_url in sorted(candidates, reverse=True)[:8]:
            self._check_cancel()
            try:
                fallback = provider_for_key("knigavuhe").fetch_book(candidate_url, cancel_event=cancel_event)
            except Cancelled:
                raise
            except Exception:
                continue
            fallback_title, fallback_author, fallback_narrator = self._book_identity_hints(fallback)
            fb_title_tokens = set(self._identity_tokens(fallback_title))
            if not fb_title_tokens:
                continue
            title_overlap = len(title_tokens & fb_title_tokens) / max(1, len(title_tokens | fb_title_tokens))
            if title_overlap < 0.60 and not (title_tokens <= fb_title_tokens or fb_title_tokens <= title_tokens):
                continue
            fb_author_tokens = set(self._identity_tokens(fallback_author))
            if author_tokens and fb_author_tokens:
                author_overlap = len(author_tokens & fb_author_tokens) / max(1, len(author_tokens | fb_author_tokens))
                if author_overlap < 0.50:
                    continue
            fb_narrator_tokens = set(self._identity_tokens(fallback_narrator))
            if narrator_tokens and fb_narrator_tokens:
                narrator_overlap = len(narrator_tokens & fb_narrator_tokens) / max(1, len(narrator_tokens | fb_narrator_tokens))
                if narrator_overlap < 0.40:
                    continue
            return fallback
        return None

    def _service(self) -> BookAnalysisService:
        return BookAnalysisService(
            cancel_event=getattr(self, "cancel_event", None),
            progress=self.log,
            options=AnalysisOptions(
                playwright_fallback_enabled=bool(
                    getattr(self, "runtime_playwright_fallback_enabled", True)
                ),
                fetch_cover=True,
                fetch_remote_size=True,
            ),
        )

    @staticmethod
    def _looks_like_protection(html_text, status_code):
        return BookAnalysisService._looks_like_protection(html_text, status_code)

    def _analyze_book_requests(self, url):
        """Compatibility hook backed by the shared analyzer implementation."""
        return self._service()._analyze_audioknigi_requests(url)

    def _analyze_book_playwright(self, url, primary_error=None):
        """Compatibility hook backed by the shared analyzer implementation."""
        return self._service()._analyze_audioknigi_playwright(url, primary_error)

    def _recover_short_audioknigi_source(self, book):
        """Compatibility hook backed by the shared analyzer implementation."""
        return self._service()._recover_short_audioknigi_source(book)

    def _analyze_book(self, url):
        """Analyze through the shared service, preserving subclass test hooks.

        Production uses one implementation in :class:`BookAnalysisService`.  A
        small compatibility path remains only when a subclass overrides the
        historic request/recovery hooks used by external tests/hosts.
        """
        self._check_cancel()
        cls = type(self)
        custom_hooks = (
            getattr(cls, "_analyze_book_requests", None) is not SourceAnalysisMixin._analyze_book_requests
            or getattr(cls, "_recover_short_audioknigi_source", None) is not SourceAnalysisMixin._recover_short_audioknigi_source
            or getattr(cls, "_analyze_book_playwright", None) is not SourceAnalysisMixin._analyze_book_playwright
        )
        if not custom_hooks:
            book = self._service().analyze(url)
            self._check_cancel()
            return book

        primary_error = None
        try:
            book = self._analyze_book_requests(url)
        except Cancelled:
            raise
        except Exception as exc:
            primary_error = exc
        if primary_error is not None:
            if not bool(getattr(self, "runtime_playwright_fallback_enabled", True)):
                raise primary_error
            book = self._analyze_book_playwright(url, primary_error)
        # Recovery errors are semantic media errors, not HTTP parse failures, so
        # they must never trigger Playwright a second time.
        return self._recover_short_audioknigi_source(book)
