from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.site_builder import (
    ConnpassEvent,
    ContentItem,
    build_site,
    extract_connpass_event,
    sanitize_html,
)


CONNPASS_HTML = """
<html>
  <head>
    <meta property="og:title" content="Sample event (2026/07/10 14:00〜)" />
    <meta property="og:image" content="https://media.connpass.com/sample.png" />
  </head>
  <body>
    <div class="current_event_title">Sample event</div>
    <table>
      <tr><th>開催日時</th><td>2026/07/10(金) 14:00 ～ 15:30</td></tr>
    </table>
    <div id="editor_area" class="group_inner">
      <h2>HCCJP 第75回</h2>
      <p>イベント本文です。</p>
      <script>alert("bad")</script>
    </div>
  </body>
</html>
"""


def test_sanitize_html_removes_active_content_and_unsafe_links() -> None:
    raw_html = """
    <p onclick="steal()">安全な本文</p>
    <script>alert("bad")</script>
    <a href="javascript:alert(1)">bad link</a>
    <a href="https://example.com/path">good link</a>
    """

    result = sanitize_html(raw_html)

    assert "安全な本文" in result
    assert "<script" not in result
    assert "onclick" not in result
    assert "javascript:" not in result
    assert 'href="https://example.com/path"' in result
    assert 'rel="noopener noreferrer"' in result


def test_sanitize_html_restricts_iframe_hosts() -> None:
    raw_html = """
    <iframe src="https://www.youtube.com/embed/abc"></iframe>
    <iframe src="https://evil.example/embed/abc"></iframe>
    """

    result = sanitize_html(raw_html)

    assert "youtube.com/embed/abc" in result
    assert 'sandbox="allow-scripts allow-same-origin allow-presentation"' in result
    assert "evil.example" not in result


def test_sanitize_html_handles_children_of_removed_elements() -> None:
    raw_html = "<form><div><span>remove all of this</span></div></form><p>keep</p>"

    result = sanitize_html(raw_html)

    assert "remove all of this" not in result
    assert "<p>keep</p>" in result


def test_extract_connpass_event_reads_public_event_fields() -> None:
    event = extract_connpass_event(
        html=CONNPASS_HTML,
        event_number=75,
        source_url="https://hybridcloud.connpass.com/event/399283/",
    )

    assert event.number == 75
    assert event.title == "Sample event"
    assert event.date == "2026-07-10"
    assert event.start_time == "14:00"
    assert event.end_time == "15:30"
    assert event.image_url == "https://media.connpass.com/sample.png"
    assert "イベント本文です。" in event.content_html
    assert "<script" not in event.content_html


def test_extract_connpass_event_uses_longest_editor_area() -> None:
    html_with_private_notice = CONNPASS_HTML.replace(
        '<div id="editor_area" class="group_inner">',
        (
            '<div id="editor_area">(参加者のみに公開)</div>'
            '<div id="editor_area" class="group_inner">'
        ),
    )

    event = extract_connpass_event(
        html=html_with_private_notice,
        event_number=75,
        source_url="https://hybridcloud.connpass.com/event/399283/",
    )

    assert "イベント本文です。" in event.content_html
    assert "参加者のみに公開" not in event.content_html


def test_extract_connpass_event_rejects_missing_description() -> None:
    with pytest.raises(ValueError, match="editor_area"):
        extract_connpass_event(
            html=(
                "<html><body><div class='current_event_title'>Sample</div>"
                "</body></html>"
            ),
            event_number=75,
            source_url="https://hybridcloud.connpass.com/event/399283/",
        )


def test_homepage_hero_crop_preserves_embedded_title() -> None:
    stylesheet = (Path(__file__).parents[1] / "site" / "static" / "site.css").read_text(
        encoding="utf-8"
    )

    assert "object-position: 10% center;" in stylesheet
    assert "object-position: left center;" in stylesheet


def test_build_site_creates_home_archive_details_and_metadata(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "public"
    source_dir.mkdir()
    (source_dir / "assets").mkdir()
    (source_dir / "assets" / "logo.png").write_bytes(b"image")
    wordpress_item = ContentItem(
        title="既存の記事",
        date="2026-02-02",
        path="2026/02/02/existing",
        excerpt="既存記事の概要",
        content_html="<p>既存記事の本文</p>",
        source_url="https://www.hccjp.org/2026/02/02/existing/",
        image_path="assets/logo.png",
        kind="post",
    )
    connpass_event = ConnpassEvent(
        number=75,
        title="最新イベント",
        date="2026-07-10",
        start_time="14:00",
        end_time="15:30",
        source_url="https://hybridcloud.connpass.com/event/399283/",
        image_url="https://media.connpass.com/sample.png",
        image_path="assets/logo.png",
        content_html="<p>最新イベントの本文</p>",
    )
    (source_dir / "content.json").write_text(
        json.dumps(
            {
                "wordpress": [wordpress_item.to_dict()],
                "connpass": [connpass_event.to_dict()],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    build_site(source_dir=source_dir, output_dir=output_dir)

    home = (output_dir / "index.html").read_text(encoding="utf-8")
    archive = (output_dir / "events" / "index.html").read_text(encoding="utf-8")
    detail = (output_dir / "events" / "75" / "index.html").read_text(encoding="utf-8")
    legacy = (output_dir / "2026" / "02" / "02" / "existing" / "index.html").read_text(
        encoding="utf-8"
    )
    sitemap = (output_dir / "sitemap.xml").read_text(encoding="utf-8")

    assert "最新イベント" in home
    assert "第75回" in home
    assert "既存の記事" in archive
    assert "最新イベントの本文" in detail
    assert "既存記事の本文" in legacy
    assert "https://hccjp.org/events/75/" in sitemap
    assert (output_dir / "_headers").exists()
    assert (output_dir / "404.html").exists()
