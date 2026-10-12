
import json
from pathlib import Path

import pytest
from scrapy.http import HtmlResponse, Request
from scrapy.exceptions import DropItem

from app.scrapers.scrapy_crawler.pipelines import (
    CleanQuotePipeline,
)
from app.scrapers.scrapy_crawler.spiders.dynamic_quotes_spider import (
    DynamicQuotesSpider,
)


DATA_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "raw"
    / "dynamic_quotes.json"
)


def test_spider_extracts_rendered_html():
    html = """
    <html>
      <body>
        <div class="quote">
          <span class="text">Hello from JavaScript</span>
          <small class="author">Test Author</small>
          <div class="tags">
            <a class="tag">technology</a>
          </div>
        </div>
      </body>
    </html>
    """

    url = "https://quotes.toscrape.com/js/"

    response = HtmlResponse(
        url=url,
        body=html.encode("utf-8"),
        encoding="utf-8",
        request=Request(url),
    )

    spider = DynamicQuotesSpider()
    items = list(spider.parse(response))

    assert len(items) == 1
    assert items[0]["text"] == "Hello from JavaScript"
    assert items[0]["author"] == "Test Author"
    assert items[0]["tags"] == ["technology"]
    assert items[0]["rendering_engine"] == "playwright"


def test_pipeline_cleans_whitespace():
    pipeline = CleanQuotePipeline()

    item = {
        "text": "  Hello   world  ",
        "author": "  Test   Author ",
        "tags": ["ai", "ai", "python"],
    }

    cleaned = pipeline.process_item(item)

    assert cleaned["text"] == "Hello world"
    assert cleaned["author"] == "Test Author"
    assert cleaned["tags"] == ["ai", "python"]


def test_pipeline_rejects_empty_records():
    pipeline = CleanQuotePipeline()

    with pytest.raises(DropItem):
        pipeline.process_item({
            "text": "",
            "author": "Test Author",
            "tags": [],
        })


def test_exported_json():
    if not DATA_FILE.exists():
        pytest.skip("Run the Playwright crawl before this test.")

    with DATA_FILE.open("r", encoding="utf-8") as file:
        records = json.load(file)

    assert isinstance(records, list)
    assert len(records) > 0

    for record in records:
        assert record["text"]
        assert record["author"]
        assert isinstance(record["tags"], list)
        assert record["rendering_engine"] == "playwright"

    unique_records = {
        (record["text"], record["author"])
        for record in records
    }

    assert len(unique_records) == len(records)
