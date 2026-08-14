from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import (
    UserProfile,
    Dataset,
    ChatSession,
    ChatMessage,
    Analysis,
    Dashboard,
    ExportedReport,
)

admin.site.site_header = "AnalytixPro Admin"
admin.site.site_title = "AnalytixPro"
admin.site.index_title = "Welcome to AnalytixPro Dashboard"

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("role", "content", "created_at")
    can_delete = False


class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "date_joined")


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "updated_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "user",
        "file_type",
        "status",
        "rows",
        "columns",
        "file_size_display",
        "created_at",
    )
    list_filter = ("status", "file_type", "created_at")
    search_fields = ("name", "user__username")
    readonly_fields = ("file_size", "rows", "columns", "column_names", "created_at", "updated_at")
    ordering = ("-created_at",)

    @admin.display(description="File Size")
    def file_size_display(self, obj):
        if obj.file_size is None:
            return "—"
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 ** 2:
            return f"{obj.file_size / 1024:.1f} KB"
        return f"{obj.file_size / 1024 ** 2:.1f} MB"


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "dataset",
        "analysis_type",
        "goal",
        "dashboard_level",
        "is_complete",
        "created_at",
    )
    list_filter = ("analysis_type", "goal", "dashboard_level", "is_complete", "created_at")
    search_fields = ("user__username", "dataset__name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
    inlines = (ChatMessageInline,)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "role", "short_content", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("session__id", "content")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    @admin.display(description="Content")
    def short_content(self, obj):
        return obj.content[:80] + ("…" if len(obj.content) > 80 else "")


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "dataset",
        "analysis_type",
        "chat_session",
        "has_cleaned_file",
        "created_at",
    )
    list_filter = ("analysis_type", "created_at")
    search_fields = ("dataset__name",)
    readonly_fields = (
        "summary_statistics",
        "missing_values",
        "correlation_matrix",
        "categorical_insights",
        "top_kpis",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)

    @admin.display(description="Cleaned File", boolean=True)
    def has_cleaned_file(self, obj):
        return bool(obj.cleaned_file)


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "dataset", "analysis", "level", "created_at")
    list_filter = ("level", "created_at")
    search_fields = ("title", "dataset__name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(ExportedReport)
class ExportedReportAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "dashboard", "format", "created_at")
    list_filter = ("format", "created_at")
    search_fields = ("user__username", "dashboard__title")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)