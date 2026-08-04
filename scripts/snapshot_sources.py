from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import time
from dataclasses import replace
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from scripts.site_builder import (
    ConnpassEvent,
    ContentItem,
    extract_connpass_event,
    sanitize_html,
)

WORDPRESS_POSTS_URL = "https://www.hccjp.org/wp-json/wp/v2/posts?per_page=100&_embed"
WORDPRESS_PAGES_URL = "https://www.hccjp.org/wp-json/wp/v2/pages?per_page=100&_embed"
CONNPASS_EVENTS = (
    (71, "https://hybridcloud.connpass.com/event/386349/"),
    (72, "https://hybridcloud.connpass.com/event/389668/"),
    (73, "https://hybridcloud.connpass.com/event/391292/"),
    (74, "https://hybridcloud.connpass.com/event/396455/"),
    (75, "https://hybridcloud.connpass.com/event/399283/"),
    (76, "https://hybridcloud.connpass.com/event/402528/"),
)
DOCUMENT_HOSTS = frozenset({"www.hccjp.org", "hybridcloud.connpass.com"})
ASSET_HOSTS = frozenset(
    {
        "www.hccjp.org",
        "hccjp.org",
        "wordpressimages.blob.core.windows.net",
        "media.connpass.com",
        "i0.wp.com",
        "i1.wp.com",
        "i2.wp.com",
    }
)
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "Chrome/124 Safari/537.36 HCCJPStaticArchive/1.0"
)
MAX_ASSET_BYTES = 15 * 1024 * 1024
RETRY_DELAYS = (0.0, 1.0, 2.0)
MIME_EXTENSIONS = {
    "image/gif": ".gif",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/svg+xml": ".svg",
    "image/webp": ".webp",
}


def _validate_url(url: str, allowed_hosts: frozenset[str]) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in allowed_hosts:
        raise ValueError(f"URL host is not allowed: {url}")


def _fetch(url: str, allowed_hosts: frozenset[str]) -> tuple[bytes, str]:
    _validate_url(url, allowed_hosts)
    request = Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for delay in RETRY_DELAYS:
        if delay:
            time.sleep(delay)
        try:
            with urlopen(request, timeout=30) as response:  # nosec B310
                content_type = response.headers.get_content_type()
                payload = response.read(MAX_ASSET_BYTES + 1)
                if len(payload) > MAX_ASSET_BYTES:
                    raise ValueError(f"Response exceeds size limit: {url}")
                return payload, content_type
        except (HTTPError, URLError, TimeoutError) as error:
            last_error = error
    raise RuntimeError(f"Failed to download {url}: {last_error}")


def _fetch_text(url: str) -> str:
    payload, _ = _fetch(url, DOCUMENT_HOSTS)
    return payload.decode("utf-8")


def _fetch_json(url: str) -> list[dict[str, Any]]:
    payload = json.loads(_fetch_text(url))
    if not isinstance(payload, list):
        raise ValueError(f"Expected a JSON list from {url}")
    return payload


def _asset_filename(url: str, content_type: str) -> str:
    parsed = urlparse(url)
    original_name = Path(unquote(parsed.path)).name
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", original_name).strip("-")
    stem = stem[:80] or "asset"
    extension = MIME_EXTENSIONS.get(content_type)
    if extension is None:
        guessed = mimetypes.guess_extension(content_type)
        if guessed not in MIME_EXTENSIONS.values():
            raise ValueError(f"Unsupported asset type {content_type}: {url}")
        extension = guessed
    if Path(stem).suffix.lower() in MIME_EXTENSIONS.values():
        stem = str(Path(stem).with_suffix(""))
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    return f"{digest}-{stem}{extension}"


def _download_asset(url: str, assets_dir: Path) -> str:
    secure_url = re.sub(r"^http://", "https://", url)
    payload, content_type = _fetch(secure_url, ASSET_HOSTS)
    if content_type not in MIME_EXTENSIONS:
        raise ValueError(f"Downloaded content is not an image: {secure_url}")
    filename = _asset_filename(secure_url, content_type)
    destination = assets_dir / "media" / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return f"assets/media/{filename}"


