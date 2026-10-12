
import asyncio
import json
import logging

from scrapy.downloadermiddlewares.retry import get_retry_request
from twisted.internet.error import (
    ConnectionLost,
    ConnectionRefusedError,
    DNSLookupError,
    TCPTimedOutError,
    TimeoutError,
)

from app.scrapers.scrapy_crawler.reliability import (
    RETRYABLE_STATUSES,
    calculate_backoff,
)

logger = logging.getLogger("webintel.reliability")

NETWORK_ERRORS = (
    ConnectionLost,
    ConnectionRefusedError,
    DNSLookupError,
    TCPTimedOutError,
    TimeoutError,
    OSError,
)


def log_event(event, **fields):
    logger.info(
        "WEBINTEL_EVENT %s",
        json.dumps(
            {"event": event, **fields},
            ensure_ascii=False,
        ),
    )


class ResilientRetryMiddleware:

    def __init__(self, crawler):
        self.crawler = crawler
        self.max_retries = crawler.settings.getint(
            "RETRY_TIMES", 2
        )
        self.base_delay = crawler.settings.getfloat(
            "WEBINTEL_RETRY_BASE_DELAY", 1.0
        )
        self.max_delay = crawler.settings.getfloat(
            "WEBINTEL_RETRY_MAX_DELAY", 10.0
        )

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    async def retry_request(
        self, request, reason, retry_after=None
    ):
        if request.meta.get("dont_retry"):
            return None

        attempt = request.meta.get("retry_times", 0) + 1

        # Do not retry after the configured attempt limit.
        if attempt > self.max_retries:
            self.crawler.stats.inc_value(
                "webintel/retry_exhausted"
            )
            log_event(
                "retry_exhausted",
                url=request.url,
                reason=str(reason),
            )
            return None

        delay = calculate_backoff(
            attempt,
            self.base_delay,
            self.max_delay,
            retry_after,
        )

        if delay < 0:
            self.crawler.stats.inc_value(
                "webintel/retry_deferred"
            )
            log_event(
                "retry_deferred",
                url=request.url,
                reason=str(reason),
            )
            return None

        retry = get_retry_request(
            request,
            spider=self.crawler.spider,
            reason=str(reason),
            max_retry_times=self.max_retries,
            stats_base_key="webintel/retry",
        )

        if retry is None:
            return None

        self.crawler.stats.inc_value(
            "webintel/retry_scheduled"
        )

        log_event(
            "retry_scheduled",
            url=request.url,
            reason=str(reason),
            attempt=attempt,
            delay_seconds=delay,
        )

        await asyncio.sleep(delay)

        return retry

    async def process_response(self, request, response):
        if response.status not in RETRYABLE_STATUSES:
            return response

        header = response.headers.get(b"Retry-After")
        retry_after = (
            header.decode("utf-8", errors="replace")
            if header else None
        )

        retry = await self.retry_request(
            request,
            reason=f"http_{response.status}",
            retry_after=retry_after
            if response.status in (429, 503)
            else None,
        )

        return retry or response

    async def process_exception(self, request, exception):
        if not isinstance(exception, NETWORK_ERRORS):
            return None

        return await self.retry_request(
            request,
            reason=type(exception).__name__,
        )
