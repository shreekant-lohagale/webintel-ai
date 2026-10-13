
from scrapy.http import HtmlResponse, Request

from app.scrapers.scrapy_crawler.spiders.article_spider import (
    ArticleSpider,
)


def make_response(url, html):
    return HtmlResponse(
        url=url,
        request=Request(url),
        body=html.encode("utf-8"),
        encoding="utf-8",
    )


def test_article_extraction():
    spider = ArticleSpider(
        start_url="http://127.0.0.1:8766/"
    )

    html = """
    <html>
      <head>
        <meta name="author" content="Test Author">
        <meta name="keywords" content="AI, Python">
      </head>
      <body>
        <article>
          <h1>AI Article</h1>
          <time datetime="2026-10-13T08:00:00+00:00">
            Date
          </time>
          <div class="article-body">
            <p>First paragraph.</p>
            <p>Second paragraph.</p>
          </div>
        </article>
      </body>
    </html>
    """

    response = make_response(
        "http://127.0.0.1:8766/articles/ai",
        html,
    )

    records = list(spider.parse_article(response))

    assert len(records) == 1

    record = records[0]

    assert record["title"] == "AI Article"
    assert record["content"] == (
        "First paragraph. Second paragraph."
    )
    assert record["author"] == "Test Author"
    assert record["tags"] == ["AI", "Python"]
    assert record["published_at"] == (
        "2026-10-13T08:00:00+00:00"
    )


def test_missing_content_is_skipped():
    spider = ArticleSpider(
        start_url="http://127.0.0.1:8766/"
    )

    response = make_response(
        "http://127.0.0.1:8766/articles/empty",
        "<article><h1>Empty Article</h1></article>",
    )

    assert list(spider.parse_article(response)) == []


def test_same_origin_scope():
    spider = ArticleSpider(
        start_url="http://127.0.0.1:8766/"
    )

    assert spider.in_scope(
        "http://127.0.0.1:8766/articles/test"
    )

    assert not spider.in_scope(
        "https://example.com/articles/test"
    )

    assert not spider.in_scope(
        "http://127.0.0.1:8767/articles/test"
    )


def test_external_url_requires_opt_in():
    from app.pipeline.run import validate_start_url

    try:
        validate_start_url(
            "https://example.com/news"
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "External URL should have been rejected"
        )


def test_browser_flag():
    spider = ArticleSpider(
        start_url="http://127.0.0.1:8766/",
        browser="1",
    )

    assert spider.use_browser
    assert spider.request_meta()["playwright"] is True
