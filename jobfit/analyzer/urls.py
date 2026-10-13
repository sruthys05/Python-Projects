from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("result/<int:pk>/", views.result, name="result"),
    path("job/<int:job_id>/ranking/", views.leaderboard, name="leaderboard"),
]
