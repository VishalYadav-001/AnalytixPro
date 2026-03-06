from django.contrib import admin
from .models import Dataset, Analysis, Dashboard
from django.contrib import admin

admin.site.site_header = "AnalytixPro Admin"
admin.site.site_title = "AnalytixPro"
admin.site.index_title = "Welcome to AnalytixPro Dashboard"

@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'user',
        'status',
        'rows',
        'columns',
        'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'user__username')
    readonly_fields = ('file_size', 'rows', 'columns', 'created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'dataset',
        'analysis_type',
        'created_at',
    )
    list_filter = ('analysis_type', 'created_at')
    search_fields = ('dataset__name',)
    ordering = ('-created_at',)


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'dataset',
        'created_at',
    )
    search_fields = ('title', 'dataset__name')
    ordering = ('-created_at',)