def _localize_content_images(content_html: str, assets_dir: Path) -> str:
    soup = BeautifulSoup(content_html, "html.parser")
    for image in list(soup.find_all("img")):
        source = str(image.get("src", ""))
        if not source:
            image.decompose()
            continue
        try:
            image["src"] = f"/{_download_asset(source, assets_dir)}"
        except (RuntimeError, ValueError):
            image.decompose()
            continue
        image.attrs.pop("srcset", None)
        image.attrs.pop("sizes", None)
    return sanitize_html(str(soup))


def _featured_image_url(item: dict[str, Any]) -> str | None:
    embedded = item.get("_embedded", {})
    media_list = embedded.get("wp:featuredmedia", [])
    if not media_list:
        return None
    media = media_list[0]
    sizes = media.get("media_details", {}).get("sizes", {})
    for size_name in ("medium_large", "large", "medium"):
        source = sizes.get(size_name, {}).get("source_url")
        if source:
            return str(source)
    source = media.get("source_url")
    return str(source) if source else None


def _wordpress_path(item: dict[str, Any]) -> str:
    parsed = urlparse(str(item["link"]))
    path = unquote(parsed.path).strip("/")
    if not path or ".." in Path(path).parts:
        raise ValueError(f"Unsafe WordPress path: {path}")
    return path


def _wordpress_item(
    item: dict[str, Any],
    *,
    kind: str,
    assets_dir: Path,
) -> ContentItem:
    content_html = _localize_content_images(
        str(item["content"]["rendered"]),
        assets_dir,
    )
    excerpt_html = sanitize_html(str(item["excerpt"]["rendered"]))
    excerpt = BeautifulSoup(excerpt_html, "html.parser").get_text(" ", strip=True)
    featured_url = _featured_image_url(item)
    image_path = _download_asset(featured_url, assets_dir) if featured_url else None
    return ContentItem(
        title=BeautifulSoup(str(item["title"]["rendered"]), "html.parser").get_text(
            " ", strip=True
        ),
        date=str(item["date"])[:10],
        path=_wordpress_path(item),
        excerpt=excerpt,
        content_html=content_html,
        source_url=str(item["link"]),
        image_path=image_path,
        kind=kind,
    )


def _connpass_event(
    number: int,
    url: str,
    assets_dir: Path,
) -> ConnpassEvent:
    event = extract_connpass_event(
        html=_fetch_text(url),
        event_number=number,
        source_url=url,
    )
    image_path = (
        _download_asset(event.image_url, assets_dir) if event.image_url else None
    )
    content_html = _localize_content_images(event.content_html, assets_dir)
    return replace(
        event,
        image_path=image_path,
        content_html=content_html,
    )


def snapshot_sources(output_dir: Path) -> None:
    assets_dir = output_dir / "assets"
    posts = [
        _wordpress_item(item, kind="post", assets_dir=assets_dir)
        for item in _fetch_json(WORDPRESS_POSTS_URL)
    ]
    pages = [
        _wordpress_item(item, kind="page", assets_dir=assets_dir)
        for item in _fetch_json(WORDPRESS_PAGES_URL)
    ]
    events = [
        _connpass_event(number, url, assets_dir) for number, url in CONNPASS_EVENTS
    ]
    payload = {
        "snapshot_date": "2026-07-30",
        "wordpress": [item.to_dict() for item in [*posts, *pages]],
        "connpass": [event.to_dict() for event in events],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "content.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Snapshot HCCJP WordPress and Connpass content"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("site"),
        help="Destination for content.json and downloaded assets",
    )
    arguments = parser.parse_args()
    snapshot_sources(arguments.output)


if __name__ == "__main__":
    main()
