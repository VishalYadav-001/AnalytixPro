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


# ── Domain-specific dashboard configurations ──────────────────────
_DOMAIN_CONFIG = {
    "sales": {
        "label": "Sales Dashboard",
        "color": "#3b82f6",
        "sections": {
            "kpi":         "Sales KPIs",
            "overview":    "Revenue Overview",
            "distribution": "Sales by Channel",
            "correlation": "Revenue Correlations",
            "quality":     "Data Completeness",
            "categorical": "Category Breakdowns",
            "numeric":     "Sales Metrics",
        }
    },
    "hr": {
        "label": "HR Analytics Dashboard",
        "color": "#8b5cf6",
        "sections": {
            "kpi":         "Workforce KPIs",
            "overview":    "Headcount Overview",
            "distribution": "Department Distribution",
            "correlation": "Performance Correlations",
            "quality":     "Data Completeness",
            "categorical": "Team Breakdowns",
            "numeric":     "HR Metrics",
        }
    },
    "financial": {
        "label": "Financial Dashboard",
        "color": "#10b981",
        "sections": {
            "kpi":         "Financial KPIs",
            "overview":    "Revenue & Expenses",
            "distribution": "Budget Allocation",
            "correlation": "Financial Correlations",
            "quality":     "Data Completeness",
            "categorical": "Category Analysis",
            "numeric":     "Financial Metrics",
        }
    },
    "custom": {
        "label": "Analytics Dashboard",
        "color": "#f59e0b",
        "sections": {
            "kpi":         "Key Metrics",
            "overview":    "Distribution Overview",
            "distribution": "Top Categories",
            "correlation": "Correlation Heatmap",
            "quality":     "Data Quality",
            "categorical": "Categorical Distributions",
            "numeric":     "Numeric Analysis",
        }
    }
}


def generate_dashboard_config(analysis: Analysis) -> Dashboard:
    session = analysis.chat_session
    level = (session.dashboard_level if session else None) or "basic"
    analysis_type = (session.analysis_type if session else None) or "custom"
    target_column = (session.target_column if session else None) or ""

    domain = _DOMAIN_CONFIG.get(analysis_type, _DOMAIN_CONFIG["custom"])
    title = f"{analysis.dataset.name} — {domain['label']}"

    charts = [
        {"type": "kpi_cards",    "title": domain["sections"]["kpi"],       "data_key": "top_kpis",      "section": "kpi"},
        {"type": "bar",          "title": domain["sections"]["overview"],   "data_key": "top_kpis",      "section": "overview"},
    ]

    if analysis.categorical_insights:
        for col in list(analysis.categorical_insights.keys())[:3]:
            charts.append({
                "type": "pie",
                "title": f"{col} Distribution",
                "data_key": f"categorical_insights.{col}",
                "section": "categorical"
            })

    if analysis.correlation_matrix:
        charts.append({
            "type": "heatmap",
            "title": domain["sections"]["correlation"],
            "data_key": "correlation_matrix",
            "section": "correlation"
        })

    charts.append({
        "type": "missing_bar",
        "title": "Missing Values",
        "data_key": "missing_values",
        "section": "quality"
    })

    if level == "advanced" and analysis.top_kpis:
        for col in list(analysis.top_kpis.keys())[:6]:
            charts.append({
                "type": "histogram",
                "title": f"{col} — Distribution",
                "data_key": f"top_kpis.{col}",
                "section": "numeric"
            })

    layout_config = {
        "level": level,
        "analysis_type": analysis_type,
        "domain_label": domain["label"],
        "domain_color": domain["color"],
        "target_column": target_column,
        "sections": domain["sections"],
        "charts": charts,
        "command_state": {
            "hidden_sections": [],
            "highlighted_columns": [target_column] if target_column and target_column != "__none__" else [],
            "focus_type": None,
        }
    }

    return Dashboard.objects.create(
        dataset=analysis.dataset,
        analysis=analysis,
        title=title,
        level=level,
        layout_config=layout_config,
    )


