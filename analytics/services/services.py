from datetime import datetime
import io
import logging

import pandas as pd
from django.core.files.base import ContentFile

from ..models import Analysis, ChatSession, Dashboard, ExportedReport

logger = logging.getLogger(__name__)

import numpy as np

def _make_json_serializable(data):
    if isinstance(data, dict):
        return {str(k): _make_json_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_make_json_serializable(i) for i in data]
    
    elif isinstance(data, (datetime, pd.Timestamp)):
        return data.isoformat()
    
    elif isinstance(data, (np.integer, np.int64)):
        return int(data)
    
    elif isinstance(data, (np.floating, np.float64)):
        return float(data) if not np.isnan(data) else 0
    
    elif pd.isna(data):
        return None
    
    return data

def parse_uploaded_file(dataset) -> None:
    """
    Read the uploaded CSV/Excel file and populate metadata fields.
    Called synchronously during Dataset.create — must be fast.
    """
    file = dataset.file
    file.seek(0)
    raw = file.read()         
    ext = dataset.file.name.rsplit(".", 1)[-1].lower()

    try:
        if ext == "csv":
            df_head = pd.read_csv(io.BytesIO(raw), nrows=0)
            text = raw.decode("utf-8", errors="replace")
            total = max(0, text.count("\n") - 1)
            dataset.file_type = "csv"
        else:
            df_head = pd.read_excel(io.BytesIO(raw), nrows=0)
            full_df = pd.read_excel(io.BytesIO(raw))
            total = len(full_df)
            dataset.file_type = "excel"

        dataset.columns     = len(df_head.columns)
        dataset.rows        = total
        dataset.column_names = list(df_head.columns)
        dataset.file_size   = len(raw)
        dataset.status      = "uploaded"
        dataset.save(update_fields=[
            "file_type", "rows", "columns",
            "column_names", "file_size", "status",
        ])

    except Exception as exc:
        logger.error("parse_uploaded_file error: %s", exc)
        raise


def run_eda_analysis(dataset, analysis_type: str = "eda",
                     chat_session_id: int = None) -> Analysis:
 
    dataset.status = "processing"
    dataset.save(update_fields=["status"])

    try:
        dataset.file.seek(0)
        raw = dataset.file.read()
        ext = dataset.file.name.rsplit(".", 1)[-1].lower()
        df = pd.read_csv(io.BytesIO(raw)) if ext == "csv" else pd.read_excel(io.BytesIO(raw))

        cleaned_df = _clean_dataframe(df)

        summary_stats  = _compute_summary_statistics(cleaned_df)
        missing_values = _compute_missing_values(df)        # pre-clean
        correlation    = _compute_correlation_matrix(cleaned_df)
        cat_insights   = _compute_categorical_insights(cleaned_df)
        top_kpis       = _compute_top_kpis(cleaned_df)

        cleaned_buf = io.BytesIO()
        cleaned_df.to_csv(cleaned_buf, index=False)
        cleaned_buf.seek(0)
        cleaned_filename = f"cleaned_{dataset.id}_{dataset.name}.csv"

        chat_session = None
        if chat_session_id:
            try:
                chat_session = ChatSession.objects.get(
                    id=chat_session_id, user=dataset.user
                )
            except ChatSession.DoesNotExist:
                pass

        analysis = Analysis.objects.create(
            dataset=dataset,
            chat_session=chat_session,
            analysis_type=analysis_type,
            summary_statistics=summary_stats,
            missing_values=missing_values,
            correlation_matrix=correlation,
            categorical_insights=cat_insights,
            top_kpis=top_kpis,
        )
        analysis.cleaned_file.save(
            cleaned_filename,
            ContentFile(cleaned_buf.read()),
            save=True,
        )

        dataset.status = "completed"
        dataset.save(update_fields=["status"])
        return analysis

    except Exception as exc:
        dataset.status = "failed"
        dataset.save(update_fields=["status"])
        logger.exception("run_eda_analysis failed for dataset %s", dataset.id)
        raise


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates()
    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include="object").columns.tolist()
    
    for col in num_cols:
        if df[col].isnull().all():
            df[col] = df[col].fillna(0) 
        else:
            df[col] = df[col].fillna(df[col].median())
            
    if cat_cols:
        mode = df[cat_cols].mode()
        fill = mode.iloc[0] if not mode.empty else "Unknown"
        df[cat_cols] = df[cat_cols].fillna(fill)
    return df


def _compute_summary_statistics(df: pd.DataFrame) -> dict:
    stats = df.describe(include="all").fillna("")
    return _make_json_serializable(stats.to_dict())

