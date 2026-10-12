
import json
from pathlib import Path


DATA_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "raw"
    / "quotes.json"
)


def main():
    if not DATA_FILE.exists():
        print("Dataset not found. Run the spider first.")
        return

    with DATA_FILE.open("r", encoding="utf-8") as file:
        records = json.load(file)

    unique_quotes = {
        (record["text"], record["author"])
        for record in records
    }

    pages = {
        record["source_url"]
        for record in records
    }

    print("WEBINTEL AI - SCRAPY REPORT")
    print("-" * 35)
    print("Total records:", len(records))
    print("Unique quotes:", len(unique_quotes))
    print("Pages collected:", len(pages))
    print("Duplicate records:", len(records) - len(unique_quotes))

    if records:
        print("Sample author:", records[0]["author"])
        print("Sample quote:", records[0]["text"][:100])


if __name__ == "__main__":
    main()
