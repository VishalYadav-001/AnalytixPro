import io
import logging

import pandas as pd
from django.core.files.base import ContentFile

from ..models import Analysis, ChatSession, Dashboard, ExportedReport

logger = logging.getLogger(__name__)


def parse_uploaded_file(dataset) -> None:
    """
    Read the uploaded CSV/Excel file and populate metadata fields.
    Called synchronously during Dataset.create — must be fast.
    """
    file = dataset.file
    file.seek(0)

    ext = dataset.file.name.rsplit(".", 1)[-1].lower()
    try:
        if ext == "csv":
            df = pd.read_csv(file, nrows=0)          # headers only for metadata
            dataset.file_type = "csv"
        else:
            df = pd.read_excel(file, nrows=0)
            dataset.file_type = "excel"

        # Full row count (without loading everything into memory)
        file.seek(0)
        if ext == "csv":
            total = sum(1 for _ in file) - 1         # subtract header
        else:
            full_df = pd.read_excel(dataset.file)
            total = len(full_df)

        dataset.columns = len(df.columns)
        dataset.rows = total
        dataset.column_names = list(df.columns)
        dataset.file_size = dataset.file.size
        dataset.status = "uploaded"
        dataset.save(update_fields=[
            "file_type", "rows", "columns",
            "column_names", "file_size", "status",
        ])

    except Exception as exc:
        logger.error("parse_uploaded_file error: %s", exc)
        raise


def run_eda_analysis(dataset, analysis_type: str = "eda",
                     chat_session_id: int = None) -> Analysis:
    """
    Run pandas-based EDA on the dataset.
    Populates summary_statistics, missing_values, correlation_matrix,
    categorical_insights, top_kpis, and saves a cleaned CSV.

    For ML analysis_type, extend this function to invoke scikit-learn.
    """
    dataset.status = "processing"
    dataset.save(update_fields=["status"])

    try:
        # ── Load ────────────────────────────────────────────
        dataset.file.seek(0)
        ext = dataset.file.name.rsplit(".", 1)[-1].lower()
        df = pd.read_csv(dataset.file) if ext == "csv" else pd.read_excel(dataset.file)

        # ── Clean ───────────────────────────────────────────
        cleaned_df = _clean_dataframe(df)

        # ── EDA computations ────────────────────────────────
        summary_stats   = _compute_summary_statistics(cleaned_df)
        missing_values  = _compute_missing_values(df)           # pre-clean
        correlation     = _compute_correlation_matrix(cleaned_df)
        cat_insights    = _compute_categorical_insights(cleaned_df)
        top_kpis        = _compute_top_kpis(cleaned_df)

        # ── Persist cleaned file ─────────────────────────────
        cleaned_csv_buffer = io.BytesIO()
        cleaned_df.to_csv(cleaned_csv_buffer, index=False)
        cleaned_csv_buffer.seek(0)
        cleaned_filename = f"cleaned_{dataset.id}_{dataset.name}.csv"

        # ── Resolve chat session ─────────────────────────────
        chat_session = None
        if chat_session_id:
            try:
                chat_session = ChatSession.objects.get(
                    id=chat_session_id, user=dataset.user
                )
            except ChatSession.DoesNotExist:
                pass

        # ── Create Analysis record ───────────────────────────
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
            ContentFile(cleaned_csv_buffer.read()),
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
    """Drop duplicates, fill / drop nulls, encode categoricals."""
    df = df.drop_duplicates()

    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include="object").columns.tolist()

    df[num_cols] = df[num_cols].fillna(df[num_cols].median())
    df[cat_cols] = df[cat_cols].fillna(df[cat_cols].mode().iloc[0]
                                        if not df[cat_cols].mode().empty else "Unknown")
    return df


def _compute_summary_statistics(df: pd.DataFrame) -> dict:
    return df.describe(include="all").fillna("").to_dict()


def _compute_missing_values(df: pd.DataFrame) -> dict:
    missing = df.isnull().sum()
    pct = (missing / len(df) * 100).round(2)
    return {"count": missing.to_dict(), "percentage": pct.to_dict()}


