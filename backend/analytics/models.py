from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


class Dataset(models.Model):
    FILE_TYPE_CHOICES = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
    ]

    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='datasets')
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='datasets/')
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)   # bytes
    rows = models.IntegerField(null=True, blank=True)
    columns = models.IntegerField(null=True, blank=True)
    column_names = models.JSONField(null=True, blank=True)      # list of column names
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class ChatSession(models.Model):
    ANALYSIS_TYPE_CHOICES = [
        ('sales', 'Sales'),
        ('hr', 'HR'),
        ('financial', 'Financial'),
        ('custom', 'Custom'),
    ]

    GOAL_CHOICES = [
        ('find_trends', 'Find Trends'),
        ('predict_outcomes', 'Predict Outcomes'),
        ('custom', 'Custom'),
    ]

    DASHBOARD_LEVEL_CHOICES = [
        ('basic', 'Basic'),
        ('advanced', 'Advanced'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    dataset = models.ForeignKey(
        Dataset, on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_sessions'
    )

    # Answers gathered by the chatbot (Step 1–5 from the doc)
    analysis_type = models.CharField(
        max_length=20, choices=ANALYSIS_TYPE_CHOICES, null=True, blank=True
    )
    goal = models.CharField(max_length=50, choices=GOAL_CHOICES, null=True, blank=True)
    target_column = models.CharField(max_length=255, null=True, blank=True)
    dashboard_level = models.CharField(
        max_length=10, choices=DASHBOARD_LEVEL_CHOICES, null=True, blank=True
    )
    download_code = models.BooleanField(default=False)

    is_complete = models.BooleanField(default=False)  # True when all 5 questions answered
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session {self.id} — {self.user.username}"


# ──────────────────────────────────────────────
# Chat Message  (individual turns in a session)
# ──────────────────────────────────────────────
class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role}] {self.content[:60]}"


# ──────────────────────────────────────────────
# Analysis  (EDA / ML results for a dataset)
# ──────────────────────────────────────────────
class Analysis(models.Model):
    ANALYSIS_TYPES = [
        ('eda', 'Exploratory Data Analysis'),
        ('ml', 'Machine Learning'),
    ]

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='analyses')
    chat_session = models.OneToOneField(
        ChatSession, on_delete=models.SET_NULL, null=True, blank=True, related_name='analysis'
    )
    analysis_type = models.CharField(max_length=50, choices=ANALYSIS_TYPES)

    # EDA outputs
    summary_statistics = models.JSONField(null=True, blank=True)
    missing_values = models.JSONField(null=True, blank=True)
    correlation_matrix = models.JSONField(null=True, blank=True)
    categorical_insights = models.JSONField(null=True, blank=True)
    top_kpis = models.JSONField(null=True, blank=True)           # added per doc

    # Cleaned dataset
    cleaned_file = models.FileField(upload_to='cleaned_datasets/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.analysis_type} — {self.dataset.name}"


# ──────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────
class Dashboard(models.Model):
    LEVEL_CHOICES = [
        ('basic', 'Basic'),
        ('advanced', 'Advanced'),
    ]

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='dashboards')
    analysis = models.OneToOneField(Analysis, on_delete=models.CASCADE, related_name='dashboard')
    title = models.CharField(max_length=255)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='basic')
    layout_config = models.JSONField()          # chart types, positions, axis config, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# ──────────────────────────────────────────────
# Exported Report / Code
# ──────────────────────────────────────────────
class ExportedReport(models.Model):
    FORMAT_CHOICES = [
        ('pdf', 'PDF Report'),
        ('ipynb', 'Jupyter Notebook'),
        ('py', 'Python Script'),
    ]

    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='exports')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exports')
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    file = models.FileField(upload_to='exports/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.format.upper()} export — {self.dashboard.title}"