# osint-harvester

![Python](https://img.shields.io/badge/Language-Python-3776AB?style=flat-square)
![Playwright](https://img.shields.io/badge/Automation-Playwright-2EAD33?style=flat-square)
![License](https://img.shields.io/badge/License-Research--only-lightgrey?style=flat-square)

> Web intelligence collector built on Playwright.

An open-source-intelligence (OSINT) harvesting tool that drives a headless browser to visit target pages and collect public data into structured output files for further analysis.

---

## Features

- **Playwright-driven scraping** - reliable navigation of modern, JavaScript-heavy pages
- **Injected collector** - browser-side script gathers page data where a pure HTTP client cannot
- **Structured output** - results saved under `output/` as JSON and plain-text dumps
- **Headless operation** - designed to run unattended

---

## Project structure

```
osint-harvester/
├── scripts/
│   ├── scraper.py    # Playwright-driven scraper (entry point)
│   └── console.js    # Browser-side collector injected by the scraper
└── output/           # Collected results
```

---

## Requirements

- Python **3.8+**
- `pip install playwright`, then install a browser:

  ```bash
  pip install playwright
  playwright install
  ```

- A Chromium / Edge browser binary for Playwright

---

## Usage

```bash
python scripts/scraper.py
```

Configure the target list at the top of `scraper.py` before running. Results are written to `output/`.

---

## Disclaimer

Use this tool solely for **authorized intelligence gathering** on data that is public and lawful to collect. Respect target terms of service, privacy laws, and rate limits.