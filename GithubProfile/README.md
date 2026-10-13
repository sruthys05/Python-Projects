# GitHub public profile scraper

A small Python CLI that extracts publicly visible profile details and public
repositories from GitHub profile pages using Requests and BeautifulSoup.
It does not sign in or access private account data.
Requires Python 3.10 or newer.

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

## Run

From this folder, pass a GitHub username. The default output is
`github_profile.json`:

```powershell
py -m github_profile_scraper torvalds
```

Choose a different JSON output path with `--output`:

```powershell
py -m github_profile_scraper torvalds --output .\output\torvalds.json
```

The JSON contains the profile's public name, bio, location, company, website,
public email when displayed, and public repositories with available
descriptions, languages, stars, forks, and update timestamps. GitHub's HTML
can change, so selectors may need maintenance. Use the scraper responsibly and
avoid sending requests too frequently.
