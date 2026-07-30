from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Comment, Tag

SITE_NAME = "ハイブリッドクラウド研究会"
SITE_TAGLINE = (
    "クラウドとオンプレミス、そしてAIの「いいとこ取り」を研究するコミュニティ"
)
SITE_URL = "https://hccjp.org"
CONNPASS_URL = "https://hybridcloud.connpass.com/"
YOUTUBE_URL = "https://www.youtube.com/@hccjp"

ALLOWED_TAGS = frozenset(
    {
        "a",
        "blockquote",
        "br",
        "code",
        "del",
        "em",
        "figcaption",
        "figure",
        "h2",
        "h3",
        "h4",
        "h5",
        "hr",
        "iframe",
        "img",
        "li",
        "ol",
        "p",
        "pre",
        "span",
        "strong",
        "table",
        "tbody",
        "td",
        "th",
        "thead",
        "tr",
        "ul",
    }
)
REMOVED_TAGS = frozenset(
    {"script", "style", "form", "input", "button", "object", "embed", "svg"}
)
SAFE_IFRAME_HOSTS = frozenset(
    {
        "www.youtube.com",
        "www.youtube-nocookie.com",
        "youtube.com",
        "www.slideshare.net",
        "slideshare.net",
    }
)
DATE_TIME_PATTERN = re.compile(
    r"(?P<date>\d{4}/\d{2}/\d{2}).*?"
    r"(?P<start>\d{2}:\d{2}).*?(?P<end>\d{2}:\d{2})",
    re.DOTALL,
)


@dataclass(frozen=True)
class ContentItem:
    title: str
    date: str
    path: str
    excerpt: str
    content_html: str
    source_url: str
    image_path: str | None
    kind: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> ContentItem:
        return cls(
            title=str(value["title"]),
            date=str(value["date"]),
            path=str(value["path"]).strip("/"),
            excerpt=str(value.get("excerpt", "")),
            content_html=str(value["content_html"]),
            source_url=str(value["source_url"]),
            image_path=(str(value["image_path"]) if value.get("image_path") else None),
            kind=str(value.get("kind", "post")),
        )


@dataclass(frozen=True)
class ConnpassEvent:
    number: int
    title: str
    date: str
    start_time: str
    end_time: str
    source_url: str
    image_url: str | None
    image_path: str | None
    content_html: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> ConnpassEvent:
        return cls(
            number=int(value["number"]),
            title=str(value["title"]),
            date=str(value["date"]),
            start_time=str(value["start_time"]),
            end_time=str(value["end_time"]),
            source_url=str(value["source_url"]),
            image_url=(str(value["image_url"]) if value.get("image_url") else None),
            image_path=(str(value["image_path"]) if value.get("image_path") else None),
            content_html=str(value["content_html"]),
        )

    def as_content_item(self) -> ContentItem:
        return ContentItem(
            title=self.title,
            date=self.date,
            path=f"events/{self.number}",
            excerpt=_excerpt_from_html(self.content_html),
            content_html=self.content_html,
            source_url=self.source_url,
            image_path=self.image_path,
            kind="event",
        )


def _safe_url(value: str, *, allow_mailto: bool = True) -> bool:
    parsed = urlparse(value)
    if not parsed.scheme:
        return not value.strip().lower().startswith("javascript:")
    allowed_schemes = {"http", "https"}
    if allow_mailto:
        allowed_schemes.add("mailto")
    return parsed.scheme.lower() in allowed_schemes


def _sanitize_attributes(tag: Tag) -> None:
    allowed: dict[str, frozenset[str]] = {
        "a": frozenset({"href", "title"}),
        "img": frozenset(
            {"src", "alt", "title", "width", "height", "loading", "class"}
        ),
        "iframe": frozenset(
            {"src", "title", "width", "height", "allow", "allowfullscreen"}
        ),
        "td": frozenset({"colspan", "rowspan"}),
        "th": frozenset({"colspan", "rowspan", "scope"}),
        "figure": frozenset({"class"}),
        "span": frozenset({"class"}),
        "code": frozenset({"class"}),
        "pre": frozenset({"class"}),
    }
    accepted = allowed.get(tag.name or "", frozenset())
    clean_attributes = {
        key: value for key, value in tag.attrs.items() if key in accepted
    }
    tag.attrs = clean_attributes

    if tag.name == "a":
        href = str(tag.get("href", ""))
        if href and not _safe_url(href):
            tag.attrs.pop("href", None)
        elif href:
            tag["rel"] = "noopener noreferrer"
    elif tag.name == "img":
        source = str(tag.get("src", ""))
        if not source or not _safe_url(source, allow_mailto=False):
            tag.decompose()
            return
        tag["loading"] = "lazy"


