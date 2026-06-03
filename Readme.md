# Annota

Annota is a Django web app for turning scattered research material into an
organised, searchable writing workspace. It helps researchers collect sources,
generate structured annotations, draft summaries with inline citation chips, and
compare papers or methods side by side.

The repository is still named `ResearchDoc`, but the application is now called
**Annota**.

## Live Deployment

- App: https://web-production-0b24b3.up.railway.app
- Admin: https://web-production-0b24b3.up.railway.app/admin/

## What Annota Is About

Research work often starts as a messy mix of PDFs, article links, notes,
comparison tables, and half-written synthesis. Annota brings those pieces into
one place. Each research project becomes a focused workspace where sources,
annotations, summaries, citations, and comparison tables stay connected.

Annota is designed for students, academics, analysts, and research teams who
need to move from "I have a pile of readings" to "I can explain, compare, and
cite these sources clearly."

## How It Works

1. Create a research project.
   Each project has its own resources, summaries, and comparison tables, so
   work on different topics stays separated.

2. Add resources.
   A resource can be a PDF upload or an article link. Users can record the
   title, authors, year, tags, URL or file, and their own notes.

3. Generate or write annotations.
   For supported PDFs and web links, Annota can extract source text and ask the
   OpenAI API to produce a structured annotation covering argument,
   methodology, findings, and limitations. Users can edit the annotation before
   saving it.

4. Draft summaries with citations.
   Summaries use a TipTap rich-text editor. Users can write formatted notes and
   insert citation chips that link the summary back to the resources it cites.

5. Build comparison tables.
   Comparison tables use the same rich-text editor with table controls, making
   it easier to compare papers, methods, tools, or arguments across custom rows
   and columns.

6. Search the workspace.
   The search page looks across projects, resources, summaries, and comparison
   tables. Results can be filtered by content type.

## Core Features

- Project-based research workspaces
- PDF and link resource management
- Tags, authors, years, annotations, and source metadata
- AI-generated research annotations using OpenAI
- Rich-text summaries powered by TipTap
- Inline citation chips connected to saved resources
- Rich comparison tables for structured analysis
- Dashboard with project, resource, citation, and writing activity counts
- Full-workspace search across major content types
- Google OAuth and local email/password sign-up through `django-allauth`
- Django admin support for managing projects, resources, tags, summaries,
  citations, comparison tables, and subscriptions

## Tech Stack

- Python / Django
- SQLite for local development
- Postgres support through `DATABASE_URL` for deployment
- `django-allauth` for authentication and Google OAuth
- OpenAI API for annotation generation
- TipTap, esbuild, and Tailwind CSS for the editor and frontend assets
- WhiteNoise and Gunicorn for production serving
- Railway deployment via `railpack.json`

## Data Model

Annota is built around a small set of connected models:

- `Project`: a user-owned research workspace
- `Resource`: a PDF or link inside a project
- `Tag`: reusable labels for resources
- `Summary`: a rich-text research note or synthesis document
- `Citation`: a connection between a summary and a cited resource
- `ComparisonTable`: a rich-text comparison document inside a project
- `Subscription`: a simple user subscription record used for admin features

## Local Setup

### 1. Create and activate a Python environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Node dependencies

```bash
npm install
```

### 4. Configure environment variables

Create a `.env` file in the project root. For local development, the app can run
with SQLite and without Google OAuth, but AI annotation requires an OpenAI key.

```env
SECRET_KEY=replace-me
DEBUG=True
ALLOWED_HOSTS=localhost 127.0.0.1
OPENAI_API_KEY=replace-me
OPENAI_MODEL=gpt-4o-mini
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

Optional production variables:

```env
DATABASE_URL=postgres://...
CSRF_TRUSTED_ORIGINS=https://your-domain.example
```

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Build frontend assets

```bash
npm run build
```

For development, you can run the CSS and JS watchers in separate terminals:

```bash
npm run watch:css
npm run watch:js
```

### 7. Start Django

```bash
python manage.py runserver
```

Then visit:

```text
http://127.0.0.1:8000/
```

## Demo Data

The project includes a management command that seeds a realistic research
workspace for an existing user.

```bash
python manage.py seed --user <username>
```

The seed data creates example projects, resources, summaries, citations, and
comparison tables for topics such as mixture-of-experts research and
long-context retrieval.

## AI Annotation Flow

When a user clicks the AI annotation action for a resource, Annota:

1. Checks whether the resource is a PDF or link.
2. Extracts text with `pypdf` for PDFs or `requests` and BeautifulSoup for web
   links.
3. Truncates extracted content to keep token usage predictable.
4. Sends the source text to OpenAI with a prompt asking for four sections:
   argument, methodology, findings, and limitations.
5. Saves the formatted result into the resource annotation field.

If a PDF is scanned, a webpage cannot be fetched, or `OPENAI_API_KEY` is not
configured, the app shows a user-facing error message instead of saving a broken
annotation.

## Security and Content Handling

- Users only access their own projects and related resources.
- Rich-text summary and comparison HTML is sanitised before saving.
- Generated static files are served through WhiteNoise in production.
- Uploaded media is stored under `media/` in local development.
- API keys and OAuth secrets are read from environment variables.

## Access for Marking

Users can sign in with Google from the landing page, or create a local account
at:

```text
https://web-production-0b24b3.up.railway.app/accounts/signup/
```

The deployed admin panel is available at:

```text
https://web-production-0b24b3.up.railway.app/admin/
```

Admin credentials should be shared privately rather than committed to the
repository.

The subscriptions admin demonstrates:

- List display for user, plan, archived status, and created date
- Filtering by plan and archived status
- Pagination
- A custom archive action that marks subscriptions as archived instead of
  deleting them
- Standard Django admin add and edit forms

## AI Use Declaration

This project was developed with assistance from generative AI. AI support was
used to help translate the product design into Django templates, models, views,
frontend assets, editor behaviour, deployment configuration, troubleshooting
steps, and documentation drafts.

The core product idea, design direction, schema decisions, feature scope,
deployment choices, testing, and final review were directed by the developer.
AI suggestions were reviewed before being accepted or changed.

## Project Status

Annota is a working research management prototype with deployed user flows for:

- Signing up or signing in
- Creating projects
- Adding PDFs and links
- Generating AI annotations
- Writing cited summaries
- Creating comparison tables
- Searching across the workspace
- Managing records through Django admin

The app is suitable as a demonstration of a research workflow tool and as a
foundation for future collaboration, export, and deeper citation-management
features.
