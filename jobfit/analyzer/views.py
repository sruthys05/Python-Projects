from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404

from .forms import AnalyzeForm
from .models import JobPosting, Analysis
from .services.parser import load_skill_catalog
from .services.scorer import analyze


def index(request):
    form = AnalyzeForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        job, _ = JobPosting.objects.get_or_create(
            title=d["job_title"], description=d["job_description"])
        catalog = load_skill_catalog(settings.SKILLS_FILE)
        r = analyze(d["resume_content"], job.description, catalog)
        a = Analysis.objects.create(
            job=job, candidate_name=d["candidate_name"], resume_text=d["resume_content"],
            score=r["score"], verdict=r["verdict"],
            matched_required=",".join(r["matched_required"]),
            missing_required=",".join(r["missing_required"]),
            matched_preferred=",".join(r["matched_preferred"]),
            missing_preferred=",".join(r["missing_preferred"]),
            extra_skills=",".join(r["extra_skills"]))
        return redirect("result", pk=a.pk)
    return render(request, "analyzer/index.html", {"form": form})


def result(request, pk):
    a = get_object_or_404(Analysis, pk=pk)
    return render(request, "analyzer/result.html", {"a": a})


def leaderboard(request, job_id):
    job = get_object_or_404(JobPosting, pk=job_id)
    return render(request, "analyzer/leaderboard.html",
                  {"job": job, "analyses": job.analyses.all()})  # already sorted by score
