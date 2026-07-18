#!/usr/bin/env python3
"""Rebuilds ai-pulse/index.html from ai-pulse/log.json.

Each entry is bucketed into exactly one section — the tightest window it
falls into (today / this week / this month / this year) — so nothing is
repeated across sections. Run with no arguments; it uses the current date.
"""
import json
import html
import os
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(HERE, "log.json")
TEMPLATE_PATH = os.path.join(HERE, "template.html")
OUTPUT_PATH = os.path.join(HERE, "index.html")

CATEGORY_LABELS = {
    "model-release": "Model Release",
    "research": "Research",
    "policy": "Policy",
    "infrastructure": "Infrastructure",
}


def load_entries():
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("entries", [])


def bucket_for(entry_date, today):
    age = (today - entry_date).days
    if age < 0:
        return None
    if age == 0:
        return "today"
    if age <= 7:
        return "week"
    if age <= 30:
        return "month"
    if age <= 365:
        return "year"
    return None


def render_entry(entry):
    label = CATEGORY_LABELS.get(entry["category"], entry["category"].title())
    title = html.escape(entry["title"])
    why = html.escape(entry["why_it_matters"])
    entry_date = html.escape(entry["date"])
    sources = entry.get("sources", [])
    source_links = " &middot; ".join(
        '<a href="{url}" target="_blank" rel="noopener">{name}</a>'.format(
            url=html.escape(s["url"]), name=html.escape(s["name"])
        )
        for s in sources
    )
    return """
    <article class="entry">
      <div class="entry-meta">
        <span class="tag">{label}</span>
        <span class="entry-date">{date}</span>
      </div>
      <h3 class="entry-title">{title}</h3>
      <p class="entry-why">{why}</p>
      <div class="entry-sources">{sources}</div>
    </article>""".format(label=label, date=entry_date, title=title, why=why, sources=source_links)


QUIET_MESSAGES = {
    "today": "Nothing cleared the bar today. Most days won't — that's expected.",
    "week": "Nothing new this week beyond what's already shown above.",
    "month": "Nothing new this month beyond what's already shown above.",
    "year": "Nothing new this year beyond what's already shown above.",
}


def render_section(bucket_entries, bucket):
    if not bucket_entries:
        return '<p class="quiet">{}</p>'.format(QUIET_MESSAGES[bucket])
    bucket_entries = sorted(bucket_entries, key=lambda e: e["date"], reverse=True)
    return "".join(render_entry(e) for e in bucket_entries)


def main():
    today = date.today()
    entries = load_entries()

    buckets = {"today": [], "week": [], "month": [], "year": []}
    for entry in entries:
        entry_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
        b = bucket_for(entry_date, today)
        if b:
            buckets[b].append(entry)

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        tpl = f.read()

    replacements = {
        "{{LAST_UPDATED}}": today.strftime("%B %-d, %Y"),
        "{{TODAY_COUNT}}": "({})".format(len(buckets["today"])) if buckets["today"] else "",
        "{{WEEK_COUNT}}": "({})".format(len(buckets["week"])) if buckets["week"] else "",
        "{{MONTH_COUNT}}": "({})".format(len(buckets["month"])) if buckets["month"] else "",
        "{{YEAR_COUNT}}": "({})".format(len(buckets["year"])) if buckets["year"] else "",
        "{{TODAY_ENTRIES}}": render_section(buckets["today"], "today"),
        "{{WEEK_ENTRIES}}": render_section(buckets["week"], "week"),
        "{{MONTH_ENTRIES}}": render_section(buckets["month"], "month"),
        "{{YEAR_ENTRIES}}": render_section(buckets["year"], "year"),
    }
    for placeholder, value in replacements.items():
        tpl = tpl.replace(placeholder, value)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(tpl)

    print("Wrote", OUTPUT_PATH)
    print("Bucket counts:", {k: len(v) for k, v in buckets.items()})


if __name__ == "__main__":
    main()