def _compute_missing_values(df: pd.DataFrame) -> dict:
    missing = df.isnull().sum()
    pct = (missing / len(df) * 100).round(2)
    data = {
        "count": missing.to_dict(),
        "percentage": pct.to_dict()
    }
    return _make_json_serializable(data)

def _compute_correlation_matrix(df: pd.DataFrame) -> dict:
    num_df = df.select_dtypes(include="number")
    if num_df.empty:
        return {}
    corr = num_df.corr().fillna(0).round(4)
    return _make_json_serializable(corr.to_dict())

def _compute_categorical_insights(df: pd.DataFrame) -> dict:
    cat_cols = df.select_dtypes(include="object").columns
    insights = {}
    for col in cat_cols:
        counts = df[col].value_counts().head(10).to_dict()
        insights[col] = counts
    return _make_json_serializable(insights)

def _compute_top_kpis(df: pd.DataFrame) -> dict:
    num_df = df.select_dtypes(include="number")
    if num_df.empty:
        return {}
    
    kpis = {}
    for col in num_df.columns:
        kpis[col] = {
            "mean":   float(num_df[col].mean()) if pd.notnull(num_df[col].mean()) else 0,
            "median": float(num_df[col].median()) if pd.notnull(num_df[col].median()) else 0,
            "std":    float(num_df[col].std()) if pd.notnull(num_df[col].std()) else 0,
            "min":    num_df[col].min(),
            "max":    num_df[col].max(),
        }
    return _make_json_serializable(kpis)

def generate_dashboard_config(analysis: Analysis) -> Dashboard:
    session = analysis.chat_session
    level = (session.dashboard_level if session else None) or "basic"
    title = f"{analysis.dataset.name} — {analysis.get_analysis_type_display()} Dashboard"

    charts = [
        {"type": "summary_stats", "title": "Summary Statistics",  "data_key": "summary_statistics"},
        {"type": "bar",           "title": "Missing Values",       "data_key": "missing_values"},
    ]

    if analysis.correlation_matrix:
        charts.append({"type": "heatmap", "title": "Correlation Heatmap",
                        "data_key": "correlation_matrix"})

    if analysis.categorical_insights:
        for col in list(analysis.categorical_insights.keys())[:3]:
            charts.append({"type": "pie", "title": f"{col} Distribution",
                            "data_key": f"categorical_insights.{col}"})

    if level == "advanced" and analysis.top_kpis:
        charts.append({"type": "kpi_cards", "title": "Top KPIs", "data_key": "top_kpis"})
        for col in list(analysis.top_kpis.keys())[:5]:
            charts.append({"type": "histogram", "title": f"{col} Distribution",
                            "data_key": f"top_kpis.{col}"})

    return Dashboard.objects.create(
        dataset=analysis.dataset,
        analysis=analysis,
        title=title,
        level=level,
        layout_config={"level": level, "charts": charts},
    )


def export_dashboard_report(dashboard: Dashboard, user, fmt: str) -> ExportedReport:
    if fmt == "pdf":
        file_content, filename = _export_pdf(dashboard)
    elif fmt == "ipynb":
        file_content, filename = _export_notebook(dashboard)
    else:
        file_content, filename = _export_python_script(dashboard)

    report = ExportedReport(dashboard=dashboard, user=user, format=fmt)
    report.file.save(filename, ContentFile(file_content), save=True)
    return report


def _export_pdf(dashboard: Dashboard):
    content = f"PDF Report: {dashboard.title}\n\nLayout:\n{dashboard.layout_config}".encode()
    return content, f"dashboard_{dashboard.id}.pdf"


def _export_notebook(dashboard: Dashboard):
    import json
    analysis = dashboard.analysis
    cells = [
        _nb_markdown_cell(f"# {dashboard.title}"),
        _nb_code_cell("import pandas as pd\nimport matplotlib.pyplot as plt\nimport seaborn as sns"),
        _nb_code_cell(f"stats = {json.dumps(analysis.summary_statistics, indent=2)}\nprint(stats)"),
        _nb_code_cell(f"corr = {json.dumps(analysis.correlation_matrix, indent=2)}\nsns.heatmap(pd.DataFrame(corr), annot=True)\nplt.show()"),
    ]
    notebook = {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "cells": cells,
    }
    return json.dumps(notebook, indent=2).encode(), f"dashboard_{dashboard.id}.ipynb"


