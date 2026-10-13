
import pytest

from app.processing.cleaning import (
    canonicalize_url,
    clean_html,
    clean_text,
    normalize_tags,
    sha256_hash,
)


def test_clean_text():
    assert clean_text(
        "  Hello \n  world \t "
    ) == "Hello world"


def test_unicode_normalization():
    assert clean_text("ＡＩ\u00a0tools") == "AI tools"


def test_clean_html():
    html = """
    <article>
        <h1>AI News</h1>
        <script>secretTrackingCode()</script>
        <p>New model released.</p>
    </article>
    """

    result = clean_html(html)

    assert result == "AI News New model released."
    assert "secretTrackingCode" not in result


def test_normalize_tags():
    assert normalize_tags([
        " AI ",
        "ai",
        "Python",
        "python",
    ]) == ["ai", "python"]


def test_canonicalize_url():
    assert canonicalize_url(
        "HTTPS://EXAMPLE.COM:443/news?id=2&utm_source=abc#top"
    ) == "https://example.com/news?id=2"


def test_url_rejects_unsupported_scheme():
    with pytest.raises(ValueError):
        canonicalize_url("file:///private.txt")


def test_hash_is_deterministic():
    first = sha256_hash("same content")
    second = sha256_hash("same content")

    assert first == second
    assert len(first) == 64
