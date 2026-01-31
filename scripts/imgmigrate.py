#!/usr/bin/env python3
"""Usage: python scripts/md_img_to_cdn.py --root content --base-url http://public.kambri.top"""

import argparse
import os
import re
import sys


IMG_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replace local Markdown image paths with CDN URLs.")
    parser.add_argument("--root", "-r", default="content/post", help="Root directory. Default: content.")
    parser.add_argument(
        "--base-url",
        "-b",
        default="http://public.kambri.top/post",
        help="Base CDN URL. Default: http://public.kambri.top/post.",
    )
    return parser.parse_args()


def process_file(md_path: str, root: str, base_url: str):
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    rel_dir = os.path.relpath(os.path.dirname(md_path), root).replace("\\", "/")

    def repl(match):
        alt, path = match.groups()
        if path.startswith("http://") or path.startswith("https://"):
            return match.group(0)
        url = f"{base_url}/{rel_dir}/{path}".replace("//", "/")
        url = url.replace("http:/", "http://")
        return f"![{alt}]({url})"

    new_text = IMG_PATTERN.sub(repl, text)
    if new_text != text:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(new_text)
        print(f"[done] {md_path}")


def main():
    args = parse_args()
    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        raise SystemExit(f"Root directory does not exist: {root}")

    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if name.endswith(".md"):
                process_file(os.path.join(dirpath, name), root, args.base_url)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Failed: {exc}", file=sys.stderr)
        sys.exit(1)