def _export_python_script(dashboard: Dashboard):
    script = f'''#!/usr/bin/env python3
"""Auto-generated analysis script for: {dashboard.title}"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("your_dataset.csv")
print(df.describe(include="all"))
print(df.isnull().sum())

plt.figure(figsize=(12, 8))
sns.heatmap(df.select_dtypes(include="number").corr(), annot=True, fmt=".2f")
plt.title("{dashboard.title} — Correlation Heatmap")
plt.tight_layout()
plt.savefig("correlation_heatmap.png")
plt.show()

for col in df.select_dtypes(include="object").columns[:3]:
    df[col].value_counts().head(10).plot(kind="bar", title=col)
    plt.tight_layout()
    plt.savefig(f"{{col}}_distribution.png")
    plt.show()
'''
    return script.encode(), f"dashboard_{dashboard.id}.py"


def _nb_code_cell(source):
    return {"cell_type": "code", "source": source, "metadata": {}, "outputs": [], "execution_count": None}

def _nb_markdown_cell(source):
    return {"cell_type": "markdown", "source": source, "metadata": {}}


TARGET_COLUMN_NONE_SENTINEL = "__none__"  # Stored in DB when user says "none"

_CHAT_FLOW = [
    ("analysis_type",   "What type of analysis are you looking for?\nOptions: **sales** / **hr** / **financial** / **custom**"),
    ("goal",            "What is the goal of your data?\nOptions: **find_trends** / **predict_outcomes** / **custom**"),
    ("target_column",   "What's your target column, if any? (e.g. Revenue — or type 'none')"),
    ("dashboard_level", "How would you like the dashboard?\nOptions: **basic** / **advanced**"),
    ("download_code",   "Would you like to download the generated Python code? (yes / no)"),
]

_FIELD_PARSERS = {
    "analysis_type": lambda v: (
        normalized := v.strip().lower().replace(" ", "_"),
        normalized if normalized in ("sales", "hr", "financial", "custom") else None
    )[-1],
    
    "goal": lambda v: (
        normalized := v.strip().lower().replace(" ", "_"),
        normalized if normalized in ("find_trends", "predict_outcomes", "custom") else None
    )[-1],
    
    "target_column":   lambda v: TARGET_COLUMN_NONE_SENTINEL if v.strip().lower() == "none" else v.strip(),
    "dashboard_level": lambda v: (
        normalized := v.strip().lower().replace(" ", "_"),
        normalized if normalized in ("basic", "advanced") else None
    )[-1],
    "download_code":   lambda v: v.strip().lower().startswith("y"),
}


def _is_field_answered(session, field):
    """
    Determines if a field has been explicitly answered — no extra DB columns needed.
    """
    if field == "download_code":

        prior_fields = ["analysis_type", "goal", "target_column", "dashboard_level"]
        return all(_is_field_answered(session, f) for f in prior_fields) and (
            session.is_complete or getattr(session, "_download_code_set", False)
        )

    if field == "target_column":
        val = session.target_column
        return val is not None and val != ""

    val = getattr(session, field)
    return val is not None and val != ""


def handle_chat_turn(session: ChatSession, user_content: str):
    """
    Processes one user turn. Finds the current unanswered field,
    validates input, saves it, then returns the next question or completion message.
    """
    current_field = None
    for field, _ in _CHAT_FLOW:
        if not _is_field_answered(session, field):
            current_field = field
            break

    if current_field:
        parser = _FIELD_PARSERS[current_field]
        parsed = parser(user_content)

        if current_field == "download_code":
            session.download_code = parsed
            session._download_code_set = True  
            session.save(update_fields=["download_code"])

        elif parsed is not None:
            setattr(session, current_field, parsed)
            session.save(update_fields=[current_field])

        else:
            for field, question in _CHAT_FLOW:
                if field == current_field:
                    return f"⚠️ That doesn't look right. Please choose one of the options:\n\n{question}", session

    next_question = None
    for field, question in _CHAT_FLOW:
        if not _is_field_answered(session, field):
            next_question = question
            break

    if next_question:
        return next_question, session

    session.is_complete = True
    session.save(update_fields=["is_complete"])

    display_target = (
        "None" 
        if session.target_column == TARGET_COLUMN_NONE_SENTINEL 
        else (session.target_column or "None")
    )

    reply = (
        "✅ Great! I have everything I need.\n\n"
        "Here's a summary of your setup:\n"
        f"• Analysis type: {session.analysis_type}\n"
        f"• Goal: {session.goal}\n"
        f"• Target column: {display_target}\n"
        f"• Dashboard level: {session.dashboard_level}\n"
        f"• Download code: {'Yes' if session.download_code else 'No'}\n\n"
        "Head to **Datasets** and click **Analyse** to generate your dashboard!"
    )
    return reply, session