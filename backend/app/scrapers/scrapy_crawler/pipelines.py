
import re

from scrapy.exceptions import DropItem


class CleanQuotePipeline:

    def process_item(self, item):
        """Clean and validate each extracted record."""

        text = item.get("text") or ""
        author = item.get("author") or ""

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        author = re.sub(r"\s+", " ", author).strip()

        # Reject incomplete records
        if not text or not author:
            raise DropItem("Missing quote text or author")

        item["text"] = text
        item["author"] = author

        # Remove duplicate tags inside one record
        item["tags"] = list(dict.fromkeys(
            tag.strip()
            for tag in item.get("tags", [])
            if tag and tag.strip()
        ))

        return item
