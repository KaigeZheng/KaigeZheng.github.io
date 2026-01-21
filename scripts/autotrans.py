#!/usr/bin/env python3
"""Usage: python scripts/autotrans.py --languages en ja --root content --mode overwrite"""

import argparse
import copy
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with `pip install pyyaml`.") from exc


DEFAULT_LANGS = ["en", "ja"]
TRANSLATABLE_KEYS = {"title", "description", "summary", "tags"}
WARNING_BY_LANG = {
    "en": "⚠️ Please note that the content here was translated by a large language model.",
    "ja": "⚠️ご注意ください、ここにある内容は大規模言語モデルによって翻訳されたものです。",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Translate Markdown into target languages.")
    parser.add_argument(
        "--languages",
        "-l",
        nargs="+",
        default=DEFAULT_LANGS,
        help="Target language codes, e.g. en ja. Default: en ja.",
    )
    parser.add_argument(
        "--root",
        "-r",
        default="content",
        help="Root directory to process. Default: content.",
    )
    parser.add_argument(
        "--mode",
        choices=["skip", "overwrite"],
        default="skip",
        help="How to handle existing translations: skip or overwrite. Default: skip.",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="Model name. Default: gpt-4o.",
    )
    parser.add_argument(
        "--retry",
        type=int,
        default=3,
        help="Retry count for failed API calls. Default: 3.",
    )
    return parser.parse_args()


def lang_name(code: str) -> str:
    return {"en": "English", "ja": "Japanese"}.get(code.lower(), code)


def load_api_key() -> str:
    api_key = os.environ.get("API_KEY")
    if not api_key:
        raise SystemExit("Please set API_KEY in environment.")
    return api_key


def translate_text(
    text: str, target_lang: str, api_key: str, model: str, retry: int = 3
) -> str:
    """
    Translate text using an OpenAI-compatible Chat Completions API.
    """
    api_base = os.environ.get("BASE_URL", "https://api.openai.com/v1")
    url = api_base.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a professional translator. Translate user-provided text "
                    f"into {lang_name(target_lang)}. Preserve Markdown structure, code "
                    "blocks, and links. Output only the translated text."
                ),
            },
            {"role": "user", "content": text},
        ],
        "temperature": 0,
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")

    last_error = None
    attempts = max(1, int(retry))
    resp_body = b""
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request) as resp:
                resp_body = resp.read()
            last_error = None
            break
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            last_error = RuntimeError(
                f"Translation API error: {exc.code} {exc.reason} {detail}"
            )
        except urllib.error.URLError as exc:
            last_error = RuntimeError(f"Cannot reach translation API: {exc.reason}")
        except Exception as exc:
            last_error = RuntimeError(f"Translation request failed: {exc}")

        if attempt < attempts:
            time.sleep(min(2 ** (attempt - 1), 8))

    if last_error is not None:
        raise last_error

    try:
        parsed = json.loads(resp_body)
        return parsed["choices"][0]["message"]["content"].strip()
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Failed to parse translation response: {resp_body!r}") from exc


def split_frontmatter(content: str):
    if not content.startswith("---"):
        return None, content

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", content, re.S)
    if not match:
        return None, content
    front_raw, body = match.groups()
    front_dict = yaml.safe_load(front_raw) or {}
    return front_dict, body


def dump_frontmatter(front_dict) -> str:
    dumped = yaml.safe_dump(
        front_dict,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    ).rstrip()
    return f"---\n{dumped}\n---\n\n"


def translate_frontmatter(front_dict, target_lang, api_key, model, retry: int):
    translated = copy.deepcopy(front_dict)
    for key in TRANSLATABLE_KEYS:
        if key not in front_dict:
            continue
        value = front_dict[key]
        if isinstance(value, str):
            translated[key] = translate_text(value, target_lang, api_key, model, retry)
        elif isinstance(value, list) and all(isinstance(i, str) for i in value):
            translated[key] = [
                translate_text(i, target_lang, api_key, model, retry) for i in value
            ]
        else:
            translated[key] = value
    return translated


def process_file(
    src_path: str, target_langs, mode: str, api_key: str, model: str, retry: int
):
    with open(src_path, "r", encoding="utf-8") as f:
        content = f.read()

    front, body = split_frontmatter(content)
    body_is_empty = body.strip() == ""

    for lang in target_langs:
        target_path = src_path.replace(".md", f".{lang}.md")
        if os.path.exists(target_path) and mode == "skip":
            print(f"[skip] already exists: {target_path}")
            continue

        front_part = ""
        if front is not None:
            translated_front = translate_frontmatter(front, lang, api_key, model, retry)
            front_part = dump_frontmatter(translated_front)

        if body_is_empty:
            output = front_part
        else:
            warning_line = WARNING_BY_LANG.get(lang, WARNING_BY_LANG["en"])
            translated_body = translate_text(body, lang, api_key, model, retry)
            warning_block = f"> {warning_line}\n\n"
            output = f"{front_part}{warning_block}{translated_body}\n"

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"[done] {src_path} -> {target_path}")


def main():
    args = parse_args()
    api_key = load_api_key()
    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        raise SystemExit(f"Root directory does not exist: {root}")

    target_langs = [lang.lower() for lang in args.languages]
    candidates = {"index.md", "_index.md"}

    for dirpath, _, filenames in os.walk(root):
        for name in candidates:
            if name in filenames:
                process_file(
                    os.path.join(dirpath, name),
                    target_langs,
                    args.mode,
                    api_key,
                    args.model,
                    args.retry,
                )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Failed: {exc}", file=sys.stderr)
        sys.exit(1)