def _sanitize_iframe(tag: Tag) -> None:
    source = str(tag.get("src", ""))
    parsed = urlparse(source)
    if parsed.scheme != "https" or parsed.hostname not in SAFE_IFRAME_HOSTS:
        tag.decompose()
        return
    _sanitize_attributes(tag)
    tag["loading"] = "lazy"
    tag["sandbox"] = "allow-scripts allow-same-origin allow-presentation"
    tag["referrerpolicy"] = "strict-origin-when-cross-origin"


def sanitize_html(raw_html: str) -> str:
    """Return a conservative HTML subset suitable for static publishing."""
    soup = BeautifulSoup(raw_html, "html.parser")
    for comment in soup.find_all(string=lambda value: isinstance(value, Comment)):
        comment.extract()
    for tag in list(soup.find_all(True)):
        if tag.parent is None:
            continue
        if tag.name in REMOVED_TAGS:
            tag.decompose()
        elif tag.name == "iframe":
            _sanitize_iframe(tag)
        elif tag.name not in ALLOWED_TAGS:
            tag.unwrap()
        else:
            _sanitize_attributes(tag)
    return str(soup)


def extract_connpass_event(
    *,
    html: str,
    event_number: int,
    source_url: str,
) -> ConnpassEvent:
    soup = BeautifulSoup(html, "html.parser")
    title_node = soup.select_one(".current_event_title")
    description_nodes = soup.select("#editor_area")
    description_node = (
        max(
            description_nodes,
            key=lambda node: len(node.get_text(" ", strip=True)),
        )
        if description_nodes
        else None
    )
    if title_node is None:
        raise ValueError("Connpass page is missing current_event_title")
    if description_node is None:
        raise ValueError("Connpass page is missing editor_area")

    text = soup.get_text(" ", strip=True)
    match = DATE_TIME_PATTERN.search(text)
    if match is None:
        raise ValueError("Connpass page is missing a recognizable event date")

    image_node = soup.select_one('meta[property="og:image"]')
    image_url = str(image_node.get("content")) if image_node is not None else None
    normalized_date = match.group("date").replace("/", "-")
    return ConnpassEvent(
        number=event_number,
        title=title_node.get_text(" ", strip=True),
        date=normalized_date,
        start_time=match.group("start"),
        end_time=match.group("end"),
        source_url=source_url,
        image_url=image_url,
        image_path=None,
        content_html=sanitize_html(description_node.decode_contents()),
    )


def _excerpt_from_html(content_html: str, limit: int = 150) -> str:
    text = BeautifulSoup(content_html, "html.parser").get_text(" ", strip=True)
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}…"


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def _format_date(value: str) -> str:
    parsed = date.fromisoformat(value)
    return f"{parsed.year}.{parsed.month:02d}.{parsed.day:02d}"


def _header() -> str:
    return f"""
<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="/">
      <span class="brand-mark" aria-hidden="true">H</span>
      <span><strong>HCCJP</strong><small>{SITE_NAME}</small></span>
    </a>
    <nav aria-label="メインナビゲーション">
      <a href="/hccjp/">HCCJPとは</a>
      <a href="/events/">勉強会</a>
      <a href="{CONNPASS_URL}" rel="noopener noreferrer">connpass</a>
      <a href="{YOUTUBE_URL}" rel="noopener noreferrer">YouTube</a>
    </nav>
  </div>
</header>
"""


def _footer() -> str:
    return f"""
<footer class="site-footer">
  <div class="footer-inner">
    <div><strong>HCCJP</strong><br><span>{SITE_NAME}</span></div>
    <p>クラウドとオンプレミスの境界を越えて、現場の知恵を共有する。</p>
    <p class="copyright">© 2018–{date.today().year} {SITE_NAME}</p>
  </div>
</footer>
"""


def _document(*, title: str, description: str, body: str) -> str:
    safe_title = _escape(title)
    safe_description = _escape(description)
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{safe_title} | HCCJP</title>
  <meta name="description" content="{safe_description}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{safe_title}">
  <meta property="og:description" content="{safe_description}">
  <meta property="og:site_name" content="HCCJP">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="stylesheet" href="/assets/site.css">
</head>
<body>
  <a class="skip-link" href="#main">本文へ移動</a>
  {_header()}
  <main id="main">{body}</main>
  {_footer()}
