"""Run without Django:  python cli.py"""
from pathlib import Path
from analyzer.services.parser import load_skill_catalog, read_text_file, extract_email
from analyzer.services.scorer import analyze, rank

BASE = Path(__file__).parent / "data"
catalog = load_skill_catalog(BASE / "skills.txt")
job_text = read_text_file(BASE / "sample_job.txt")

results = []
for f in sorted(BASE.glob("sample_resume_*.txt")):
    text = read_text_file(f)
    r = analyze(text, job_text, catalog)
    r["name"] = f.stem.replace("sample_resume_", "").title()
    r["email"] = extract_email(text)
    results.append(r)

print("=" * 62)
print("JOB FIT ANALYSER - Python Backend Developer")
print("=" * 62)
for pos, r in enumerate(rank(results), 1):
    print(f"\n#{pos}  {r['name']} <{r['email']}>")
    print(f"    Score   : {r['score']}%  ->  {r['verdict']}")
    print(f"    Experience: {r['years_have']} yrs (needs {r['years_needed']})")
    print(f"    Matched required : {', '.join(r['matched_required']) or '-'}")
    print(f"    Missing required : {', '.join(r['missing_required']) or '-'}")
    print(f"    Matched preferred: {', '.join(r['matched_preferred']) or '-'}")
    print(f"    Missing preferred: {', '.join(r['missing_preferred']) or '-'}")
    print(f"    Extra skills     : {', '.join(r['extra_skills']) or '-'}")
