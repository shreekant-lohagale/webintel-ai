
BOT_NAME = "webintel_ai"

SPIDER_MODULES = [
    "app.scrapers.scrapy_crawler.spiders"
]

NEWSPIDER_MODULE = (
    "app.scrapers.scrapy_crawler.spiders"
)

# Respect website crawling rules
ROBOTSTXT_OBEY = True

# Identify our crawler
USER_AGENT = "WebIntelAI-LearningBot/0.1"

# Avoid excessive requests
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 2.0

# Network safety
DOWNLOAD_TIMEOUT = 20
DOWNLOAD_MAXSIZE = 5 * 1024 * 1024

# Limit retries
RETRY_TIMES = 2

# Avoid crawling unexpectedly large sites
CLOSESPIDER_PAGECOUNT = 15

# Limit redirects to unexpected domains
REDIRECT_ENABLED = False

# Export UTF-8 JSON
FEED_EXPORT_ENCODING = "utf-8"

# Enable cleaning pipeline
ITEM_PIPELINES = {
    "app.scrapers.scrapy_crawler.pipelines.CleanQuotePipeline": 300,
}

LOG_LEVEL = "INFO"
