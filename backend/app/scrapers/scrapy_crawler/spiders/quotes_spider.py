
from datetime import datetime, timezone

import scrapy


class QuotesSpider(scrapy.Spider):
    name = "quotes"

    allowed_domains = ["quotes.toscrape.com"]

    start_urls = [
        "https://quotes.toscrape.com/"
    ]

    def parse(self, response):
        """Extract quotes and follow pagination links."""

        self.logger.info("Crawling: %s", response.url)

        # Extract every quote on the current page
        for quote in response.css("div.quote"):

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
                ).isoformat()
            }

        # Find the next page
        next_page = response.css(
            "li.next a::attr(href)"
        ).get()

        # Schedule another request if a next page exists
        if next_page:
            yield response.follow(
                next_page,
                callback=self.parse
            )
