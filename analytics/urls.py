"""
urls.py  (app-level)
─────────────────────────────────────────────────────────────
Mount this file in your project-level urls.py:

    from django.urls import path, include

    urlpatterns = [
        path("api/", include("your_app.urls")),
        ...
    ]

Full URL map
────────────────────────────────────────────────────────────
AUTH
  POST   /api/auth/register/
  POST   /api/auth/login/                 (JWT access + refresh)
  POST   /api/auth/token/refresh/
  POST   /api/auth/token/verify/
  GET    /api/auth/me/
  PATCH  /api/auth/me/
  POST   /api/auth/me/change-password/

DATASETS
  GET    /api/datasets/
  POST   /api/datasets/                   (multipart upload)
  GET    /api/datasets/{id}/
  DELETE /api/datasets/{id}/
  POST   /api/datasets/{id}/run-analysis/

CHAT
  GET    /api/chat-sessions/
  POST   /api/chat-sessions/
  GET    /api/chat-sessions/{id}/
  PATCH  /api/chat-sessions/{id}/
  DELETE /api/chat-sessions/{id}/
  POST   /api/chat-sessions/{id}/send-message/
  GET    /api/chat-sessions/{id}/messages/

ANALYSIS
  GET    /api/analyses/
  GET    /api/analyses/{id}/

DASHBOARDS
  GET    /api/dashboards/
  POST   /api/dashboards/
  GET    /api/dashboards/{id}/
  DELETE /api/dashboards/{id}/
  POST   /api/dashboards/generate/
  POST   /api/dashboards/{id}/export/
  GET    /api/dashboards/{id}/exports/

EXPORTS
  GET    /api/exports/
  GET    /api/exports/{id}/
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import (
    RegisterViewSet,
    UserViewSet,
    DatasetViewSet,
    ChatSessionViewSet,
    AnalysisViewSet,
    DashboardViewSet,
    ExportedReportViewSet,
    EmailTokenObtainPairView,
)

router = DefaultRouter(trailing_slash=True)
router.register(r"datasets",      DatasetViewSet,       basename="dataset")
router.register(r"chat-sessions", ChatSessionViewSet,   basename="chat-session")
router.register(r"analyses",      AnalysisViewSet,      basename="analysis")
router.register(r"dashboards",    DashboardViewSet,     basename="dashboard")
router.register(r"exports",       ExportedReportViewSet, basename="export")

auth_urlpatterns = [
    path(
        "register/",
        RegisterViewSet.as_view({"post": "create"}),
        name="auth-register",
    ),
    path("login/", EmailTokenObtainPairView.as_view(), name="auth-login"),
    path("token/refresh/", TokenRefreshView.as_view(),    name="auth-token-refresh"),
    path("token/verify/",  TokenVerifyView.as_view(),     name="auth-token-verify"),
    path(
        "me/",
        UserViewSet.as_view({"get": "me", "patch": "me"}),
        name="auth-me",
    ),
    path(
        "me/change-password/",
        UserViewSet.as_view({"post": "change_password"}),
        name="auth-change-password",
    ),
]

urlpatterns = [
    path("auth/", include((auth_urlpatterns, "auth"))),
    path("",       include(router.urls)),
]