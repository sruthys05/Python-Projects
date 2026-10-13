# GFG Article Scraper

A beginner-friendly Python program that downloads one GeeksforGeeks article and saves its title and paragraphs as a PDF.

## Install dependencies

Run this command in the project terminal:

```bash
pip install requests beautifulsoup4 fpdf2
```

Or install the packages listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Run

```bash
python scraper.py
```

Paste a GeeksforGeeks article URL when prompted. The PDF is saved to `output/article.pdf`.
