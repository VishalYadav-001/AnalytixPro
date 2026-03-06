"""
serializers.py
Production-level DRF serializers for the AI Data Analysis Platform.

Conventions:
  - Read serializers  → flat, optimised for list/retrieve responses
  - Write serializers → validate input, enforce ownership, call services
  - Nested serializers used only for safe read operations
"""

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    UserProfile,
    Dataset,
    ChatSession,
    ChatMessage,
    Analysis,
    Dashboard,
    ExportedReport,
)

ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB



class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["bio", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class UserSerializer(serializers.ModelSerializer):
    """Returned after login / register and in /me endpoint."""
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "profile"]
        read_only_fields = ["id"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm password")
    tokens = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name",
                  "password", "password2", "tokens"]
        extra_kwargs = {
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password2"):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)
        return user

    def get_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True, write_only=True, validators=[validate_password]
    )

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value



class DatasetListSerializer(serializers.ModelSerializer):
    """Lightweight representation for list views."""

    class Meta:
        model = Dataset
        fields = [
            "id", "name", "file_type", "file_size",
            "rows", "columns", "status", "created_at",
        ]
        read_only_fields = fields


class DatasetUploadSerializer(serializers.ModelSerializer):
    """Handles file upload + basic validation."""

    class Meta:
        model = Dataset
        fields = ["id", "name", "file", "status", "file_type",
                  "file_size", "rows", "columns", "column_names", "created_at"]
        read_only_fields = [
            "id", "status", "file_type", "file_size",
            "rows", "columns", "column_names", "created_at",
        ]

    def validate_file(self, file):
        ext = file.name.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file type '.{ext}'. Allowed: {ALLOWED_EXTENSIONS}"
            )
        if file.size > MAX_FILE_SIZE_BYTES:
            raise serializers.ValidationError(
                f"File too large ({file.size // (1024*1024)} MB). Maximum is 100 MB."
            )
        return file

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class DatasetDetailSerializer(serializers.ModelSerializer):
    """Full representation for retrieve views."""
    owner = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Dataset
        fields = [
            "id", "owner", "name", "file", "file_type", "file_size",
            "rows", "columns", "column_names", "status",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "created_at"]
        read_only_fields = ["id", "created_at"]


class SendMessageSerializer(serializers.Serializer):
    """Payload for POST /chat-sessions/{id}/send_message/."""
    content = serializers.CharField(required=True, max_length=4096)


class ChatSessionListSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source="dataset.name", read_only=True, default=None)
    message_count = serializers.IntegerField(read_only=True)  # annotated in queryset

    class Meta:
        model = ChatSession
        fields = [
            "id", "dataset", "dataset_name", "analysis_type", "goal",
            "target_column", "dashboard_level", "download_code",
            "is_complete", "message_count", "created_at",
        ]
        read_only_fields = fields


class ChatSessionDetailSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    dataset_name = serializers.CharField(source="dataset.name", read_only=True, default=None)

    class Meta:
        model = ChatSession
        fields = [
            "id", "dataset", "dataset_name",
            "analysis_type", "goal", "target_column",
            "dashboard_level", "download_code",
            "is_complete", "messages", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_complete", "messages", "created_at", "updated_at"]

    def validate_dataset(self, dataset):
        request = self.context["request"]
        if dataset and dataset.user != request.user:
            raise serializers.ValidationError("Dataset not found.")
        return dataset


class ChatSessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ["id", "dataset"]

    def validate_dataset(self, dataset):
        request = self.context["request"]
        if dataset and dataset.user != request.user:
            raise serializers.ValidationError("Dataset not found.")
        return dataset

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class ChatSessionUpdateSerializer(serializers.ModelSerializer):
    """Allows updating context fields gathered during the chat flow."""

    class Meta:
        model = ChatSession
        fields = [
            "analysis_type", "goal", "target_column",
            "dashboard_level", "download_code", "is_complete",
        ]


class AnalysisListSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source="dataset.name", read_only=True)

    class Meta:
        model = Analysis
        fields = [
            "id", "dataset", "dataset_name", "analysis_type",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class AnalysisDetailSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source="dataset.name", read_only=True)
    cleaned_file_url = serializers.SerializerMethodField()

    class Meta:
        model = Analysis
        fields = [
            "id", "dataset", "dataset_name", "chat_session", "analysis_type",
            "summary_statistics", "missing_values", "correlation_matrix",
            "categorical_insights", "top_kpis",
            "cleaned_file", "cleaned_file_url",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_cleaned_file_url(self, obj):
        request = self.context.get("request")
        if obj.cleaned_file and request:
            return request.build_absolute_uri(obj.cleaned_file.url)
        return None


class TriggerAnalysisSerializer(serializers.Serializer):
    """Payload for POST /datasets/{id}/run_analysis/."""
    analysis_type = serializers.ChoiceField(choices=["eda", "ml"], default="eda")
    chat_session_id = serializers.IntegerField(required=False, allow_null=True)



class DashboardListSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source="dataset.name", read_only=True)

    class Meta:
        model = Dashboard
        fields = [
            "id", "dataset", "dataset_name", "title",
            "level", "created_at",
        ]
        read_only_fields = fields


class DashboardDetailSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source="dataset.name", read_only=True)
    analysis = AnalysisDetailSerializer(read_only=True)

    class Meta:
        model = Dashboard
        fields = [
            "id", "dataset", "dataset_name", "analysis",
            "title", "level", "layout_config",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class DashboardCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dashboard
        fields = ["id", "dataset", "analysis", "title", "level", "layout_config"]

    def validate(self, attrs):
        request = self.context["request"]
        dataset = attrs.get("dataset")
        analysis = attrs.get("analysis")

        if dataset and dataset.user != request.user:
            raise serializers.ValidationError({"dataset": "Dataset not found."})
        if analysis and analysis.dataset != dataset:
            raise serializers.ValidationError(
                {"analysis": "Analysis does not belong to this dataset."}
            )
        return attrs



class ExportedReportSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    dashboard_title = serializers.CharField(source="dashboard.title", read_only=True)

    class Meta:
        model = ExportedReport
        fields = [
            "id", "dashboard", "dashboard_title",
            "format", "file", "file_url", "created_at",
        ]
        read_only_fields = fields

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class TriggerExportSerializer(serializers.Serializer):
    """Payload for POST /dashboards/{id}/export/."""
    format = serializers.ChoiceField(choices=["pdf", "ipynb", "py"])