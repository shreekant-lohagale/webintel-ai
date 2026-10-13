
from datetime import datetime, timezone
from urllib.parse import urlsplit

import scrapy
from scrapy_playwright.page import PageMethod


class ArticleSpider(scrapy.Spider):
    name = "articles"

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 1.0,
        "DOWNLOAD_DELAY_JITTER": 0,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1.0,
        "AUTOTHROTTLE_MAX_DELAY": 10.0,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,
        "DOWNLOAD_TIMEOUT": 20,
        "DOWNLOAD_MAXSIZE": 2 * 1024 * 1024,
        "REDIRECT_ENABLED": False,
        "CLOSESPIDER_PAGECOUNT": 10,
        "ITEM_PIPELINES": {},
        "LOG_LEVEL": "INFO",
    }

    def __init__(
        self,
        start_url=None,
        browser="0",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        if not start_url:
            raise ValueError("start_url is required")

        parts = urlsplit(start_url)

        if parts.scheme not in ("http", "https"):
            raise ValueError("Only HTTP/HTTPS is supported")

        if not parts.hostname:
            raise ValueError("Invalid start URL")

        if parts.username or parts.password:
            raise ValueError("Credentials in URLs are not supported")

        self.start_url = start_url
        self.origin = (
            parts.scheme.lower(),
            parts.hostname.lower(),
            parts.port,
        )

        self.allowed_domains = [parts.hostname]

        if browser not in ("0", "1"):
            raise ValueError("browser must be 0 or 1")

        self.use_browser = browser == "1"

    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)

        # Configured at spider scope so the existing
        # dynamic_quotes spider is not modified.
        #
        # Scrapy-playwright requires both handlers
        # on Windows for the working project setup.
        if settings.getbool("WEBINTEL_ARTICLE_BROWSER", False):
            settings.set(
                "DOWNLOAD_HANDLERS",
                {
                    "http":
                        "scrapy_playwright.handler."
                        "ScrapyPlaywrightDownloadHandler",
                    "https":
                        "scrapy_playwright.handler."
                        "ScrapyPlaywrightDownloadHandler",
                },
                priority="spider",
            )
            settings.set(
                "TWISTED_REACTOR",
                "twisted.internet.asyncioreactor."
                "AsyncioSelectorReactor",
                priority="spider",
            )
            settings.set(
                "PLAYWRIGHT_BROWSER_TYPE",
                "chromium",
                priority="spider",
            )

    def in_scope(self, url):
        parts = urlsplit(url)

        return (
            (
                parts.scheme.lower(),
                (parts.hostname or "").lower(),
                parts.port,
            ) == self.origin
            and not parts.username
            and not parts.password
        )


    def request_meta(self, selector="article"):
        if not self.use_browser:
            return {}

        return {
            "playwright": True,
            "playwright_page_methods": [
                PageMethod(
                    "wait_for_selector",
                    selector,
                    timeout=12000,
                )
            ],
        }

        if not self.use_browser:
            return {}

        return {
            "playwright": True,
            "playwright_page_methods": [
                PageMethod(
                    "wait_for_selector",
                    "article",
                    timeout=12000,
                )
            ],
        }

    async def start(self):
        yield scrapy.Request(
            self.start_url,
            callback=self.parse_index,
            meta=self.request_meta('a[href*="/articles/"]'),
            errback=self.log_failure,
        )

    def parse_index(self, response):
        if response.status != 200:
            self.logger.warning(
                "Index returned HTTP %s",
                response.status,
            )
            return

        links = response.css(
            'a[href*="/articles/"]::attr(href)'
        ).getall()

        for href in links:
            url = response.urljoin(href)

            if not self.in_scope(url):
                continue

            yield scrapy.Request(
                url,
                callback=self.parse_article,
                meta=self.request_meta(),
                errback=self.log_failure,
            )

    def parse_article(self, response):
        if response.status != 200:
            return

        # This is a site-specific selector-based extractor.
        # Other publishers will need extractor adapters.
        article = response.css("article")

        if not article:
            self.logger.warning(
                "Missing article element: %s",
                response.url,
            )
            return

        title = article.css("h1::text").get()

        paragraphs = article.css(
            ".article-body p::text"
        ).getall()

        content = " ".join(
            paragraph.strip()
            for paragraph in paragraphs
            if paragraph.strip()
        )

        if not title or not content:
            self.logger.warning(
                "Missing article title/content: %s",
                response.url,
            )
            return

        author = response.css(
            'meta[name="author"]::attr(content)'
        ).get()

        keywords = response.css(
            'meta[name="keywords"]::attr(content)'
        ).get() or ""

        published_at = article.css(
            "time::attr(datetime)"
        ).get()

        yield {
            "title": title,
            "content": content,
            "source_url": response.url,
            "author": author,
            "tags": [
                tag.strip()
                for tag in keywords.split(",")
                if tag.strip()
            ],
            "published_at": published_at,
            "scraped_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

    def log_failure(self, failure):
        self.logger.error(
            "Article request failed: %s",
            failure.value,
        )