</body>
</html>
"""


def _card(item: ContentItem, event_numbers: dict[str, int]) -> str:
    number = event_numbers.get(item.path)
    event_label = f"第{number}回" if number is not None else "勉強会"
    image = (
        f'<img src="/{_escape(item.image_path)}" alt="" loading="lazy">'
        if item.image_path
        else '<div class="card-placeholder" aria-hidden="true">HCCJP</div>'
    )
    return f"""
<article class="event-card">
  <a class="card-image" href="/{_escape(item.path)}/">{image}</a>
  <div class="card-body">
    <div class="card-meta"><span>{event_label}</span><time>{_format_date(item.date)}</time></div>
    <h3><a href="/{_escape(item.path)}/">{_escape(item.title)}</a></h3>
    <p>{_escape(item.excerpt)}</p>
  </div>
</article>
"""


def _home_page(
    posts: list[ContentItem],
    events: list[ConnpassEvent],
) -> str:
    latest = posts[0]
    event_numbers = {f"events/{event.number}": event.number for event in events}
    latest_number = event_numbers.get(latest.path)
    latest_label = f"HCCJP 第{latest_number}回勉強会" if latest_number else "HCCJP"
    hero_image = (
        f'<img src="/{_escape(latest.image_path)}" alt="" loading="eager">'
        if latest.image_path
        else '<div class="hero-placeholder" aria-hidden="true">HCCJP</div>'
    )
    cards = "".join(_card(item, event_numbers) for item in posts[:9])
    body = f"""
<section class="hero">
  <div class="hero-copy">
    <p class="eyebrow">HYBRID CLOUD COMMUNITY JAPAN</p>
    <h1>境界を越えて、<br><span>クラウドの次</span>を考える。</h1>
    <p class="hero-lead">{SITE_TAGLINE}</p>
    <div class="hero-actions">
      <a class="button button-primary" href="{CONNPASS_URL}">connpassで参加する</a>
      <a class="button button-secondary" href="/hccjp/">HCCJPについて</a>
    </div>
  </div>
  <div class="hero-visual" aria-label="最新イベント">
    {hero_image}
    <div class="hero-event">
      <span>{_escape(latest_label)}</span>
      <strong>{_escape(latest.title)}</strong>
      <time>{_format_date(latest.date)}</time>
    </div>
  </div>
</section>
<section class="topics">
  <p>AZURE LOCAL</p><p>AZURE ARC</p><p>HYBRID AI</p><p>ADAPTIVE CLOUD</p>
</section>
<section class="section">
  <div class="section-heading">
    <div><p class="eyebrow">EVENTS</p><h2>勉強会・お知らせ</h2></div>
    <a href="/events/">すべて見る →</a>
  </div>
  <div class="card-grid">{cards}</div>
</section>
<section class="about-band">
  <div>
    <p class="eyebrow">ABOUT HCCJP</p>
    <h2>ハイブリッドは、<br>つなぐ技術から<br><span>選べる設計</span>へ。</h2>
  </div>
  <div>
    <p>HCCJPは、Azureを中心としたハイブリッドクラウド、エッジコンピューティング、生成AIの最新技術を研究し、現場の知恵を共有するオープンなコミュニティです。</p>
    <a class="text-link" href="/hccjp/">私たちについて詳しく見る →</a>
  </div>
</section>
"""
    return _document(
        title="ハイブリッドクラウド研究会",
        description=SITE_TAGLINE,
        body=body,
    )


def _archive_page(
    posts: list[ContentItem],
    events: list[ConnpassEvent],
) -> str:
    event_numbers = {f"events/{event.number}": event.number for event in events}
    cards = "".join(_card(item, event_numbers) for item in posts)
    body = f"""
<section class="page-hero">
  <p class="eyebrow">EVENT ARCHIVE</p>
  <h1>勉強会・お知らせ</h1>
  <p>2018年の活動開始から最新回まで、HCCJPの記録をまとめています。</p>
</section>
<section class="section"><div class="card-grid">{cards}</div></section>
"""
    return _document(
        title="勉強会・お知らせ",
        description="HCCJPの勉強会とお知らせの一覧",
        body=body,
    )


def _detail_page(
    item: ContentItem,
    event_number: int | None,
) -> str:
    label = f"HCCJP 第{event_number}回勉強会" if event_number else "HCCJP"
    source_link = (
        f'<a href="{_escape(item.source_url)}" rel="noopener noreferrer">'
        "出典ページを見る ↗</a>"
    )
    image = (
        f'<img class="article-cover" src="/{_escape(item.image_path)}" alt="">'
        if item.image_path
        else ""
    )
    body = f"""
