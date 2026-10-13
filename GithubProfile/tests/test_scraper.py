import unittest

from github_profile_scraper.scraper import parse_profile, parse_repositories


class ParseProfileTests(unittest.TestCase):
    def test_extracts_public_profile_fields(self):
        html = """
        <span class="vcard-fullname">Ada Lovelace</span>
        <div class="p-note">Analytical engine enthusiast</div>
        <ul class="vcard-details">
          <li itemprop="homeLocation">London</li>
          <li itemprop="worksFor">Analytical Engines</li>
          <li itemprop="url"><a href="https://example.com">Website</a></li>
          <li><a href="mailto:ada@example.com">Email</a></li>
        </ul>
        """

        profile = parse_profile(html, "ada")

        self.assertEqual(profile.username, "ada")
        self.assertEqual(profile.name, "Ada Lovelace")
        self.assertEqual(profile.bio, "Analytical engine enthusiast")
        self.assertEqual(profile.location, "London")
        self.assertEqual(profile.company, "Analytical Engines")
        self.assertEqual(profile.website, "https://example.com")
        self.assertEqual(profile.email, "ada@example.com")


class ParseRepositoriesTests(unittest.TestCase):
    def test_extracts_repository_details(self):
        html = """
        <div id="user-repositories-list">
          <ul><li>
            <h3><a itemprop="name codeRepository" href="/ada/engine">engine</a></h3>
            <p itemprop="description">An analytical engine</p>
            <span itemprop="programmingLanguage">Python</span>
            <a href="/ada/engine/stargazers">42</a>
            <a href="/ada/engine/forks">7</a>
            <relative-time datetime="2026-01-02T03:04:05Z">recently</relative-time>
          </li></ul>
        </div>
        """

        repositories = parse_repositories(html)

        self.assertEqual(len(repositories), 1)
        repository = repositories[0]
        self.assertEqual(repository.name, "engine")
        self.assertEqual(repository.url, "https://github.com/ada/engine")
        self.assertEqual(repository.description, "An analytical engine")
        self.assertEqual(repository.language, "Python")
        self.assertEqual(repository.stars, "42")
        self.assertEqual(repository.forks, "7")
        self.assertEqual(repository.last_updated, "2026-01-02T03:04:05Z")

    def test_ignores_repository_items_without_a_link(self):
        html = '<div id="user-repositories-list"><ul><li><h3>Hidden</h3></li></ul></div>'

        self.assertEqual(parse_repositories(html), [])


if __name__ == "__main__":
    unittest.main()
