from django.db import models


class JobPosting(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Analysis(models.Model):
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name="analyses")
    candidate_name = models.CharField(max_length=120)
    resume_text = models.TextField()
    score = models.FloatField()
    verdict = models.CharField(max_length=30)
    matched_required = models.TextField(blank=True)
    missing_required = models.TextField(blank=True)
    matched_preferred = models.TextField(blank=True)
    missing_preferred = models.TextField(blank=True)
    extra_skills = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-score", "candidate_name"]   # sorting at DB level

    def _split(self, value):
        return [s for s in value.split(",") if s]

    @property
    def matched_required_list(self): return self._split(self.matched_required)
    @property
    def missing_required_list(self): return self._split(self.missing_required)
    @property
    def matched_preferred_list(self): return self._split(self.matched_preferred)
    @property
    def missing_preferred_list(self): return self._split(self.missing_preferred)
    @property
    def extra_skills_list(self): return self._split(self.extra_skills)

    def __str__(self):
        return f"{self.candidate_name} - {self.score}%"
