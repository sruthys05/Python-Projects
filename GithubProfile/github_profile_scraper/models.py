from dataclasses import dataclass, field


@dataclass
class Repository:
    name: str
    url: str
    description: str | None = None
    language: str | None = None
    stars: str | None = None
    forks: str | None = None
    last_updated: str | None = None


@dataclass
class GithubProfile:
    username: str
    profile_url: str
    name: str | None = None
    bio: str | None = None
    location: str | None = None
    company: str | None = None
    website: str | None = None
    email: str | None = None
    repositories: list[Repository] = field(default_factory=list)
