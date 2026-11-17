# satyaprakashdwivedi.github.io

My projects page: **https://satyaprakashdwivedi.github.io**. It lists the public repositories I've committed to in the
last 30 days.

- **Daily refresh:** [`site/build_site.py`](site/build_site.py) reads the GitHub API and regenerates `index.html`.
  A GitHub Action runs it every day, and whenever `site/` changes.
- **Hand-written content:** titles, summaries and highlights live in [`site/highlights.json`](site/highlights.json).
  A new qualifying repository still appears automatically, using its GitHub description.
- **Layout:** [`site/template.html`](site/template.html). The LinkedIn preview image is `assets/preview.png`.

Run locally: `GITHUB_TOKEN=$(gh auth token) python3 site/build_site.py`, then open `index.html`.
