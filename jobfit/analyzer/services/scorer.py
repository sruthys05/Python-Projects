"""Set operations + sorting to compute the fit score."""
from .parser import (extract_skills, split_job_sections, extract_years)

REQUIRED_WEIGHT, PREFERRED_WEIGHT, EXPERIENCE_WEIGHT = 0.65, 0.20, 0.15


def verdict_for(score):
    if score >= 80:
        return "Strong Fit"
    if score >= 60:
        return "Good Fit"
    if score >= 40:
        return "Partial Fit"
    return "Weak Fit"


def analyze(resume_text, job_text, catalog):
    req_text, pref_text = split_job_sections(job_text)
    required = extract_skills(req_text, catalog)
    preferred = extract_skills(pref_text, catalog) - required
    have = extract_skills(resume_text, catalog)

    matched_req = required & have            # intersection
    missing_req = required - have            # difference
    matched_pref = preferred & have
    missing_pref = preferred - have
    extra = have - (required | preferred)    # bonus skills

    req_cov = len(matched_req) / len(required) if required else 1.0
    pref_cov = len(matched_pref) / len(preferred) if preferred else 1.0

    need_years, have_years = extract_years(req_text), extract_years(resume_text)
    exp_cov = 1.0 if need_years == 0 else min(have_years / need_years, 1.0)

    score = 100 * (REQUIRED_WEIGHT * req_cov + PREFERRED_WEIGHT * pref_cov
                   + EXPERIENCE_WEIGHT * exp_cov)
    return {
        "score": round(score, 1),
        "verdict": verdict_for(score),
        "matched_required": sorted(matched_req),
        "missing_required": sorted(missing_req),
        "matched_preferred": sorted(matched_pref),
        "missing_preferred": sorted(missing_pref),
        "extra_skills": sorted(extra),
        "years_needed": need_years,
        "years_have": have_years,
    }


def rank(results):
    """Sort candidates: score desc, then fewer missing required skills, then name."""
    return sorted(results, key=lambda r: (-r["score"], len(r["missing_required"]), r["name"]))