def process_dashboard_command(dashboard: Dashboard, command: str):
    """
    Process a natural language command to update the dashboard layout.
    Returns (response_message, updated_layout_config).
    """
    cmd = command.lower().strip()
    config = {**dashboard.layout_config}

    if "command_state" not in config:
        config["command_state"] = {
            "hidden_sections": [],
            "highlighted_columns": [],
            "focus_type": None,
        }

    state = config["command_state"]

    # Hide / Remove
    if any(w in cmd for w in ["hide", "remove"]):
        if any(w in cmd for w in ["correlation", "heatmap"]):
            if "correlation" not in state["hidden_sections"]:
                state["hidden_sections"].append("correlation")
            return " Correlation heatmap hidden. Type **show correlation** to restore it.", config

        if any(w in cmd for w in ["missing", "quality", "completeness"]):
            if "quality" not in state["hidden_sections"]:
                state["hidden_sections"].append("quality")
            return " Data quality section hidden.", config

        if any(w in cmd for w in ["kpi", "metric card", "key metric", "cards"]):
            if "kpi" not in state["hidden_sections"]:
                state["hidden_sections"].append("kpi")
            return " KPI cards hidden.", config

        if any(w in cmd for w in ["distribution", "categorical", "category", "pie"]):
            if "categorical" not in state["hidden_sections"]:
                state["hidden_sections"].append("categorical")
            return " Categorical distributions hidden.", config

        if any(w in cmd for w in ["numeric", "bar chart", "column analysis", "overview"]):
            if "numeric" not in state["hidden_sections"]:
                state["hidden_sections"].append("numeric")
            return " Numeric analysis section hidden.", config

        return "I can hide: **correlation**, **quality**, **kpi cards**, **distributions**, or **numeric analysis**. Which section?", config

    # Show / Add
    if any(w in cmd for w in ["show", "add", "display", "reveal"]):
        if any(w in cmd for w in ["all", "everything", "full", "reset"]):
            state["hidden_sections"] = []
            state["highlighted_columns"] = []
            state["focus_type"] = None
            return " Dashboard restored to full view — all sections visible.", config

        if any(w in cmd for w in ["correlation", "heatmap"]):
            if "correlation" in state["hidden_sections"]:
                state["hidden_sections"].remove("correlation")
            return " Correlation heatmap is now visible.", config

        if any(w in cmd for w in ["missing", "quality"]):
            if "quality" in state["hidden_sections"]:
                state["hidden_sections"].remove("quality")
            return " Data quality section is now visible.", config

        if any(w in cmd for w in ["kpi", "metric", "cards"]):
            if "kpi" in state["hidden_sections"]:
                state["hidden_sections"].remove("kpi")
            return " KPI cards are now visible.", config

        if any(w in cmd for w in ["distribution", "categorical"]):
            if "categorical" in state["hidden_sections"]:
                state["hidden_sections"].remove("categorical")
            return " Categorical distributions are now visible.", config

        return "All sections are already visible. Try **hide correlation** or **focus on Revenue** to customize.", config

    # Focus / Highlight
    if any(w in cmd for w in ["focus", "highlight", "zoom", "spotlight"]):
        skip = {"focus", "on", "highlight", "zoom", "into", "the", "a", "an", "spotlight"}
        words = [w for w in cmd.split() if w not in skip and len(w) > 1]
        if words:
            state["highlighted_columns"] = [w.title() for w in words[:3]]
            cols = ", ".join(state["highlighted_columns"])
            return f" Highlighting: **{cols}**. These metrics are now featured prominently.", config
        return "Please specify a column. Example: **focus on Revenue** or **highlight Sales**", config

    # Simple / Minimal view
    if any(w in cmd for w in ["simple", "minimal", "clean", "basic"]):
        state["hidden_sections"] = ["correlation", "categorical", "quality"]
        state["focus_type"] = "simple"
        return " Switched to simplified view — KPIs and key charts only.", config

    # Full / Advanced view
    if any(w in cmd for w in ["full", "complete", "advanced", "detailed", "expand"]):
        state["hidden_sections"] = []
        state["focus_type"] = "advanced"
        return " Switched to full view — all charts and analysis sections visible.", config

    # Reset
    if any(w in cmd for w in ["reset", "default", "original", "undo", "restore", "clear"]):
        state["hidden_sections"] = []
        state["highlighted_columns"] = []
        state["focus_type"] = None
        return " Dashboard reset to default view.", config

    # Help
    if any(w in cmd for w in ["help", "what", "commands", "how", "options"]):
        return (
            "Here's what I can do:\n\n"
            "• **hide [section]** — Hide correlation, quality, kpi cards, distributions\n"
            "• **show [section]** — Show a hidden section\n"
            "• **show all** — Restore full dashboard\n"
            "• **focus on [column]** — Highlight specific metrics\n"
            "• **simple view** — Show only key metrics\n"
            "• **full view** — Show all analytics\n"
            "• **reset** — Restore defaults"
        ), config

    return (
        "I didn't quite understand that. Try:\n"
        "• **hide correlation** or **hide quality**\n"
        "• **show all** or **reset**\n"
        "• **focus on Revenue**\n"
        "• **simple view** or **full view**\n"
        "• **help** for all commands"
    ), config


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


TARGET_COLUMN_NONE_SENTINEL = "__none__"


