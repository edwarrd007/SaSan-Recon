<div align="center">
  <img src="https://raw.githubusercontent.com/edwarrd007/SaSan-Recon/2003fd6c1bf9b5c520e4fda7c66567836ef206c3/assets/banner.svg" alt="SaSaN-Recon banner" width="100%">
</div>

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Selenium](https://img.shields.io/badge/Selenium-Web_Automation-43B02A?style=for-the-badge&logo=selenium&logoColor=white)](https://www.selenium.dev/)
[![OSINT](https://img.shields.io/badge/Focus-OSINT-111827?style=for-the-badge)](#)
[![Recon](https://img.shields.io/badge/Workflow-Recon-7C3AED?style=for-the-badge)](#)
[![JSON](https://img.shields.io/badge/Storage-JSON-F7DF1E?style=for-the-badge&logo=json&logoColor=111827)](#)

**Automated search-engine reconnaissance and asset extraction for authorized security research.**

</div>

---

## Overview

**SaSaN-Recon** is a modular Python reconnaissance tool that collects search-engine results from configured dorks, preserves the raw HTML source, and then extracts useful indicators such as URLs, domains, IPv4 addresses, e-mails, hashes, JWT-like tokens, paths, and security-related strings.

The project is intentionally split into two main stages:

```text
┌──────────────────────────┐
│        dorks.json        │
│  targets + dork queries  │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│         dork.py          │
│ Selenium / search engines│
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│          JSON            │
│ timestamp-keyed records  │
│ + raw HTML source        │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│         main.py          │
│ extraction pipeline      │
└────────────┬─────────────┘
             │
       ┌─────┴─────┐
       ▼           ▼
┌────────────┐ ┌──────────────┐
│ extractor  │ │   analyzer   │
│ raw assets │ │ classification│
└─────┬──────┘ └──────┬───────┘
      └────────┬──────┘
               ▼
      ┌──────────────────┐
      │ results / JSON   │
      └──────────────────┘
```

> **Use only on systems, domains, and data you are authorized to assess.**

---

## Features

| Feature | Description |
|---|---|
| 🔎 Dork collection | Runs configured dorks against supported search engines through Selenium. |
| 🌐 Multi-engine workflow | Keeps each engine's results separated. |
| 🧾 Raw HTML capture | Stores `page_source` so extraction can be repeated later without another search. |
| 🕒 Timestamped storage | Every saved record uses the date/time as the JSON root key. |
| 🧩 Modular extraction | `Extractor` handles URL, domain, IP, e-mail, hash, JWT, path and related patterns. |
| 🧠 Optional analysis | `AssetAnalyzer` can classify/validate extracted values after raw extraction. |
| 📁 Program separation | Results can be grouped per program/target. |
| ♻️ Re-processing | Run `main.py` again against previously collected JSON without reopening the browser. |

---

## Project Structure

```text
SaSaN-Recon/
│
├── dork.py                         # Search-engine collector
├── main.py                         # Extraction / analysis pipeline
├── extractor.py                    # Regex-based asset extraction
├── analyzer.py                     # Optional asset analysis
├── storage.py                      # JSON result storage helpers
├── config.py                       # Program / target / path configuration
├── dorks.json                      # Dork definitions
│
├── results/
│   └── <program>/
│       ├── search-engine-html-sources.json
│       ├── <engine>/
│       │   └── <target>.json
│       └── ...
│
└── assets/
    └── banner.svg
```

### What each file does

**`dork.py`**  
Opens the configured search engines with Selenium, executes dorks, waits for the manual/browser interaction when required, extracts links, captures the current page HTML, and saves the collection data.

**`main.py`**  
Reads all previously collected timestamp-keyed records and sends their `html_source` values to `Extractor`. It then merges/deduplicates the discovered assets and can run `AssetAnalyzer`.

**`extractor.py`**  
Contains the extraction rules. Typical categories include:

```text
URL
DOMAIN
IPv4
EMAIL
HASH
JWT
PATH
SECURITY / SECRET-LIKE LINES
```

**`analyzer.py`**  
Runs additional checks/classification on the raw assets after extraction.

**`storage.py`**  
Handles result serialization and JSON persistence.

**`config.py`**  
Stores values such as the selected program, target and output locations.

**`dorks.json`**  
Defines the search queries used by the collector.

---

## Requirements

- Python **3.10+**
- Firefox
- Selenium
- Internet access
- A configured `dorks.json`

Install the Python dependencies from your project environment. For example:

```bash
python -m venv .venv
```

### Windows

```powershell
.\.venv\Scripts\Activate.ps1
pip install selenium
```

### Linux

```bash
source .venv/bin/activate
pip install selenium
```

Selenium can use modern driver management, but Firefox itself must be installed and accessible.

---

## Configuration

Before running the project, configure the program and target in your project configuration.

A typical reconnaissance session looks like:

```text
Program : semtech
Target  : www.semtech.com
```

For another target, use another program directory so the collected data stays separated.

Example:

```text
results/
├── semtech/
│   ├── search-engine-html-sources.json
│   └── ...
│
└── bmw/
    ├── search-engine-html-sources.json
    └── ...
```

This makes it easier to keep campaigns isolated instead of mixing assets from different targets.

---

## Dorks

`dorks.json` is the input used by `dork.py` to determine what to search.

A dork is simply a search-engine query designed to narrow the results to a useful category of information.

Example search ideas:

```text
site:example.com
site:example.com filetype:pdf
site:example.com inurl:login
site:example.com intitle:index.of
site:example.com inurl:api
site:example.com ext:js
```

For a real engagement, replace `example.com` with the authorized target.

> Keep your actual organization-specific dorks private when they contain sensitive or internal information.

---

# 1. Run the Collector

The first stage is `dork.py`.

```bash
python dork.py
```

The collector will:

```text
1. Load the dork configuration
2. Start the configured search engine browser sessions
3. Open the generated search URLs
4. Let the operator complete any required human verification
5. Collect result links
6. Capture the page HTML source
7. Save the collection to JSON
```

A typical flow is:

```text
[dorks.json]
      │
      ▼
   dork.py
      │
      ▼
 Selenium / Firefox
      │
      ▼
 Search result pages
      │
      ▼
 page_source + links
      │
      ▼
 results/<program>/...
```

---

# 2. Understand the Collector JSON

SaSaN-Recon uses the **timestamp itself as the root JSON key**.

This is important because each new run creates a new record instead of overwriting an older record.

Example:

```json
{
  "2026-10-05 12:40:21.123456": {
    "application": "SaSaN-Recon",
    "program": "semtech",
    "target": "www.semtech.com",
    "engine": "google",
    "data": {
      "pages": [
        {
          "url": "https://www.google.com/search?...",
          "links": [
            "https://www.semtech.com/...",
            "https://example.org/..."
          ],
          "html_source": "<html>...</html>"
        }
      ]
    }
  },
  "2026-10-05 12:43:17.882341": {
    "application": "SaSaN-Recon",
    "program": "semtech",
    "target": "www.semtech.com",
    "engine": "bing",
    "data": {
      "pages": [
        {
          "url": "https://www.bing.com/search?...",
          "links": [
            "https://www.semtech.com/..."
          ],
          "html_source": "<html>...</html>"
        }
      ]
    }
  }
}
```

### Why use the timestamp as the key?

Instead of:

```json
{
  "date": "2026-10-05 12:40:21",
  "data": {}
}
```

SaSaN-Recon stores:

```json
{
  "2026-10-05 12:40:21.123456": {
    "data": {}
  }
}
```

So every timestamp becomes a unique record identifier.

---

# 3. Run the Extractor

After the collector has finished, run:

```bash
python main.py
```

`main.py` reads the previously stored records and processes **all timestamp keys**.

The logical pipeline is:

```text
JSON record
   │
   ├── application
   ├── program
   ├── target
   ├── engine
   └── data.pages[].html_source
                  │
                  ▼
             Extractor
                  │
        ┌─────────┼──────────┐
        ▼         ▼          ▼
       URLs     Domains      IPs
        │         │          │
        ├────── Emails       │
        ├────── Hashes       │
        ├────── JWTs         │
        └────── Paths        │
                  │
                  ▼
             AssetAnalyzer
                  │
                  ▼
               Results
```

---

## What Does `Extractor` Find?

### URL

Example input:

```html
<a href="https://www.example.com/admin/login">Login</a>
```

Possible result:

```text
https://www.example.com/admin/login
```

### Domain

Example:

```text
api.example.com
cdn.example.com
mail.example.org
```

### IPv4

Example:

```text
192.168.1.10
8.8.8.8
203.0.113.20
```

The extractor can validate candidate IPv4 values instead of blindly treating every four-number sequence as an address.

### E-mail

Example:

```text
security@example.com
admin@example.org
```

### Hash

The extractor can identify hexadecimal strings matching common hash lengths, such as:

```text
32 hex characters  -> MD5-like
40 hex characters  -> SHA-1-like
64 hex characters  -> SHA-256-like
96 hex characters  -> SHA-384-like
128 hex characters -> SHA-512-like
```

> A matching length does **not** prove the algorithm. It only indicates that the value has the expected shape/length.

### JWT-like values

Example shape:

```text
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMifQ.signature
```

The extractor looks for the common three-part JWT structure.

### Paths

Examples:

```text
/admin
/login
/api/v1/users
/.well-known/security.txt
/config/settings.json
```

### Security-related lines

The extraction rules can also locate lines containing security-sensitive keywords such as:

```text
api_key
access_token
client_secret
authorization
password
passwd
secret
```

This is only a **pattern-based discovery mechanism**. A match should always be manually verified before it is treated as a real secret.

---

# Example: From HTML to Assets

Suppose the saved search page contains:

```html
<html>
  <a href="https://portal.example.com/login">Login</a>
  <a href="https://api.example.com/v1/users">API</a>
  <script src="https://cdn.example.net/app.js"></script>
  <p>Contact: security@example.com</p>
  <p>Server: 203.0.113.25</p>
</html>
```

The extraction stage can produce data conceptually similar to:

```json
{
  "urls": [
    "https://portal.example.com/login",
    "https://api.example.com/v1/users",
    "https://cdn.example.net/app.js"
  ],
  "domains": [
    "portal.example.com",
    "api.example.com",
    "cdn.example.net"
  ],
  "ipv4": [
    "203.0.113.25"
  ],
  "emails": [
    "security@example.com"
  ]
}
```

The exact final JSON structure depends on the current `storage.py` implementation and analyzer output.

---

# Search Engine Separation

The collector keeps engines distinguishable through the `engine` field.

Example:

```json
{
  "2026-10-05 12:40:21.123456": {
    "program": "semtech",
    "target": "www.semtech.com",
    "engine": "google",
    "data": {}
  },
  "2026-10-05 12:43:17.882341": {
    "program": "semtech",
    "target": "www.semtech.com",
    "engine": "bing",
    "data": {}
  }
}
```

This means the extraction stage can process Google, Bing, Yahoo, DuckDuckGo, or other configured engines without needing a different parser for every engine.

---

# Program-Based Result Storage

Keeping targets in separate program folders is useful for long-running assessments.

```text
results/
│
├── semtech/
│   ├── search-engine-html-sources.json
│   ├── google/
│   ├── bing/
│   └── ...
│
├── bmw/
│   ├── search-engine-html-sources.json
│   ├── google/
│   ├── bing/
│   └── ...
│
└── example-program/
    └── ...
```

So when you later review a campaign, you know exactly which data belongs to which target/program.

---

# Re-Processing Existing Data

One of the biggest advantages of storing the raw HTML is that you can improve the extractor later without repeating the browser collection step.

```text
Old collection
      │
      ▼
search-engine-html-sources.json
      │
      ▼
 update extractor.py
      │
      ▼
     main.py
      │
      ▼
new extraction results
```

For example, if tomorrow you add a new regex for:

```text
AWS-style identifiers
GitHub URLs
Cloud endpoints
Source-map references
Internal hostnames
```

you can run the extraction pipeline again against the stored HTML.

---

# Typical Workflow

```bash
# Step 1 — configure the target and dorks
# Edit config.py / dorks.json

# Step 2 — collect search pages
python dork.py

# Step 3 — extract assets from saved HTML
python main.py
```

Recommended workflow during development:

```text
Configure
   ↓
Collect
   ↓
Inspect raw JSON
   ↓
Extract
   ↓
Inspect assets
   ↓
Improve extractor/analyzer
   ↓
Re-run main.py
```

---

# Troubleshooting

## `pages=0`

If `main.py` shows something like:

```text
[google] pages=0
[bing] pages=0
```

check:

```text
1. Is the source JSON path correct?
2. Does the JSON use timestamp keys at the root?
3. Does each timestamp record contain `data.pages`?
4. Does every page contain a string `html_source`?
5. Did you regenerate the collection after changing the collector?
```

A valid page record should contain something structurally similar to:

```json
{
  "url": "https://...",
  "links": [],
  "html_source": "<html>...</html>"
}
```

## `Raw extracted assets: all 0`

First check the raw HTML length.

A useful temporary debug line in `main.py` is:

```python
print(f"  html_length={len(html_source)}")
```

Interpretation:

```text
html_length = 0
    ↓
Collection/storage problem

html_length > 0 + assets = 0
    ↓
Extraction-rule problem
```

Also make sure `extractor.py` contains valid Python regex strings and was not accidentally altered by Markdown formatting.

---

# Security & Privacy

SaSaN-Recon is a reconnaissance utility, not a permission system.

Use it only for:

```text
✅ Your own infrastructure
✅ Authorized penetration tests
✅ Bug bounty programs within scope
✅ Security research with explicit permission
```

Do not use it to collect or exploit information from systems you do not have permission to assess.

Search results can contain personal information, credentials, tokens, internal URLs, or other sensitive material. Store collected JSON carefully and avoid publishing real secrets in public repositories.

---

# Responsible Handling of Collected Data

Because `dork.py` stores raw HTML, the output may contain more information than the final extracted asset list.

For public GitHub repositories:

```text
DO NOT COMMIT
├── real access tokens
├── real passwords
├── private API keys
├── internal-only domains
├── private customer data
└── raw sensitive search captures
```

Add sensitive result directories to `.gitignore`, for example:

```gitignore
results/
*.local.json
.env
```

Keep safe example data in a separate folder such as:

```text
examples/
└── sample-search-engine-html-sources.json
```

---

# Example Mini Dataset

A safe public example can look like this:

```json
{
  "2026-10-05 12:40:21.123456": {
    "application": "SaSaN-Recon",
    "program": "example",
    "target": "example.com",
    "engine": "google",
    "data": {
      "pages": [
        {
          "url": "https://www.google.com/search?q=site%3Aexample.com",
          "links": [
            "https://example.com/",
            "https://api.example.com/docs"
          ],
          "html_source": "<html><body>security@example.com 203.0.113.10</body></html>"
        }
      ]
    }
  }
}
```

The example uses documentation-safe values and should not be treated as a real target.

---

# Extending the Project

The modular design makes it easy to add new capabilities.

### Add a new extractor

Inside `extractor.py`, add a compiled regular expression and expose it from `extract()`.

Conceptually:

```python
NEW_RE = re.compile(r"your-pattern", re.I)
```

Then:

```python
results["new_type"] = sorted(set(NEW_RE.findall(text)))
```

### Add a new analyzer rule

Keep raw extraction separate from validation/classification.

```text
Extractor
   ↓
"What strings exist?"

Analyzer
   ↓
"What do these strings probably represent?"
```

This separation makes the project easier to maintain and test.

### Add another search engine

The collector can be extended by adding another engine definition to the search workflow while keeping the same storage contract:

```text
engine
program
 target
 data.pages[]
     ├── url
     ├── links
     └── html_source
```

The extractor does not need to know which search engine produced the HTML.

---

# Design Philosophy

SaSaN-Recon follows four simple ideas:

```text
1. Collect once
2. Preserve raw evidence
3. Extract separately
4. Analyze independently
```

This prevents the browser collection stage from becoming tightly coupled to the extraction logic.

---

# Roadmap Ideas

Potential future modules include:

```text
[ ] URL normalization
[ ] Domain / subdomain classification
[ ] URL parameter extraction
[ ] JavaScript endpoint discovery
[ ] Source-map detection
[ ] Cloud asset detection
[ ] Technology fingerprinting
[ ] DNS enrichment
[ ] IP / ASN enrichment
[ ] Evidence snapshots
[ ] SQLite backend
[ ] Export to CSV / Markdown
[ ] Concurrent extraction workers
```

These are natural extensions because the raw HTML is already preserved as evidence.

---

# Credits

**SaSaN-Recon** is a modular reconnaissance project built with Python and Selenium, focused on repeatable collection, structured storage, and asset extraction.

<div align="center">

**SaSaN-Recon**  •  **Collect → Extract → Analyze**

</div>
