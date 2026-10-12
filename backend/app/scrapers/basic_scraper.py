
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup


USER_AGENT = "WebIntelAI-LearningBot/0.1"
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def check_robots(url: str, client: httpx.Client) -> bool:
    """Check whether robots.txt permits fetching the URL."""

    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    response = client.get(robots_url)

    if response.status_code in (404, 410):
        return True

    if response.status_code != 200:
        raise RuntimeError(
            f"Cannot verify crawl permission: "
            f"robots.txt returned {response.status_code}"
        )

    parser = RobotFileParser()
    parser.parse(response.text.splitlines())

    if not parser.can_fetch(USER_AGENT, url):
        return False

    return True


def fetch_html(url: str, client: httpx.Client) -> str:
    """Download a permitted HTML page."""

    response = client.get(url)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()

    if "text/html" not in content_type:
        raise ValueError("The URL did not return an HTML page.")

    return response.text


def parse_html(html: str, url: str) -> dict:
    """Extract structured information from HTML."""

    soup = BeautifulSoup(html, "lxml")

    title = soup.title.get_text(" ", strip=True) if soup.title else ""

    headings = [
        tag.get_text(" ", strip=True)
        for tag in soup.select("h1, h2, h3")
    ]

    paragraphs = [
        tag.get_text(" ", strip=True)
        for tag in soup.select("p")
    ]

    links = []

    for tag in soup.select("a[href]"):
        absolute_url = urljoin(url, tag["href"])

        if urlparse(absolute_url).scheme not in ("http", "https"):
            continue

        links.append({
            "text": tag.get_text(" ", strip=True),
            "url": absolute_url
        })

    return {
        "url": url,
        "title": title,
        "headings": headings,
        "paragraphs": paragraphs,
        "links": links,
        "scraped_at": datetime.now(timezone.utc).isoformat()
    }


def save_json(data: dict) -> Path:
    """Write extracted data to a JSON file."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    hostname = urlparse(data["url"]).hostname or "website"
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", hostname)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    output_file = OUTPUT_DIR / f"{safe_name}_{timestamp}.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    return output_file


def scrape_website(url: str) -> dict:
    """Check permissions, fetch HTML and extract data."""

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Enter a valid HTTP or HTTPS URL.")

    headers = {"User-Agent": USER_AGENT}

    with httpx.Client(
        headers=headers,
        timeout=15.0,
        follow_redirects=False
    ) as client:

        if not check_robots(url, client):
            raise PermissionError(
                "Crawling is disallowed by robots.txt."
            )

        html = fetch_html(url, client)

        return parse_html(html, url)


def main():
    parser = argparse.ArgumentParser(
        description="WebIntel AI - Basic Web Scraper"
    )

    parser.add_argument(
        "url",
        nargs="?",
        default="https://example.com/",
        help="Public webpage URL to scrape"
    )

    args = parser.parse_args()

    print(f"Fetching: {args.url}")

    try:
        data = scrape_website(args.url)
        output_file = save_json(data)

        print("\nScraping completed!")
        print(f"Title: {data['title']}")
        print(f"Headings: {len(data['headings'])}")
        print(f"Paragraphs: {len(data['paragraphs'])}")
        print(f"Links: {len(data['links'])}")
        print(f"Saved to: {output_file}")

    except (httpx.HTTPError, ValueError, PermissionError, RuntimeError) as exc:
        print(f"Scraping failed: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
