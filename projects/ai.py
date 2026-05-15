"""
AI annotation generator. Pulls text from a Resource (PDF or URL) and asks
OpenAI to produce a structured argument / methodology / findings / limitations
summary, returned as plain text suitable for the annotation field.
"""

import os
import re

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from pypdf import PdfReader


# ---------------------------------------------------------------------------
# Public errors
# ---------------------------------------------------------------------------

class AISummaryError(Exception):
    """Raised for any user-actionable failure during summary generation."""


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

MAX_CHARS = 40_000  # ~10k tokens — keeps cost predictable


def _extract_pdf_text(file_path):
    try:
        reader = PdfReader(file_path)
    except Exception as exc:
        raise AISummaryError(f"Couldn't open PDF: {exc}") from exc
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or '')
        except Exception:
            continue
    text = '\n\n'.join(parts).strip()
    if not text:
        raise AISummaryError(
            "Could not extract text from this PDF — it may be scanned images. "
            "Try a different file."
        )
    return text[:MAX_CHARS]


def _extract_url_text(url):
    try:
        resp = requests.get(
            url,
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0 (ResearchDoc bot)'},
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise AISummaryError(f"Couldn't fetch the URL: {exc}") from exc
    soup = BeautifulSoup(resp.text, 'html.parser')
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        tag.decompose()
    text = re.sub(r'\s+\n', '\n', soup.get_text(separator='\n')).strip()
    text = re.sub(r'\n{3,}', '\n\n', text)
    if len(text) < 200:
        raise AISummaryError(
            "Couldn't extract enough text from this URL "
            "(it may be JavaScript-rendered, paywalled, or empty)."
        )
    return text[:MAX_CHARS]


def extract_text(resource):
    """Return source text for an AI summary, or raise AISummaryError."""
    if resource.type == 'pdf' and resource.file_path:
        return _extract_pdf_text(resource.file_path.path)
    if resource.type == 'link' and resource.url:
        return _extract_url_text(resource.url)
    raise AISummaryError(
        "This resource has no PDF file or URL to read. "
        "Add one and try again."
    )


# ---------------------------------------------------------------------------
# OpenAI call
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a research assistant helping a researcher annotate academic papers "
    "and articles. Read the source text and produce a structured annotation with "
    "four sections: Argument, Methodology, Findings, Limitations.\n\n"
    "Be concise — roughly 50-90 words per section. Use neutral, third-person "
    "academic tone. Do not quote verbatim. If a section is genuinely not "
    "applicable to the source (e.g. a non-empirical piece has no methodology), "
    "write \"Not applicable.\" Return the annotation as JSON with keys: "
    "argument, methodology, findings, limitations."
)

USER_PROMPT_TEMPLATE = (
    "Title: {title}\n"
    "Authors: {authors}\n"
    "Year: {year}\n\n"
    "Source text:\n----\n{body}\n----"
)


def generate_annotation(resource):
    """Call OpenAI and return formatted annotation text. Raises AISummaryError."""
    api_key = os.getenv('OPENAI_API_KEY', '').strip()
    if not api_key:
        raise AISummaryError(
            "OPENAI_API_KEY isn't set. Add it to .env and restart Django."
        )

    body = extract_text(resource)

    client = OpenAI(api_key=api_key)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        title=resource.title or '(no title)',
        authors=resource.authors or '(unknown)',
        year=resource.year or '(unknown)',
        body=body,
    )

    try:
        completion = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            response_format={'type': 'json_object'},
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt},
            ],
            temperature=0.2,
        )
    except Exception as exc:
        raise AISummaryError(f"OpenAI request failed: {exc}") from exc

    content = (completion.choices[0].message.content or '').strip()
    if not content:
        raise AISummaryError("OpenAI returned an empty response.")

    import json
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AISummaryError(f"OpenAI response wasn't valid JSON: {exc}") from exc

    return _format_annotation(data)


def _format_annotation(data):
    """Render the structured dict as plain text suitable for a textarea."""
    sections = [
        ('ARGUMENT',     data.get('argument')),
        ('METHODOLOGY',  data.get('methodology')),
        ('FINDINGS',     data.get('findings')),
        ('LIMITATIONS',  data.get('limitations')),
    ]
    parts = []
    for label, value in sections:
        text = (value or '').strip()
        if not text:
            text = 'Not applicable.'
        parts.append(f'{label}\n{text}')
    return '\n\n'.join(parts)
