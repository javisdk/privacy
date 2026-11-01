#!/usr/bin/env python3
"""Archive the previous policy when index.html changes to a new app version."""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_PATTERN = r"\d+(?:\.\d+)*"
META_PATTERN = re.compile(
    r'<meta\s+name="voltio-policy-version"\s+content="(' + VERSION_PATTERN + r')"\s*/?>',
    re.IGNORECASE,
)
MARKER_PATTERN = re.compile(
    r"<!-- POLICY_VERSION_NAV_(EN|ES)_START -->.*?<!-- POLICY_VERSION_NAV_\1_END -->",
    re.DOTALL,
)


def version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def extract_version(html: str) -> str:
    match = META_PATTERN.search(html)
    if match:
        return match.group(1)
    match = re.search(
        r"(?:Current policy|Política actual)[^<]{0,120}?(?:app\s+)?(?:version|versión)\s*(" + VERSION_PATTERN + r")",
        html,
        re.IGNORECASE,
    )
    if match:
        return match.group(1)
    raise ValueError("Could not read the app version from the policy HTML")


def ensure_version_meta(html: str, version: str) -> str:
    tag = f'<meta name="voltio-policy-version" content="{version}">'
    if META_PATTERN.search(html):
        return META_PATTERN.sub(tag, html, count=1)
    description = re.search(r"<meta\s+name=\"description\"[^>]*>", html, re.IGNORECASE)
    if not description:
        raise ValueError("Could not find the description meta tag")
    return html[: description.end()] + "\n  " + tag + html[description.end() :]


def navigation_block(language: str, app_version: str, archive_versions: list[str], archived_page: str | None) -> str:
    is_spanish = language == "ES"
    if archived_page:
        status = (
            f"<p><strong>Política archivada · versión {archived_page}. "
            f"Actual: {app_version}.</strong></p>"
            if is_spanish
            else f"<p><strong>Archived policy · app version {archived_page}. "
            f"Current: {app_version}.</strong></p>"
        )
        aria = "Versiones de la política" if is_spanish else "Policy versions"
        current_name = "Versión actual" if is_spanish else "Current version"
        archive_name = "Política archivada" if is_spanish else "Archived policy"
    else:
        status = (
            f"<p><strong>Política actual · versión de la app {app_version}</strong></p>"
            if is_spanish
            else f"<p><strong>Current policy · app version {app_version}</strong></p>"
        )
        aria = "Versiones de la política" if is_spanish else "Policy versions"
        current_name = "Versión actual" if is_spanish else "Current version"
        archive_name = "Política archivada" if is_spanish else "Archived policy"

    links = [
        (app_version, "index.html", current_name, archived_page is None)
    ]
    for version in sorted(set(archive_versions), key=version_key, reverse=True):
        links.append((version, f"version-{version}.html", archive_name, archived_page == version))

    anchors = []
    for version, href, kind, active in links:
        current = ' aria-current="page"' if active else ""
        anchors.append(
            f'<a class="policy-version-link" href="{href}"{current} '
            f'aria-label="{version} · {kind}"><span>{version}</span><small>{kind}</small></a>'
        )
    start = f"<!-- POLICY_VERSION_NAV_{language}_START -->"
    end = f"<!-- POLICY_VERSION_NAV_{language}_END -->"
    return (
        f"{start}\n<nav class=\"policy-history\" aria-label=\"{aria}\">\n"
        f"  {status}\n  <div class=\"policy-version-browser\">\n    "
        + "\n    ".join(anchors)
        + f"\n  </div>\n</nav>\n{end}"
    )


def set_navigation(html: str, app_version: str, archive_versions: list[str], archived_page: str | None) -> str:
    html = ensure_version_meta(html, extract_version(html))
    blocks = {
        "EN": navigation_block("EN", app_version, archive_versions, archived_page),
        "ES": navigation_block("ES", app_version, archive_versions, archived_page),
    }
    found = set()

    def replace_marker(match: re.Match[str]) -> str:
        language = match.group(1)
        found.add(language)
        return blocks[language]

    html = MARKER_PATTERN.sub(replace_marker, html)
    if found != {"EN", "ES"}:
        html = re.sub(r'\s*<div class="policy-history">.*?</div>', "", html, flags=re.DOTALL)
        html = re.sub(r'\s*<p class="archive-notice">.*?</p>', "", html, flags=re.DOTALL)
        language_iter = iter(("EN", "ES"))

        def add_after_meta(match: re.Match[str]) -> str:
            language = next(language_iter)
            return match.group(0) + "\n      " + blocks[language]

        html, count = re.subn(r'<div class="meta">.*?</div>', add_after_meta, html, flags=re.DOTALL)
        if count != 2:
            raise ValueError(f"Expected two language policy headers, found {count}")

    css = """\n.policy-history { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px 20px; margin-top:18px; padding:14px 18px; border:1px solid var(--line); border-radius:8px; color:var(--muted); font-size:.8rem; line-height:1.5; }\n.policy-history p { margin:0; }\n.policy-history strong { color:var(--ink); }\n.policy-version-browser { display:flex; flex-wrap:wrap; gap:8px; }\n.policy-version-link { display:inline-flex; align-items:center; gap:6px; min-height:38px; padding:6px 10px; border:1px solid var(--line); border-radius:999px; color:var(--muted); font-size:.72rem; line-height:1.3; text-decoration:none; }\n.policy-version-link:hover,.policy-version-link[aria-current=page] { border-color:var(--accent); color:var(--ink); background:var(--surface); }\n.policy-version-link small { color:var(--muted); font-size:.62rem; }\n@media(max-width:480px) { .policy-history { display:block; } .policy-version-browser { margin-top:10px; } }\n"""
    if ".policy-version-browser" not in html:
        html = html.replace("\n</style>", css + "\n</style>", 1)
    elif "@media(max-width:480px) { .policy-history" not in html:
        html = html.replace("\n</style>", "\n@media(max-width:480px) { .policy-history { display:block; } .policy-version-browser { margin-top:10px; } }\n</style>", 1)
    return html


