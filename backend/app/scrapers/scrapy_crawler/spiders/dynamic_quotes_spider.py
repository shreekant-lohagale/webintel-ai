
from datetime import datetime, timezone

import scrapy
from scrapy_playwright.page import PageMethod


class DynamicQuotesSpider(scrapy.Spider):
    name = "dynamic_quotes"

    allowed_domains = ["quotes.toscrape.com"]

    start_urls = ["https://quotes.toscrape.com/js/"]

    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": (
                "scrapy_playwright.handler."
                "ScrapyPlaywrightDownloadHandler"
            ),
            "https": (
                "scrapy_playwright.handler."
                "ScrapyPlaywrightDownloadHandler"
            ),
        },
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "PLAYWRIGHT_MAX_PAGES_PER_CONTEXT": 2,
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 20000,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "ROBOTSTXT_OBEY": True,
        "RETRY_TIMES": 1,
        "CLOSESPIDER_PAGECOUNT": 2,
    }

    async def start(self):
        """Schedule the JavaScript-rendered page."""

        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod(
                            "wait_for_selector",
                            "div.quote",
                            timeout=15000,
                        )
                    ],
                },
            )

    def parse(self, response):
        """Extract quotes from rendered HTML."""

        self.logger.info(
            "Rendered page: %s",
            response.url,
        )

        quotes = response.css("div.quote")

        self.logger.info(
            "Found %d rendered quotes",
            len(quotes),
        )

        for quote in quotes:
            yield {
                "text": quote.css(
                    "span.text::text"
                ).get(),

                "author": quote.css(
                    "small.author::text"
                ).get(),

                "tags": quote.css(
                    "div.tags a.tag::text"
                ).getall(),

                "source_url": response.url,

                "scraped_at": datetime.now(
                    timezone.utc
                ).isoformat(),

                "rendering_engine": "playwright",
            }
