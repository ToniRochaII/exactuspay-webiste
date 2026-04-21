from __future__ import annotations

import ast
from pathlib import Path

from translation_overrides import TRANSLATIONS


BASE_DIR = Path(__file__).resolve().parent.parent


def _quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def _unquote_po_string(token: str) -> str:
    return ast.literal_eval(token)


def _parse_po_entry(block: str) -> tuple[str | None, str | None]:
    lines = block.splitlines()
    msgid_parts: list[str] = []
    msgstr_parts: list[str] = []
    state: str | None = None

    for line in lines:
        if line.startswith("msgid "):
            state = "msgid"
            msgid_parts = [_unquote_po_string(line[6:])]
            continue
        if line.startswith("msgstr "):
            state = "msgstr"
            msgstr_parts = [_unquote_po_string(line[7:])]
            continue
        if line.startswith('"') and state == "msgid":
            msgid_parts.append(_unquote_po_string(line))
            continue
        if line.startswith('"') and state == "msgstr":
            msgstr_parts.append(_unquote_po_string(line))
            continue

    msgid = "".join(msgid_parts) if msgid_parts else None
    msgstr = "".join(msgstr_parts) if msgstr_parts else None
    return msgid, msgstr


def _replace_msgstr(block: str, translation: str) -> str:
    lines = block.splitlines()
    out: list[str] = []
    in_msgstr = False
    inserted = False

    for line in lines:
        if line.startswith("#, fuzzy"):
            continue
        if line.startswith("msgstr "):
            if not inserted:
                out.append(f"msgstr {_quote(translation)}")
                inserted = True
            in_msgstr = True
            continue
        if in_msgstr and line.startswith('"'):
            continue
        in_msgstr = False
        out.append(line)

    if not inserted:
        out.append(f"msgstr {_quote(translation)}")
    return "\n".join(out)


def update_locale(locale: str, replacements: dict[str, str]) -> int:
    po_path = BASE_DIR / "locale" / locale / "LC_MESSAGES" / "django.po"
    text = po_path.read_text(encoding="utf-8")
    blocks = text.split("\n\n")
    updated = 0
    new_blocks: list[str] = []

    for block in blocks:
        msgid, msgstr = _parse_po_entry(block)
        if msgid and msgid in replacements and replacements[msgid]:
            translated = replacements[msgid]
            if msgstr != translated or "#, fuzzy" in block:
                block = _replace_msgstr(block, translated)
                updated += 1
        new_blocks.append(block)

    po_path.write_text("\n\n".join(new_blocks) + "\n", encoding="utf-8")
    return updated


def main() -> None:
    for locale, replacements in TRANSLATIONS.items():
        updated = update_locale(locale, replacements)
        print(locale, updated)


if __name__ == "__main__":
    main()
