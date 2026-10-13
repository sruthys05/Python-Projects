from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup, Comment
    from fpdf import FPDF
except ImportError as error:
    missing_package = error.name or "a required package"
    print(f"Missing package: {missing_package}")
    print("Install the packages with: python -m pip install requests beautifulsoup4 fpdf2")
    raise SystemExit(1) from error


class ArticleContentError(Exception):
    """Raised when the article container or readable article content is missing."""


def get_url() -> str:
    """Ask for and validate a GeeksforGeeks article URL."""
    url = input("Enter GFG article URL: ").strip()
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname or ""
    except ValueError as error:
        raise ValueError("The URL is not valid.") from error

    is_geeksforgeeks = hostname == "geeksforgeeks.org" or hostname.endswith(
        ".geeksforgeeks.org"
    )
    if parsed_url.scheme not in ("http", "https") or not is_geeksforgeeks:
        raise ValueError("Enter a valid HTTP or HTTPS GeeksforGeeks article URL.")

    return url


def download_page(url: str) -> str:
    """Download a webpage and return its HTML."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.text


def extract_article(html: str) -> tuple[str, list[str]]:
    """Extract the title and typed text blocks from the article container."""
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("h1")

    article = soup.select_one("div.article--viewer_content")
    if article is None:
        article = soup.find("article")
    if article is None:
        article = soup.find("main")
    if article is None:
        raise ArticleContentError("Could not find the article content container.")

    for comment in article.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    unwanted_words = (
        "comment",
        "advert",
        "related",
        "recommend",
        "newsletter",
        "social-share",
    )
    for element in article.select("script, style, nav, iframe, button"):
        element.decompose()
    elements_to_remove = []
    for element in article.find_all(True):
        element_names = " ".join(
            [str(element.get("id", "")), " ".join(element.get("class", []))]
        ).lower()
        if any(word in element_names for word in unwanted_words):
            if not any(parent in elements_to_remove for parent in element.parents):
                elements_to_remove.append(element)
    for element in elements_to_remove:
        element.decompose()

    title = title_tag.get_text(" ", strip=True) if title_tag else ""
    content = []
    for element in article.find_all(["h2", "h3", "h4", "p", "li", "pre"]):
        text = element.get_text(" ", strip=True)
        if not text:
            continue
        if element.name in ("h2", "h3", "h4"):
            content.append(("heading", text))
        elif element.name == "li":
            content.append(("list", text))
        elif element.name == "pre":
            content.append(("code", element.get_text("\n", strip=True)))
        else:
            content.append(("paragraph", text))

    if not title:
        raise ArticleContentError("Could not find an article title in an h1 tag.")
    if not content:
        raise ArticleContentError("The article container did not contain readable text.")

    return title, content


def create_output_folder() -> Path:
    """Create the output folder next to this script if needed."""
    output_folder = Path(__file__).resolve().parent / "output"
    output_folder.mkdir(exist_ok=True)
    return output_folder


def create_pdf(title: str, content: list[tuple[str, str]]) -> Path:
    """Write the title and article blocks to output/gfg_article.pdf."""
    output_folder = create_output_folder()
    pdf_path = output_folder / "gfg_article.pdf"

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def pdf_safe_text(text: str) -> str:
        """Replace characters unsupported by FPDF's built-in fonts."""
        return text.encode("latin-1", errors="replace").decode("latin-1")

    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, pdf_safe_text(title))
    pdf.ln(4)

    for item_type, text in content:
        if item_type == "heading":
            pdf.set_font("Helvetica", "B", 13)
            pdf.ln(2)
        elif item_type == "code":
            pdf.set_font("Courier", size=9)
        else:
            pdf.set_font("Helvetica", size=11)

        if item_type == "list":
            text = f"* {text}"
        pdf.multi_cell(0, 6, pdf_safe_text(text))
        pdf.ln(2)

    pdf.output(str(pdf_path))
    return pdf_path


def main() -> None:
    """Run the scraper and report useful progress or errors."""
    try:
        url = get_url()
    except ValueError as error:
        print(f"Invalid URL: {error}")
        return

    try:
        print("Downloading GFG article...")
        html = download_page(url)
    except requests.exceptions.HTTPError as error:
        status_code = error.response.status_code if error.response else "unknown"
        if status_code == 403:
            print("HTTP error 403 Forbidden: GeeksforGeeks refused this request.")
        else:
            print(f"HTTP error {status_code}: {error}")
        return
    except requests.exceptions.RequestException as error:
        print(f"Network error: {error}")
        return

    try:
        title, paragraphs = extract_article(html)
    except ArticleContentError as error:
        print(f"Article content not found: {error}")
        return

    print(f"Article found: {title}")
    print(f"Content items: {len(content)}")
    print("\n--- ARTICLE PREVIEW ---")
    print(f"Title: {title}\n")
    for index, (item_type, text) in enumerate(content[:5], start=1):
        preview_text = f"* {text}" if item_type == "list" else text
        print(f"{index}. {preview_text}")
    print("\n--- END PREVIEW ---")

    try:
        pdf_path = create_pdf(title, content)
    except Exception as error:
        print(f"PDF generation error: {error}")
        return

    print("PDF created successfully!")
    print(f"Open: {pdf_path.relative_to(Path(__file__).resolve().parent).as_posix()}")


if __name__ == "__main__":
    main()