def _parse_analysis_type(raw: str):
    v = raw.strip().lower().replace(" ", "_").replace("-", "_")
    mapping = {
        "sales": "sales", "sale": "sales", "revenue": "sales",
        "ecommerce": "sales", "e_commerce": "sales", "shop": "sales",
        "retail": "sales", "product": "sales", "orders": "sales",
        "hr": "hr", "human_resources": "hr", "people": "hr",
        "workforce": "hr", "employee": "hr", "employees": "hr",
        "staffing": "hr", "personnel": "hr",
        "financial": "financial", "finance": "financial",
        "accounting": "financial", "budget": "financial",
        "money": "financial", "fiscal": "financial", "economics": "financial",
        "custom": "custom", "marketing": "custom", "market": "custom",
        "operations": "custom", "ops": "custom",
        "other": "custom", "general": "custom", "any": "custom",
        "logistics": "custom", "supply": "custom", "inventory": "custom",
    }
    return mapping.get(v)


def _parse_goal(raw: str):
    v = raw.strip().lower().replace(" ", "_").replace("-", "_")
    mapping = {
        "find_trends": "find_trends", "trends": "find_trends",
        "trend": "find_trends", "patterns": "find_trends",
        "spot_trends": "find_trends", "time_trends": "find_trends",
        "predict_outcomes": "predict_outcomes", "predict": "predict_outcomes",
        "prediction": "predict_outcomes", "forecast": "predict_outcomes",
        "forecasting": "predict_outcomes", "drivers": "predict_outcomes",
        "correlations": "predict_outcomes", "relationships": "predict_outcomes",
        "custom": "custom", "explore": "custom", "all": "custom",
        "everything": "custom", "complete": "custom", "overview": "custom",
        "general": "custom", "understand": "custom", "analyze": "custom",
        "analyse": "custom",
    }
    return mapping.get(v)


def _parse_dashboard_level(raw: str):
    v = raw.strip().lower().replace(" ", "_")
    if v in ("basic", "simple", "clean", "minimal", "overview", "quick", "standard"):
        return "basic"
    if v in ("advanced", "detailed", "full", "complete", "all", "deep", "comprehensive", "pro"):
        return "advanced"
    return None


_CHAT_FLOW = [
    ("analysis_type",
     "Welcome! I'm your Analytics Assistant — let's build your professional dashboard.\n\n"
     "What type of data have you uploaded?\n\n"
     "• **sales** — Sales, revenue, orders, products, e-commerce\n"
     "• **hr** — People, workforce, departments, performance\n"
     "• **financial** — Finance, budgets, P&L, accounting\n"
     "• **custom** — Marketing, operations, or any other domain"),

    ("goal",
     "Great choice! What's your primary goal with this analysis?\n\n"
     "• **find_trends** — Spot patterns and changes over time\n"
     "• **predict_outcomes** — Understand key drivers and correlations\n"
     "• **custom** — Explore all metrics for a complete overview"),

    ("target_column",
     "Which column is your **star metric** — the one KPI you care most about?\n\n"
     "  Tip: Click any column name from the panel on the right, or type it here.\n"
     "Type **none** if you want an equal focus on all metrics."),

    ("dashboard_level",
     "How comprehensive should your dashboard be?\n\n"
     "• **basic** — Clean & focused: KPI cards, key charts, quick insights\n"
     "• **advanced** — Full analytical suite: all metrics, correlations, deep distributions"),

    ("download_code",
     "Last step! Would you like to download the Python analysis code?\n\n"
     "• **yes** — Get a Jupyter Notebook + Python script to run locally\n"
     "• **no** — Dashboard only is perfect"),
]

_FIELD_PARSERS = {
    "analysis_type":  _parse_analysis_type,
    "goal":           _parse_goal,
    "target_column":  lambda v: TARGET_COLUMN_NONE_SENTINEL if v.strip().lower() in ("none", "no", "n/a", "-", "skip", "all") else v.strip(),
    "dashboard_level": _parse_dashboard_level,
    "download_code":  lambda v: v.strip().lower()[:1] in ("y", "1", "t") if v.strip() else False,
}


def _is_field_answered(session, field):
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
                    return f" I didn't recognise that answer. Please try again:\n\n{question}", session

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
        "All metrics (equal focus)"
        if session.target_column == TARGET_COLUMN_NONE_SENTINEL
        else (session.target_column or "None")
    )

    reply = (
        " Perfect! I have everything I need to build your dashboard.\n\n"
        "**Dashboard Configuration:**\n"
        f"• Domain: {session.analysis_type.title() if session.analysis_type else '—'}\n"
        f"• Goal: {(session.goal or '').replace('_', ' ').title()}\n"
        f"• Primary Metric: {display_target}\n"
        f"• Detail Level: {(session.dashboard_level or '').title()}\n"
        f"• Export Code: {'Yes' if session.download_code else 'No'}\n\n"
        " Building your dashboard now..."
    )
    return reply, session