def _compute_correlation_matrix(df: pd.DataFrame) -> dict:
    num_df = df.select_dtypes(include="number")
    if num_df.empty:
        return {}
    return num_df.corr().fillna(0).round(4).to_dict()


def _compute_categorical_insights(df: pd.DataFrame) -> dict:
    cat_cols = df.select_dtypes(include="object").columns
    return {
        col: df[col].value_counts().head(10).to_dict()
        for col in cat_cols
    }


def _compute_top_kpis(df: pd.DataFrame) -> dict:
    num_df = df.select_dtypes(include="number")
    if num_df.empty:
        return {}
    return {
        col: {
            "mean":   round(num_df[col].mean(), 4),
            "median": round(num_df[col].median(), 4),
            "std":    round(num_df[col].std(), 4),
            "min":    round(num_df[col].min(), 4),
            "max":    round(num_df[col].max(), 4),
        }
        for col in num_df.columns
    }



def generate_dashboard_config(analysis: Analysis) -> Dashboard:
    """
    Build a layout_config JSON based on EDA results and create a Dashboard.
    Extend this with more chart types / intelligence as needed.
    """
    session = analysis.chat_session
    level = (session.dashboard_level if session else None) or "basic"
    title = (
        f"{analysis.dataset.name} — {analysis.get_analysis_type_display()} Dashboard"
    )

    charts = []

    # Always include: summary stats card
    charts.append({"type": "summary_stats", "title": "Summary Statistics",
                    "data_key": "summary_statistics"})

    # Always include: missing values bar chart
    charts.append({"type": "bar", "title": "Missing Values",
                    "data_key": "missing_values"})

    if analysis.correlation_matrix:
        charts.append({"type": "heatmap", "title": "Correlation Heatmap",
                        "data_key": "correlation_matrix"})

    if analysis.categorical_insights:
        for col in list(analysis.categorical_insights.keys())[:3]:
            charts.append({"type": "pie", "title": f"{col} Distribution",
                            "data_key": f"categorical_insights.{col}"})

    if level == "advanced" and analysis.top_kpis:
        charts.append({"type": "kpi_cards", "title": "Top KPIs",
                        "data_key": "top_kpis"})
        for col in list(analysis.top_kpis.keys())[:5]:
            charts.append({"type": "histogram", "title": f"{col} Distribution",
                            "data_key": f"top_kpis.{col}"})

    layout_config = {"level": level, "charts": charts}

    return Dashboard.objects.create(
        dataset=analysis.dataset,
        analysis=analysis,
        title=title,
        level=level,
        layout_config=layout_config,
    )


def export_dashboard_report(dashboard: Dashboard, user, fmt: str) -> ExportedReport:
    """
    Generate a file export for the given dashboard.

    fmt options: 'pdf' | 'ipynb' | 'py'
    Extend each branch with real rendering logic.
    """
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
    """Stub — replace with WeasyPrint / ReportLab rendering."""
    content = f"PDF Report: {dashboard.title}\n\nLayout:\n{dashboard.layout_config}".encode()
    return content, f"dashboard_{dashboard.id}.pdf"


def _export_notebook(dashboard: Dashboard):
    """Generate a minimal Jupyter Notebook JSON."""
    import json
    analysis = dashboard.analysis
    cells = [
        _nb_markdown_cell(f"# {dashboard.title}"),
        _nb_code_cell("import pandas as pd\nimport matplotlib.pyplot as plt\nimport seaborn as sns"),
        _nb_code_cell(f"# Summary Statistics\nimport json\nstats = {json.dumps(analysis.summary_statistics, indent=2)}\nprint(stats)"),
        _nb_code_cell(f"# Correlation Matrix\ncorr = {json.dumps(analysis.correlation_matrix, indent=2)}\nsns.heatmap(pd.DataFrame(corr), annot=True)\nplt.show()"),
    ]
    notebook = {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "cells": cells,
    }
    content = json.dumps(notebook, indent=2).encode()
    return content, f"dashboard_{dashboard.id}.ipynb"


def _export_python_script(dashboard: Dashboard):
    """Generate a standalone Python analysis script."""
    import json
    analysis = dashboard.analysis
    script = f"""#!/usr/bin/env python3
\"\"\"
Auto-generated analysis script for: {dashboard.title}
Dataset: {dashboard.dataset.name}
\"\"\"

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ── Load Dataset ──────────────────────────────────────────────
df = pd.read_csv("your_dataset.csv")  # replace with your file path

# ── Summary Statistics ────────────────────────────────────────
print(df.describe(include="all"))

# ── Missing Values ────────────────────────────────────────────
print(df.isnull().sum())

# ── Correlation Heatmap ───────────────────────────────────────
plt.figure(figsize=(12, 8))
sns.heatmap(df.select_dtypes(include="number").corr(), annot=True, fmt=".2f")
plt.title("{dashboard.title} — Correlation Heatmap")
plt.tight_layout()
plt.savefig("correlation_heatmap.png")
plt.show()

# ── Categorical Distributions ─────────────────────────────────
for col in df.select_dtypes(include="object").columns[:3]:
    df[col].value_counts().head(10).plot(kind="bar", title=col)
    plt.tight_layout()
    plt.savefig(f"{{col}}_distribution.png")
    plt.show()

print("Analysis complete.")
"""
    return script.encode(), f"dashboard_{dashboard.id}.py"


def _nb_code_cell(source: str) -> dict:
    return {"cell_type": "code", "source": source,
            "metadata": {}, "outputs": [], "execution_count": None}


def _nb_markdown_cell(source: str) -> dict:
    return {"cell_type": "markdown", "source": source, "metadata": {}}


# Chatbot question flow (mirrors the 5 steps in the project doc)
_CHAT_FLOW = [
    ("analysis_type",   "What type of analysis are you looking for? (sales / hr / financial / custom)"),
    ("goal",            "What is the goal of your data? (find_trends / predict_outcomes / custom)"),
    ("target_column",   "What's your target column, if any? (e.g. Revenue — or type 'none')"),
    ("dashboard_level", "How would you like the dashboard? (basic / advanced)"),
    ("download_code",   "Would you like to download the generated Python code? (yes / no)"),
]

_FIELD_PARSERS = {
    "analysis_type":   lambda v: v.lower() if v.lower() in ("sales","hr","financial","custom") else None,
    "goal":            lambda v: v.lower() if v.lower() in ("find_trends","predict_outcomes","custom") else None,
    "target_column":   lambda v: None if v.lower() == "none" else v.strip(),
    "dashboard_level": lambda v: v.lower() if v.lower() in ("basic","advanced") else None,
    "download_code":   lambda v: v.lower().startswith("y"),
}


def handle_chat_turn(session: ChatSession, user_content: str):
    """
    Determine which question has just been answered, parse the value,
    update the session, and return the next question (or completion message).

    Returns: (assistant_reply: str, updated_session: ChatSession)
    """
    # Find the first unanswered field
    current_field = None
    for field, _ in _CHAT_FLOW:
        if getattr(session, field) is None or (
            field == "download_code" and not session.is_complete
            and session.dashboard_level is not None
            and session.download_code is False
            and session.target_column is not None
        ):
            # Crude check — refine with a dedicated state tracker if needed
            if getattr(session, field) is None:
                current_field = field
                break

    if current_field:
        parser = _FIELD_PARSERS[current_field]
        parsed = parser(user_content)
        if parsed is not None or current_field == "target_column":
            setattr(session, current_field, parsed)
            session.save(update_fields=[current_field])

    # Find next unanswered question
    next_question = None
    for field, question in _CHAT_FLOW:
        val = getattr(session, field)
        if val is None:
            next_question = question
            break

    if next_question:
        reply = next_question
    else:
        # All questions answered — mark complete
        session.is_complete = True
        session.save(update_fields=["is_complete"])
        reply = (
            "Great! I have everything I need. "
            "Your dataset is ready for analysis. "
            "Click 'Run Analysis' to generate your dashboard."
        )

    return reply, session