#!/usr/bin/env python3
"""Extract a public Instagram post or carousel through the public embed endpoint.

Usage:
    python scripts/ig_embed.py <shortcode-or-url> <outdir>

It prints the caption, downloads slide images, and builds contact.jpg.
No login, cookies, browser, or API key required.
"""
import html
import hashlib
import math
import os
import re
import sys
from io import BytesIO
from urllib.parse import urlparse

import requests
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def parse_shortcode(value: str) -> str:
    value = value.strip()
    if "instagram.com" not in value:
        return value.strip("/")
    path = urlparse(value).path.strip("/").split("/")
    for marker in ("p", "reel", "tv"):
        if marker in path:
            i = path.index(marker)
            if i + 1 < len(path):
                return path[i + 1]
    raise SystemExit("Could not find Instagram shortcode in URL")


def decode_display_url(value: str) -> str:
    value = re.sub(r"\\+u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), value)
    return html.unescape(value.replace("\\", ""))


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python scripts/ig_embed.py <shortcode-or-url> <outdir>")

    shortcode = parse_shortcode(sys.argv[1])
    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.instagram.com/",
    }

    response = requests.get(
        f"https://www.instagram.com/p/{shortcode}/embed/captioned/",
        headers=headers,
        timeout=30,
    )
    print("status:", response.status_code)
    raw = response.text

    searchable = html.unescape(raw).replace('\\', '')
    caption_match = re.search(r'<div class="Caption">(.*?)</div>', searchable, re.S)
    if caption_match:
        caption_html = html.unescape(caption_match.group(1))
        caption_html = re.sub(r"<br\s*/?>", "\n", caption_html)
        caption = re.sub(r"<[^>]+>", "", caption_html).strip()
        print("--- CAPTION ---")
        print(caption)
    else:
        meta_caption = re.search(r'<meta[^>]+property="og:description"[^>]+content="([^"]+)"', raw)
        if not meta_caption:
            meta_caption = re.search(r'<meta[^>]+content="([^"]+)"[^>]+property="og:description"', raw)
        if meta_caption:
            print("--- CAPTION ---")
            print(html.unescape(meta_caption.group(1)).strip())
        else:
            print("(caption not found)")

    urls = []
    normalized = html.unescape(raw)
    normalized = normalized.replace('\\\\"', '"').replace('\\"', '"')
    normalized = normalized.replace('\\\\/', '/').replace('\\/', '/')
    normalized = re.sub(r"\\\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), normalized)
    normalized = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), normalized)
    candidates = [raw, normalized, searchable]
    for source in candidates:
        for pattern in (r'\\"display_url\\":\\"(.*?)\\"', r'"display_url":"(.*?)"'):
            for display in re.finditer(pattern, source):
                url = decode_display_url(display.group(1))
                if url.startswith("http") and url not in urls:
                    urls.append(url)

    if not urls:
        image = re.search(r'class="EmbeddedMediaImage"[^>]*src="([^"]+)"', searchable)
        if image:
            urls = [html.unescape(image.group(1))]

    print("slide_urls:", len(urls))

    thumbs = []
    seen_hashes = set()
    unique_index = 0
    for url in urls:
        image_response = requests.get(url, headers=headers, timeout=30)
        image_response.raise_for_status()
        digest = hashlib.sha256(image_response.content).hexdigest()
        if digest in seen_hashes:
            continue
        seen_hashes.add(digest)
        unique_index += 1
        path = os.path.join(outdir, f"slide{unique_index:02d}.jpg")
        with open(path, "wb") as f:
            f.write(image_response.content)

        img = Image.open(BytesIO(image_response.content)).convert("RGB")
        img.thumbnail((470, 585))
        canvas = Image.new("RGB", (480, 620), "white")
        canvas.paste(img, ((480 - img.width) // 2, 25))
        ImageDraw.Draw(canvas).text((10, 5), f"slide {unique_index}", fill=(0, 0, 0))
        thumbs.append(canvas)

    if thumbs:
        print("slides:", len(thumbs))
        cols = min(3, len(thumbs))
        rows = math.ceil(len(thumbs) / cols)
        contact = Image.new("RGB", (480 * cols, 620 * rows), "white")
        for index, img in enumerate(thumbs):
            contact.paste(img, ((index % cols) * 480, (index // cols) * 620))
        contact_path = os.path.join(outdir, "contact.jpg")
        contact.save(contact_path, quality=90)
        print("contact:", contact_path)


if __name__ == "__main__":
    main()