def read_previous_policy(ref: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{ref}:index.html"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def policy_date(html: str) -> str:
    match = re.search(r"Last updated:\s*([^<]+)", html, re.IGNORECASE)
    if not match:
        match = re.search(r"Última revisión:\s*([^<]+)", html, re.IGNORECASE)
    if not match:
        raise ValueError("Could not read the policy review date")
    date = match.group(1).strip()
    months = {"January":"enero", "February":"febrero", "March":"marzo", "April":"abril", "May":"mayo", "June":"junio", "July":"julio", "August":"agosto", "September":"septiembre", "October":"octubre", "November":"noviembre", "December":"diciembre"}
    parsed = re.fullmatch(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", date)
    if parsed and parsed.group(2) in months:
        return f"{parsed.group(1)} de {months[parsed.group(2)]} de {parsed.group(3)}"
    for english, spanish in months.items():
        date = re.sub(r"\b" + english + r"\b", spanish, date, flags=re.IGNORECASE)
    return date


def update_history_table(current_html: str, current_version: str, archive_versions: list[str]) -> None:
    readme_path = ROOT / "policy-history" / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    start = "<!-- POLICY_HISTORY_TABLE_START -->"
    end = "<!-- POLICY_HISTORY_TABLE_END -->"
    if start not in readme or end not in readme:
        raise ValueError("The policy history table markers are missing")

    pages = [(current_version, current_html, "../index.html", "Vigente")]
    for version in sorted(set(archive_versions), key=version_key, reverse=True):
        archived_html = (ROOT / f"version-{version}.html").read_text(encoding="utf-8")
        pages.append((version, archived_html, f"../version-{version}.html", "Archivada"))

    rows = [
        "| Versión de la app | Estado | Revisión | Política |",
        "| --- | --- | --- | --- |",
    ]
    for version, html, href, status in pages:
        date = policy_date(html)
        description = "Política actual" if status == "Vigente" else "Política archivada"
        rows.append(f"| {version} | {status} | {date} | [{description}]({href}) |")
    replacement = start + "\n" + "\n".join(rows) + "\n" + end
    before, remainder = readme.split(start, 1)
    _, after = remainder.split(end, 1)
    readme_path.write_text(before + replacement + after, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous-ref", required=True)
    args = parser.parse_args()

    if not re.fullmatch(r"[0-9a-f]{40}", args.previous_ref) or set(args.previous_ref) == {"0"}:
        print("No previous commit to archive")
        return

    current_path = ROOT / "index.html"
    current_html = current_path.read_text(encoding="utf-8")
    current_version = extract_version(current_html)
    previous_html = read_previous_policy(args.previous_ref)
    previous_version = extract_version(previous_html)
    if previous_version == current_version:
        print(f"Policy remains at version {current_version}; no archive needed")
        return

    archive_path = ROOT / f"version-{previous_version}.html"
    if not archive_path.exists():
        archive_path.write_text(
            ensure_version_meta(previous_html, previous_version), encoding="utf-8"
        )
        print(f"Archived previous policy as {archive_path.name}")

    archive_versions = [
        match.group(1)
        for path in ROOT.glob("version-*.html")
        if (match := re.fullmatch(r"version-(" + VERSION_PATTERN + r")\.html", path.name))
    ]
    archive_versions = sorted(set(archive_versions), key=version_key, reverse=True)

    current_path.write_text(
        set_navigation(current_html, current_version, archive_versions, None),
        encoding="utf-8",
    )
    for version in archive_versions:
        path = ROOT / f"version-{version}.html"
        archived_html = path.read_text(encoding="utf-8")
        archived_html = ensure_version_meta(archived_html, version)
        path.write_text(
            set_navigation(archived_html, current_version, archive_versions, version),
            encoding="utf-8",
        )
    current_html = current_path.read_text(encoding="utf-8")
    update_history_table(current_html, current_version, archive_versions)
    print(f"Policy version {current_version} published; archived {previous_version}")


if __name__ == "__main__":
    main()
