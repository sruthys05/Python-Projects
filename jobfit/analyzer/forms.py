from django import forms


class AnalyzeForm(forms.Form):
    job_title = forms.CharField(max_length=200)
    job_description = forms.CharField(widget=forms.Textarea(attrs={"rows": 8}))
    candidate_name = forms.CharField(max_length=120)
    resume_file = forms.FileField(required=False, help_text="Upload a .txt resume")
    resume_text = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 6}))

    def clean(self):
        data = super().clean()
        f = data.get("resume_file")
        text = data.get("resume_text", "")
        if f:
            text = f.read().decode("utf-8", errors="ignore")   # file handling
        if not text.strip():
            raise forms.ValidationError("Provide a resume file or paste resume text.")
        data["resume_content"] = text
        return data