<article class="article">
  <header class="article-header">
    <p class="eyebrow">{_escape(label)}</p>
    <h1>{_escape(item.title)}</h1>
    <div class="article-meta"><time>{_format_date(item.date)}</time>{source_link}</div>
  </header>
  {image}
  <div class="article-content">{item.content_html}</div>
  <footer class="article-footer">
    <a class="button button-primary" href="{CONNPASS_URL}">connpassを見る</a>
    <a class="text-link" href="/events/">イベント一覧へ戻る →</a>
  </footer>
</article>
"""
    return _document(
        title=item.title,
        description=item.excerpt,
        body=body,
    )


def _not_found_page() -> str:
    body = """
<section class="page-hero error-page">
  <p class="eyebrow">404</p>
  <h1>ページが見つかりません</h1>
  <p>URLが変わったか、ページが移動した可能性があります。</p>
  <a class="button button-primary" href="/">トップへ戻る</a>
</section>
"""
    return _document(
        title="ページが見つかりません",
        description="ページが見つかりません",
        body=body,
    )


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _load_content(source_dir: Path) -> tuple[list[ContentItem], list[ConnpassEvent]]:
    payload = json.loads((source_dir / "content.json").read_text(encoding="utf-8"))
    wordpress = [ContentItem.from_dict(item) for item in payload.get("wordpress", [])]
    events = [ConnpassEvent.from_dict(item) for item in payload.get("connpass", [])]
    return wordpress, events


def _sitemap(items: list[ContentItem]) -> str:
    paths = ["", "events", *[item.path for item in items]]
    urls = "".join(
        f"<url><loc>{SITE_URL}/{html.escape(path)}/</loc></url>" for path in paths
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{urls}</urlset>"
    )


def _feed(posts: list[ContentItem]) -> str:
    entries = "".join(
        "<entry>"
        f"<title>{html.escape(item.title)}</title>"
        f'<link href="{SITE_URL}/{html.escape(item.path)}/"/>'
        f"<id>{SITE_URL}/{html.escape(item.path)}/</id>"
        f"<updated>{item.date}T00:00:00+09:00</updated>"
        f"<summary>{html.escape(item.excerpt)}</summary>"
        "</entry>"
        for item in posts[:20]
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<feed xmlns="http://www.w3.org/2005/Atom">'
        f"<title>{SITE_NAME}</title><id>{SITE_URL}/</id>{entries}</feed>"
    )


def _write_headers(output_dir: Path) -> None:
    content_security_policy = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self'; "
        "script-src 'none'; "
        "frame-src https://www.youtube.com https://www.youtube-nocookie.com "
        "https://www.slideshare.net; "
        "base-uri 'self'; form-action 'none'; frame-ancestors 'none'"
    )
    headers = f"""/*
  Content-Security-Policy: {content_security_policy}
  Referrer-Policy: strict-origin-when-cross-origin
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Strict-Transport-Security: max-age=31536000; includeSubDomains

/assets/*
  Cache-Control: public, max-age=31536000, immutable
"""
    _write_text(output_dir / "_headers", headers)


def build_site(*, source_dir: Path, output_dir: Path) -> None:
    wordpress, events = _load_content(source_dir)
    event_items = [event.as_content_item() for event in events]
    all_items = sorted(
        [*wordpress, *event_items],
        key=lambda item: (item.date, item.title),
        reverse=True,
    )
    posts = [item for item in all_items if item.kind != "page"]
    event_numbers = {f"events/{event.number}": event.number for event in events}

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    static_dir = source_dir / "static"
    assets_dir = source_dir / "assets"
    if static_dir.exists():
        shutil.copytree(static_dir, output_dir / "assets", dirs_exist_ok=True)
    if assets_dir.exists():
        shutil.copytree(assets_dir, output_dir / "assets", dirs_exist_ok=True)

    _write_text(output_dir / "index.html", _home_page(posts, events))
    _write_text(
        output_dir / "events" / "index.html",
        _archive_page(posts, events),
    )
    for item in all_items:
        _write_text(
            output_dir / item.path / "index.html",
            _detail_page(item, event_numbers.get(item.path)),
        )
    _write_text(output_dir / "404.html", _not_found_page())
    _write_text(output_dir / "sitemap.xml", _sitemap(all_items))
    _write_text(output_dir / "feed.xml", _feed(posts))
    _write_headers(output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the HCCJP static site")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("site"),
        help="Source directory containing content.json and assets",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("public"),
        help="Output directory",
    )
    arguments = parser.parse_args()
    build_site(source_dir=arguments.source, output_dir=arguments.output)


if __name__ == "__main__":
    main()
