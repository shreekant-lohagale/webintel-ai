
import json
from datetime import datetime, timezone

import scrapy


BASE_URL = "http://127.0.0.1:8765"

SCENARIOS = [
    "unstable",
    "limited",
    "blocked",
    "captcha",
    "always-error",
]


class ResilientSpider(scrapy.Spider):
    name = "resilient"

    allowed_domains = ["127.0.0.1"]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,

        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,

        "DOWNLOAD_DELAY": 0.5,
        "RANDOMIZE_DOWNLOAD_DELAY": False,

        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.5,
        "AUTOTHROTTLE_MAX_DELAY": 5.0,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,

        "RETRY_TIMES": 2,
        "WEBINTEL_RETRY_BASE_DELAY": 1.0,
        "WEBINTEL_RETRY_MAX_DELAY": 10.0,

        # Disable Scrapy's built-in RetryMiddleware.
        # Our custom middleware handles retries instead.
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
            "app.scrapers.scrapy_crawler.middlewares.ResilientRetryMiddleware": 550,
        },

        # This spider exports diagnostics, not quotes.
        "ITEM_PIPELINES": {},

        "DOWNLOAD_TIMEOUT": 10,
        "REDIRECT_ENABLED": False,
        "LOG_LEVEL": "INFO",
    }

    async def start(self):
        for scenario in SCENARIOS:
            yield scrapy.Request(
                url=f"{BASE_URL}/{scenario}",
                callback=self.parse,
                errback=self.handle_error,
                meta={
                    "scenario": scenario,
                    "handle_httpstatus_all": True,
                },
            )

    def log_event(self, event, **fields):
        self.logger.info(
            "WEBINTEL_EVENT %s",
            json.dumps(
                {"event": event, **fields},
                ensure_ascii=False,
            ),
        )

    def parse(self, response):
        scenario = response.meta["scenario"]
        status = response.status
        body = response.text.lower()

        if status in (401, 403):
            self.crawler.stats.inc_value("webintel/blocked")

            self.log_event(
                "blocked",
                scenario=scenario,
                status=status,
            )
            return

        if "captcha required" in body:
            self.crawler.stats.inc_value(
                "webintel/captcha_detected"
            )
            self.log_event(
                "captcha_detected",
                scenario=scenario,
            )
            return

        if status != 200:
            self.crawler.stats.inc_value("webintel/failed")
            self.log_event(
                "http_failure",
                scenario=scenario,
                status=status,
            )
            return

        title = response.css("h1::text").get()

        if not title:
            self.crawler.stats.inc_value(
                "webintel/invalid_content"
            )
            self.log_event(
                "invalid_content",
                scenario=scenario,
            )
            return

        self.crawler.stats.inc_value("webintel/success")

        self.log_event(
            "success",
            scenario=scenario,
            status=status,
        )

        yield {
            "scenario": scenario,
            "title": title.strip(),
            "source_url": response.url,
            "http_status": status,
            "scraped_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

    def handle_error(self, failure):
        self.crawler.stats.inc_value("webintel/failed")

        self.log_event(
            "request_failed",
            url=failure.request.url,
            reason=str(failure.value),
        )
