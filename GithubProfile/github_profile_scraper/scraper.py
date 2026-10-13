import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

from .models import GithubProfile, Repository

BASE_URL = "https://github.com"
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")


def _text(element: Tag | None) -> str | None:
    if element is None:
        return None
    value = element.get_text(" ", strip=True)
    return value or None


def parse_profile(html: str, username: str) -> GithubProfile:
    soup = BeautifulSoup(html, "html.parser")
    details = soup.select_one(".vcard-details")

    def detail_text(selector: str) -> str | None:
        return _text(details.select_one(selector)) if details else None

    website_link = (
        details.select_one('[itemprop="url"] a, a[itemprop="url"]')
        if details
        else None
    )
    email_link = details.select_one('a[href^="mailto:"]') if details else None
    website = website_link.get("href") if website_link else None
    email = email_link.get("href", "").removeprefix("mailto:") if email_link else None

    return GithubProfile(
        username=username,
        profile_url=f"{BASE_URL}/{username}",
        name=_text(soup.select_one(".vcard-fullname")),
        bio=_text(soup.select_one(".p-note")),
        location=detail_text('[itemprop="homeLocation"]'),
        company=detail_text('[itemprop="worksFor"]'),
        website=website,
        email=email or None,
    )


def parse_repositories(html: str) -> list[Repository]:
    soup = BeautifulSoup(html, "html.parser")
    repository_items = soup.select("#user-repositories-list li")
    repositories = []

    for item in repository_items:
        name_link = item.select_one('h3 a[itemprop="name codeRepository"]') or item.select_one("h3 a")
        if name_link is None or not name_link.get("href"):
            continue

        stars_link = item.select_one('a[href$="/stargazers"]')
        forks_link = item.select_one('a[href$="/forks"]')
        updated = item.select_one("relative-time[datetime]")

        repositories.append(
            Repository(
                name=_text(name_link) or name_link["href"].rstrip("/").split("/")[-1],
                url=urljoin(BASE_URL, name_link["href"]),
                description=_text(item.select_one('[itemprop="description"]')),
                language=_text(item.select_one('[itemprop="programmingLanguage"]')),
                stars=_text(stars_link),
                forks=_text(forks_link),
                last_updated=updated.get("datetime") if updated else None,
            )
        )

    return repositories


class GithubProfileScraper:
    def __init__(self, request_delay: float = 0.5) -> None:
        self.request_delay = request_delay
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "PublicGitHubProfileScraper/1.0 (profile research)"}
        )

    def _get_html(self, url: str) -> str:
        response = self.session.get(url, timeout=20)
        response.raise_for_status()
        return response.text

    def scrape(self, username: str) -> GithubProfile:
        if not USERNAME_PATTERN.fullmatch(username):
            raise ValueError("Enter a valid GitHub username.")

        profile_url = f"{BASE_URL}/{username}"
        profile = parse_profile(self._get_html(profile_url), username)
        next_url = f"{profile_url}?tab=repositories"
        visited_urls = set()
        visited_repository_names = set()

        while next_url:
            if next_url in visited_urls:
                raise ValueError("GitHub returned a repeated repository page.")
            visited_urls.add(next_url)

            if self.request_delay:
                time.sleep(self.request_delay)

            html = self._get_html(next_url)
            page_repositories = parse_repositories(html)
            new_repositories = [
                repository
                for repository in page_repositories
                if repository.name not in visited_repository_names
            ]
            if page_repositories and not new_repositories:
                break
            profile.repositories.extend(new_repositories)
            visited_repository_names.update(
                repository.name for repository in new_repositories
            )

            soup = BeautifulSoup(html, "html.parser")
            next_link = soup.select_one('a[rel="next"]')
            next_url = (
                urljoin(BASE_URL, next_link["href"])
                if next_link and next_link.get("href")
                else ""
            )

            if next_url:
                parsed_url = urlparse(next_url)
                if parsed_url.scheme != "https" or parsed_url.netloc != "github.com":
                    raise ValueError("GitHub returned an unexpected repository pagination URL.")

        return profile
