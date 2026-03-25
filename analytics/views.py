from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import EmailTokenObtainPairSerializer

import logging
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView

from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    UserProfile, Dataset, ChatSession,
    ChatMessage, Analysis, Dashboard, ExportedReport,
)
from .serializers import (
    UserSerializer, RegisterSerializer, ChangePasswordSerializer,
    DatasetListSerializer, DatasetUploadSerializer, DatasetDetailSerializer,
    ChatSessionListSerializer, ChatSessionDetailSerializer,
    ChatSessionCreateSerializer, ChatSessionUpdateSerializer,
    ChatMessageSerializer, SendMessageSerializer,
    AnalysisListSerializer, AnalysisDetailSerializer, TriggerAnalysisSerializer,
    DashboardListSerializer, DashboardDetailSerializer, DashboardCreateSerializer,
    ExportedReportSerializer, TriggerExportSerializer,
)
from .services.services import (
    parse_uploaded_file,       # extracts rows/cols/column_names from CSV/Excel
    run_eda_analysis,          # runs pandas EDA, returns Analysis instance
    generate_dashboard_config, # builds layout_config JSON for Dashboard
    export_dashboard_report,   # generates PDF/ipynb/py file, returns ExportedReport
    handle_chat_turn,          # processes user message, returns assistant reply + updated session
)

logger = logging.getLogger(__name__)

class ChatRateThrottle(UserRateThrottle):
    scope = "chat"          # configure in settings: REST_FRAMEWORK.DEFAULT_THROTTLE_RATES


class UploadRateThrottle(UserRateThrottle):
    scope = "upload"


class AnalysisRateThrottle(UserRateThrottle):
    scope = "analysis"

class RegisterViewSet(viewsets.GenericViewSet):
    """POST /api/auth/register/"""
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            self.get_serializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class UserViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    @action(detail=False, methods=["get", "patch"], url_path="me")
    def me(self, request):
        user = request.user
        if request.method == "GET":
            return Response(UserSerializer(user, context={"request": request}).data)

        serializer = UserSerializer(user, data=request.data, partial=True,
                                    context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="me/change-password")
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data,
                                              context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response({"detail": "Password updated successfully."})


class DatasetViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    throttle_classes = [UserRateThrottle]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "file_type"]
    search_fields = ["name"]
    ordering_fields = ["created_at", "file_size", "rows"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Dataset.objects.filter(user=self.request.user).order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return DatasetUploadSerializer
        if self.action in ("retrieve",):
            return DatasetDetailSerializer
        return DatasetListSerializer

    def get_throttles(self):
        if self.action == "create":
            return [UploadRateThrottle()]
        return super().get_throttles()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dataset = serializer.save()

        # Parse file metadata in the same request (fast op — just read headers)
        try:
            parse_uploaded_file(dataset)
        except Exception as exc:
            logger.error("File parsing failed for dataset %s: %s", dataset.id, exc)
            dataset.status = "failed"
            dataset.save(update_fields=["status"])

        headers = self.get_success_headers(serializer.data)
        return Response(
            DatasetDetailSerializer(dataset, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    # Prevent PATCH/PUT — datasets are immutable after upload
    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Dataset files cannot be modified. Upload a new dataset."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @action(
        detail=True,
        methods=["post"],
        url_path="run-analysis",
        throttle_classes=[AnalysisRateThrottle],
    )
    def run_analysis(self, request, pk=None):
        """Trigger EDA or ML analysis on a dataset."""
        dataset = self.get_object()

        if dataset.status not in ("uploaded", "completed"):
            return Response(
                {"detail": f"Cannot analyse dataset with status '{dataset.status}'."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = TriggerAnalysisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        chat_session_id = data.get("chat_session_id")

        if chat_session_id:
            existing = Analysis.objects.filter(
                chat_session_id=chat_session_id
            ).first()
            if existing:
                return Response(
                    AnalysisDetailSerializer(existing, context={"request": request}).data,
                    status=status.HTTP_200_OK,
                )

        try:
            analysis = run_eda_analysis(
                dataset=dataset,
                analysis_type=data["analysis_type"],
                chat_session_id=chat_session_id,
            )
        except Exception as exc:
            logger.exception("Analysis failed for dataset %s", dataset.id)

            return Response(
                {
                    "detail": "Analysis failed. Please try again.", 
                    "error": f"{exc}" 
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            AnalysisDetailSerializer(analysis, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ChatSessionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["is_complete", "analysis_type"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            ChatSession.objects
            .filter(user=self.request.user)
            .annotate(message_count=Count("messages"))
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return ChatSessionCreateSerializer
        if self.action in ("update", "partial_update"):
            return ChatSessionUpdateSerializer
        if self.action == "retrieve":
            return ChatSessionDetailSerializer
        return ChatSessionListSerializer

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True  # always partial update for sessions
        return super().update(request, *args, **kwargs)

    @action(
        detail=True,
        methods=["post"],
        url_path="send-message",
        throttle_classes=[ChatRateThrottle],
    )
    def send_message(self, request, pk=None):
        """
        Accept a user message, persist it, call the AI service,
        persist the assistant reply, and return both.
        """
        session = self.get_object()

        if session.is_complete:
            return Response(
                {"detail": "This chat session is already complete."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_content = serializer.validated_data["content"]

        user_msg = ChatMessage.objects.create(
            session=session, role="user", content=user_content
        )

        try:
            assistant_content, updated_session = handle_chat_turn(session, user_content)
        except Exception as exc:
            logger.exception("Chat turn failed for session %s", session.id)
            return Response(
                {"detail": "AI service unavailable. Please try again.", "error": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        assistant_msg = ChatMessage.objects.create(
            session=updated_session, role="assistant", content=assistant_content
        )

        return Response(
            {
                "session": ChatSessionDetailSerializer(
                    updated_session, context={"request": request}
                ).data,
                "user_message": ChatMessageSerializer(user_msg).data,
                "assistant_message": ChatMessageSerializer(assistant_msg).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="messages")
    def messages(self, request, pk=None):
        """Return paginated message history for a session."""
        session = self.get_object()
        msgs = session.messages.order_by("created_at")
        page = self.paginate_queryset(msgs)
        if page is not None:
            return self.get_paginated_response(ChatMessageSerializer(page, many=True).data)
        return Response(ChatMessageSerializer(msgs, many=True).data)



class AnalysisViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["analysis_type", "dataset"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Analysis.objects.filter(
            dataset__user=self.request.user
        ).select_related("dataset", "chat_session").order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AnalysisDetailSerializer
        return AnalysisListSerializer


class DashboardViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["level", "dataset"]
    search_fields = ["title"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Dashboard.objects
            .filter(dataset__user=self.request.user)
            .select_related("dataset", "analysis")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return DashboardCreateSerializer
        if self.action == "retrieve":
            return DashboardDetailSerializer
        return DashboardListSerializer

    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Dashboards cannot be updated. Delete and re-generate."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        """Auto-generate a dashboard config from an existing Analysis."""
        analysis_id = request.data.get("analysis_id")
        if not analysis_id:
            return Response(
                {"detail": "analysis_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        analysis = get_object_or_404(
            Analysis, id=analysis_id, dataset__user=request.user
        )

        if hasattr(analysis, "dashboard"):
            return Response(
                DashboardDetailSerializer(
                    analysis.dashboard, context={"request": request}
                ).data,
                status=status.HTTP_200_OK,
            )

        try:
            dashboard = generate_dashboard_config(analysis)
        except Exception as exc:
            logger.exception("Dashboard generation failed for analysis %s", analysis_id)
            return Response(
                {"detail": "Dashboard generation failed.", "error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            DashboardDetailSerializer(dashboard, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="export",
            throttle_classes=[AnalysisRateThrottle])
    def export(self, request, pk=None):
        """Export a dashboard as PDF / Jupyter Notebook / Python script."""
        dashboard = self.get_object()

        serializer = TriggerExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fmt = serializer.validated_data["format"]

        try:
            report = export_dashboard_report(
                dashboard=dashboard,
                user=request.user,
                fmt=fmt,
            )
        except Exception as exc:
            logger.exception("Export failed for dashboard %s", dashboard.id)
            return Response(
                {"detail": "Export failed. Please try again.", "error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            ExportedReportSerializer(report, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="exports")
    def exports(self, request, pk=None):
        """List all exports for a dashboard."""
        dashboard = self.get_object()
        reports = dashboard.exports.filter(user=request.user).order_by("-created_at")
        page = self.paginate_queryset(reports)
        if page is not None:
            return self.get_paginated_response(
                ExportedReportSerializer(page, many=True, context={"request": request}).data
            )
        return Response(
            ExportedReportSerializer(reports, many=True, context={"request": request}).data
        )



class ExportedReportViewSet(viewsets.ReadOnlyModelViewSet):

    permission_classes = [IsAuthenticated]
    serializer_class = ExportedReportSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["format", "dashboard"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            ExportedReport.objects
            .filter(user=self.request.user)
            .select_related("dashboard")
            .order_by("-created_at")
        )
    
class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer