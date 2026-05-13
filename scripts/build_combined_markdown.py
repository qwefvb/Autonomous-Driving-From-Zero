#!/usr/bin/env python3

from __future__ import annotations

import posixpath
import re
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_MD = ROOT_DIR / "从零开始学习自动驾驶_合并版.md"

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
MD_LINK_RE = re.compile(r"(?<!\!)\[([^\]]+)\]\(([^)]+)\)")
HTML_ATTR_RE = re.compile(r'(?P<attr>href|src)="(?P<value>[^"]+)"')
CODE_FENCE_RE = re.compile(r"^(```|~~~)")


def repo_posix(path: Path) -> str:
    return path.relative_to(ROOT_DIR).as_posix()


def is_cjk(char: str) -> bool:
    codepoint = ord(char)
    return (
        0x4E00 <= codepoint <= 0x9FFF
        or 0x3400 <= codepoint <= 0x4DBF
        or 0x20000 <= codepoint <= 0x2A6DF
        or 0x2A700 <= codepoint <= 0x2B73F
        or 0x2B740 <= codepoint <= 0x2B81F
        or 0x2B820 <= codepoint <= 0x2CEAF
    )


def flatten_inline_markdown(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip().strip("#").strip()


def github_like_slug(text: str) -> str:
    plain = flatten_inline_markdown(text).lower()
    chars: list[str] = []

    for char in plain:
        if char.isalnum() or is_cjk(char):
            chars.append(char)
        elif char in {" ", "-", "_"}:
            chars.append("-")

    slug = re.sub(r"-+", "-", "".join(chars))
    return slug


def stable_path_slug(path_posix: str) -> str:
    slug = re.sub(r"[^0-9a-z]+", "-", path_posix.lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "section"


def is_external(target: str) -> bool:
    return target.startswith(("http://", "https://", "mailto:", "data:"))


def is_image_path(target: str) -> bool:
    lowered = target.lower()
    return lowered.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp"))


def collect_sources() -> list[Path]:
    docs_dir = ROOT_DIR / "docs"
    sources = [ROOT_DIR / "README.md"]
    changelog = docs_dir / "更新日志.md"

    if changelog.exists():
        sources.append(changelog)

    for path in sorted(docs_dir.rglob("*.md")):
        if path == changelog:
            continue
        sources.append(path)

    return sources


def parse_headings(path: Path, chapter_index: int) -> tuple[str, dict[str, str]]:
    path_posix = repo_posix(path)
    chapter_anchor = f"chapter-{chapter_index:02d}-{stable_path_slug(path_posix)}"
    hash_to_anchor: dict[str, str] = {}
    heading_counter = 0
    in_code_fence = False

    for line in path.read_text(encoding="utf-8").splitlines():
        if CODE_FENCE_RE.match(line.strip()):
            in_code_fence = not in_code_fence
            continue

        if in_code_fence:
            continue

        match = HEADING_RE.match(line)
        if not match:
            continue

        heading_counter += 1
        heading_text = flatten_inline_markdown(match.group(2))
        anchor = chapter_anchor if heading_counter == 1 else f"{chapter_anchor}-s{heading_counter:02d}"
        slug = github_like_slug(heading_text)

        if slug:
            hash_to_anchor[f"#{slug}"] = anchor
            hash_to_anchor[f"#{slug.lstrip('-')}"] = anchor

    return chapter_anchor, hash_to_anchor


def rewrite_target(
    current_path: Path,
    target: str,
    file_anchor_map: dict[str, str],
    file_hash_maps: dict[str, dict[str, str]],
) -> str:
    target = target.strip()

    if not target or is_external(target):
        return target

    current_posix = repo_posix(current_path)

    if target.startswith("#"):
        anchor = file_hash_maps[current_posix].get(target)
        return f"#{anchor}" if anchor else target

    path_part, _, hash_part = target.partition("#")
    current_dir = posixpath.dirname(current_posix)
    resolved = posixpath.normpath(posixpath.join(current_dir, path_part))

    if path_part.endswith(".md") and resolved in file_anchor_map:
        if hash_part:
            anchor = file_hash_maps[resolved].get(f"#{hash_part}") or file_anchor_map[resolved]
        else:
            anchor = file_anchor_map[resolved]
        return f"#{anchor}"

    if is_image_path(path_part):
        path_obj = (current_path.parent / Path(path_part)).resolve()
        return path_obj.relative_to(ROOT_DIR.resolve()).as_posix()

    return target


def rewrite_line(
    line: str,
    current_path: Path,
    file_anchor_map: dict[str, str],
    file_hash_maps: dict[str, dict[str, str]],
) -> str:
    line = line.replace("</br>", "<br />").replace("<br>", "<br />")

    def replace_md_link(match: re.Match[str]) -> str:
        text, target = match.group(1), match.group(2)
        rewritten = rewrite_target(current_path, target, file_anchor_map, file_hash_maps)
        return f"[{text}]({rewritten})"

    line = MD_LINK_RE.sub(replace_md_link, line)

    def replace_attr(match: re.Match[str]) -> str:
        attr = match.group("attr")
        value = match.group("value")

        if attr == "src" and "img.shields.io" in value:
            return 'src=""'

        rewritten = rewrite_target(current_path, value, file_anchor_map, file_hash_maps)
        return f'{attr}="{rewritten}"'

    line = HTML_ATTR_RE.sub(replace_attr, line)
    line = re.sub(r"<img\s+[^>]*>\s*", lambda m: "" if 'src=""' in m.group(0) else m.group(0), line)
    return line


def build_combined_markdown() -> None:
    sources = collect_sources()
    file_anchor_map: dict[str, str] = {}
    file_hash_maps: dict[str, dict[str, str]] = {}

    for index, path in enumerate(sources, start=1):
        anchor, hash_map = parse_headings(path, index)
        file_anchor_map[repo_posix(path)] = anchor
        file_hash_maps[repo_posix(path)] = hash_map

    output_parts: list[str] = []

    for index, path in enumerate(sources, start=1):
        path_posix = repo_posix(path)
        lines = path.read_text(encoding="utf-8").splitlines()
        chapter_anchor = file_anchor_map[path_posix]
        in_code_fence = False
        heading_counter = 0
        rewritten_lines: list[str] = []
        skip_badge_anchor = False

        for line in lines:
            stripped = line.strip()

            if path.name == "README.md":
                if skip_badge_anchor:
                    if stripped == "</a>":
                        skip_badge_anchor = False
                    continue
                if stripped.startswith('<a href="https://github.com/qwefvb/Autonomous-Driving-From-Zero'):
                    skip_badge_anchor = True
                    continue
                if "img.shields.io" in stripped:
                    continue

            if stripped in {"</br>", "<br>", "<br />"}:
                rewritten_lines.append("")
                continue

            if CODE_FENCE_RE.match(stripped):
                in_code_fence = not in_code_fence
                rewritten_lines.append(line)
                continue

            if not in_code_fence:
                match = HEADING_RE.match(line)
                if match:
                    heading_counter += 1
                    heading_level = len(match.group(1))
                    anchor = chapter_anchor if heading_counter == 1 else f"{chapter_anchor}-s{heading_counter:02d}"
                    anchor_classes = [
                        "doc-anchor",
                        "doc-anchor-chapter" if heading_counter == 1 else "doc-anchor-section",
                        f"doc-anchor-level-{heading_level}",
                    ]
                    if rewritten_lines and rewritten_lines[-1] != "":
                        rewritten_lines.append("")
                    rewritten_lines.append(
                        f'<div id="{anchor}" class="{" ".join(anchor_classes)}"></div>'
                    )
                    rewritten_lines.append("")

            if not in_code_fence:
                rewritten_lines.append(rewrite_line(line, path, file_anchor_map, file_hash_maps))
            else:
                rewritten_lines.append(line)

        body = "\n".join(rewritten_lines).strip()

        if output_parts:
            output_parts.append("\n\n---\n\n")

        output_parts.append(f"<!-- Source: {path_posix} -->\n\n{body}\n")

    OUTPUT_MD.write_text("".join(output_parts), encoding="utf-8")
    print(f"wrote {OUTPUT_MD}")


if __name__ == "__main__":
    build_combined_markdown()
