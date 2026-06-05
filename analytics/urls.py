from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import (
    RegisterViewSet,
    UserViewSet,
    DatasetViewSet,
    ChatSessionViewSet,
    AnalysisViewSet,
    DashboardViewSet,
    ExportedReportViewSet,
    EmailTokenObtainPairView,
    LogoutView,
)

router = DefaultRouter(trailing_slash=True)
router.register(r'datasets',      DatasetViewSet,        basename='dataset')
router.register(r'chat-sessions', ChatSessionViewSet,    basename='chat-session')
router.register(r'analyses',      AnalysisViewSet,       basename='analysis')
router.register(r'dashboards',    DashboardViewSet,      basename='dashboard')
router.register(r'exports',       ExportedReportViewSet, basename='export')

auth_urlpatterns = [
    path('register/',         RegisterViewSet.as_view({'post': 'create'}), name='auth-register'),
    path('login/',            EmailTokenObtainPairView.as_view(),          name='auth-login'),
    path('logout/',           LogoutView.as_view(),                        name='auth-logout'),
    path('token/refresh/',    TokenRefreshView.as_view(),                  name='auth-token-refresh'),
    path('token/verify/',     TokenVerifyView.as_view(),                   name='auth-token-verify'),
    path('me/',               UserViewSet.as_view({'get': 'me', 'patch': 'me'}), name='auth-me'),
    path('me/change-password/', UserViewSet.as_view({'post': 'change_password'}), name='auth-change-password'),
]

urlpatterns = [
    path('auth/', include((auth_urlpatterns, 'auth'))),
    path('',      include(router.urls)),
]
