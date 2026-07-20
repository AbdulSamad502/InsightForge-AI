import os
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from langgraph.graph import StateGraph, END

from langchain_core.messages import HumanMessage

from app.ai.graph.state import ReportState
from app.core.config import settings
from app.ai.llm_factory import get_fast_llm

logger = logging.getLogger(__name__)

EXPORTS_DIR = Path(settings.storage_path) / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

REPORTS_DIR = Path(settings.storage_path) / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "report.md"


# ════════════════════════════════════════════════════════════
# NODE FUNCTIONS
# Each function receives state, does work, returns partial state update
# ════════════════════════════════════════════════════════════

def gather_insights_node(state: ReportState) -> dict:
    """
    Node 1: Load chat history and dataset info from the database.
    """
    logger.info(f"[ReportGraph] gather_insights: dataset={state['dataset_id']}")
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.modules.chat.models import ChatMessage, ChatSession
        from app.modules.datasets.models import Dataset, DatasetProfile

        engine = create_engine(settings.database_url)
        Session = sessionmaker(bind=engine)
        db = Session()

        try:
            # Load dataset info
            dataset = db.query(Dataset).filter(Dataset.id == state["dataset_id"]).first()
            if not dataset:
                return {"error": f"Dataset {state['dataset_id']} not found", "status": "failed"}

            profile = db.query(DatasetProfile).filter(
                DatasetProfile.dataset_id == state["dataset_id"]
            ).first()

            dataset_info = {
                "filename": dataset.original_filename,
                "row_count": dataset.row_count or 0,
                "col_count": dataset.col_count or 0,
                "columns": [c["name"] for c in profile.columns_metadata] if profile else [],
                "status": dataset.status,
            }

            # Load last 20 assistant messages (insights from chat)
            sessions = db.query(ChatSession).filter(
                ChatSession.user_id == state["user_id"],
                ChatSession.dataset_id == state["dataset_id"],
            ).all()

            session_ids = [s.id for s in sessions]
            messages = []
            if session_ids:
                all_messages = db.query(ChatMessage).filter(
                    ChatMessage.session_id.in_(session_ids),
                    ChatMessage.role == "assistant",
                    ChatMessage.content.isnot(None),
                ).order_by(ChatMessage.created_at.desc()).limit(20).all()

                messages = [
                    {
                        "content": m.content,
                        "insight": m.insight,
                        "recommendation": m.recommendation,
                        "intent_type": m.intent_type,
                    }
                    for m in all_messages
                ]

        finally:
            db.close()

        logger.info(f"[ReportGraph] Loaded {len(messages)} messages for dataset")
        return {
            "chat_messages": messages,
            "dataset_info": dataset_info,
            "status": "running",
        }

    except Exception as e:
        logger.error(f"[ReportGraph] gather_insights failed: {e}", exc_info=True)
        return {"error": str(e), "status": "failed"}


def check_ml_node(state: ReportState) -> dict:
    """
    Node 2: Load any ML results that exist for this dataset.
    """
    logger.info(f"[ReportGraph] check_ml: dataset={state['dataset_id']}")
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.modules.ml.models import MLResult

        engine = create_engine(settings.database_url)
        Session = sessionmaker(bind=engine)
        db = Session()

        try:
            # Try exact dataset match first
            results = db.query(MLResult).filter(
                MLResult.dataset_id == state["dataset_id"],
                MLResult.status == "complete",
            ).order_by(MLResult.created_at.desc()).limit(5).all()

            # If no results for this dataset, get user's most recent ML results
            if not results:
                results = db.query(MLResult).filter(
                    MLResult.user_id == state["user_id"],
                    MLResult.status == "complete",
                ).order_by(MLResult.created_at.desc()).limit(5).all()

            ml_results = [
                {
                    "model_type": r.model_type,
                    "target_column": r.target_column,
                    "result_data": r.result_data,
                    "chart_data": r.chart_data,
                    "completed_at": str(r.completed_at),
                }
                for r in results
            ]
        finally:
            db.close()

        logger.info(f"[ReportGraph] Found {len(ml_results)} ML results")
        return {"ml_results": ml_results}

    except Exception as e:
        logger.warning(f"[ReportGraph] check_ml failed (non-fatal): {e}")
        return {"ml_results": []}
def generate_charts_node(state: ReportState) -> dict:
    """
    Node 3: Collect chart data only.
    PNG export disabled.
    """

    logger.info("[ReportGraph] generate_charts skipped export")

    return {
        "chart_paths": []
    }
# def generate_charts_node(state: ReportState):

#     logger.info("[ReportGraph] generate_charts skipped")

#     state["chart_paths"] = []

#     return state
def write_summary_node(state: ReportState) -> dict:
    """
    Node 4: LLM generates executive summary, key insights, and recommendations.
    """
    logger.info(f"[ReportGraph] write_summary")
    try:
        prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")

        # Build insights text from chat history
        messages = state.get("chat_messages", [])
        insights_text = ""
        key_insights = []
        recommendations = []

        for msg in messages[:10]:
            if msg.get("insight"):
                insights_text += f"- {msg['insight']}\n"
                key_insights.append(msg["insight"])
            if msg.get("recommendation"):
                recommendations.append(msg["recommendation"])

        if not insights_text:
            insights_text = "No specific insights generated yet. Dataset was uploaded and profiled."

        # Build ML summary
        ml_results = state.get("ml_results", [])
        ml_summary = ""
        for ml in ml_results:
            model_type = ml.get("model_type", "")
            data = ml.get("result_data", {})
            if model_type == "forecast":
                preds = data.get("predictions", [])
                dates = data.get("dates", [])
                if preds and dates:
                    ml_summary += f"Forecast: {dates[0]} predicted value = {preds[0]:,.0f}\n"
            elif model_type == "anomaly":
                count = data.get("anomaly_count", 0)
                pct = data.get("anomaly_pct", 0)
                ml_summary += f"Anomaly Detection: {count} anomalies found ({pct}% of data)\n"
            elif model_type == "churn":
                accuracy = data.get("accuracy", 0)
                ml_summary += f"Churn Prediction: Model accuracy {accuracy:.1%}\n"

        if not ml_summary:
            ml_summary = "No ML models run on this dataset yet."

        dataset_info = state.get("dataset_info", {})

        prompt = prompt_template.format(
            dataset_name=dataset_info.get("filename", "Unknown Dataset"),
            row_count=dataset_info.get("row_count", 0),
            col_count=dataset_info.get("col_count", 0),
            report_date=datetime.now().strftime("%B %d, %Y"),
            insights=insights_text[:1500],
            ml_summary=ml_summary[:500],
        )

        llm = get_fast_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        summary_text = response.content.strip()

        logger.info(f"[ReportGraph] Summary generated: {len(summary_text)} chars")
        return {
            "summary_text": summary_text,
            "key_insights": key_insights[:5],
            "recommendations": recommendations[:3],
        }

    except Exception as e:
        logger.error(f"[ReportGraph] write_summary failed: {e}")
        return {
            "summary_text": "Executive summary could not be generated automatically.",
            "key_insights": [],
            "recommendations": [],
        }


def compile_pdf_node(state: ReportState) -> dict:
    logger.info(
    f"[ReportGraph] ML results in compile: {len(state.get('ml_results', []))}"
)
    logger.info(f"[ReportGraph] compile_pdf")
    


    """
    Node 5: Assemble all sections into a professional PDF using ReportLab.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            PageBreak, Image, HRFlowable,
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

        dataset_info = state.get("dataset_info", {})
        pdf_filename = f"report_{state['report_id']}.pdf"
        pdf_path = str(REPORTS_DIR / pdf_filename)

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )

        # ── Styles ─────────────────────────────────────────
        styles = getSampleStyleSheet()

        style_cover_title = ParagraphStyle(
            "CoverTitle",
            parent=styles["Title"],
            fontSize=28,
            textColor=colors.HexColor("#1a1a2e"),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )
        style_cover_sub = ParagraphStyle(
            "CoverSub",
            parent=styles["Normal"],
            fontSize=14,
            textColor=colors.HexColor("#4361ee"),
            spaceAfter=8,
            alignment=TA_CENTER,
        )
        style_section_header = ParagraphStyle(
            "SectionHeader",
            parent=styles["Heading1"],
            fontSize=16,
            textColor=colors.HexColor("#1a1a2e"),
            spaceBefore=16,
            spaceAfter=8,
            fontName="Helvetica-Bold",
            borderPad=4,
        )
        style_body = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=11,
            textColor=colors.HexColor("#333333"),
            spaceAfter=8,
            leading=16,
            alignment=TA_JUSTIFY,
        )
        style_insight = ParagraphStyle(
            "Insight",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#1a1a2e"),
            spaceAfter=6,
            leading=14,
            leftIndent=12,
            borderPad=6,
        )
        style_meta = ParagraphStyle(
            "Meta",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#666666"),
            spaceAfter=4,
            alignment=TA_CENTER,
        )

        story = []
        W, H = A4

        # ── PAGE 1: COVER ──────────────────────────────────
        story.append(Spacer(1, 4*cm))

        story.append(Paragraph("AI Data Analyst", style_cover_title))
        story.append(Paragraph("Business Intelligence Report", style_cover_sub))
        story.append(Spacer(1, 0.5*cm))
        story.append(HRFlowable(
            width="80%", thickness=2,
            color=colors.HexColor("#4361ee"),
            hAlign="CENTER",
        ))
        story.append(Spacer(1, 1*cm))

        story.append(Paragraph(
            f"Dataset: {dataset_info.get('filename', 'Unknown')}",
            style_meta,
        ))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            style_meta,
        ))
        story.append(Paragraph(
            f"{dataset_info.get('row_count', 0):,} rows · "
            f"{dataset_info.get('col_count', 0)} columns",
            style_meta,
        ))

        story.append(PageBreak())

        # ── PAGE 2: EXECUTIVE SUMMARY ──────────────────────
        story.append(Paragraph("Executive Summary", style_section_header))
        story.append(HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor("#e0e0e0"),
        ))
        story.append(Spacer(1, 0.3*cm))

        summary = state.get("summary_text", "No summary available.")
        for para in summary.split("\n\n"):
            if para.strip():
                story.append(Paragraph(para.strip(), style_body))
                story.append(Spacer(1, 0.2*cm))

        story.append(PageBreak())

        # ── PAGE 3: DATA OVERVIEW ──────────────────────────
        story.append(Paragraph("Dataset Overview", style_section_header))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e0e0e0")))
        story.append(Spacer(1, 0.3*cm))

        overview_data = [
            ["Metric", "Value"],
            ["Total Rows", f"{dataset_info.get('row_count', 0):,}"],
            ["Total Columns", str(dataset_info.get("col_count", 0))],
            ["File Name", dataset_info.get("filename", "N/A")],
            ["Analysis Status", dataset_info.get("status", "N/A").title()],
        ]

        col_list = dataset_info.get("columns", [])
        if col_list:
            overview_data.append(["Columns", ", ".join(col_list[:10])])

        overview_table = Table(overview_data, colWidths=[5*cm, 11*cm])
        overview_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4361ee")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, 0), 11),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4ff")]),
            ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("FONTSIZE",   (0, 1), (-1, -1), 10),
            ("PADDING",    (0, 0), (-1, -1), 8),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(overview_table)
        story.append(Spacer(1, 0.5*cm))

        # ── KEY INSIGHTS ───────────────────────────────────
        key_insights = state.get("key_insights", [])
        if key_insights:
            story.append(Paragraph("Key Business Insights", style_section_header))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e0e0e0")))
            story.append(Spacer(1, 0.3*cm))

            for i, insight in enumerate(key_insights[:5], 1):
                bullet_text = f"<b>{i}.</b> {insight}"
                story.append(Paragraph(bullet_text, style_insight))
                story.append(Spacer(1, 0.2*cm))

        story.append(PageBreak())

        # ── CHARTS ─────────────────────────────────────────
        chart_paths = [p for p in state.get("chart_paths", []) if Path(p).exists()]
        if chart_paths:
            story.append(Paragraph("Data Visualizations", style_section_header))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e0e0e0")))
            story.append(Spacer(1, 0.3*cm))

            page_width = W - 4*cm
            for i, chart_path in enumerate(chart_paths):
                try:
                    img = Image(chart_path, width=page_width, height=page_width * 0.55)
                    story.append(img)
                    story.append(Spacer(1, 0.3*cm))
                    if (i + 1) % 2 == 0 and i < len(chart_paths) - 1:
                        story.append(PageBreak())
                except Exception as e:
                    logger.warning(f"Could not embed chart {chart_path}: {e}")

            story.append(PageBreak())

        # ── ML RESULTS ─────────────────────────────────────
        ml_results = state.get("ml_results", [])
        if ml_results:
            story.append(Paragraph("Machine Learning Results", style_section_header))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e0e0e0")))
            story.append(Spacer(1, 0.3*cm))

            for ml in ml_results:
                model_type = ml.get("model_type", "").title()
                data = ml.get("result_data", {})
                story.append(Paragraph(f"{model_type} Model", ParagraphStyle(
                    "MLHeader", parent=styles["Heading2"], fontSize=13,
                    textColor=colors.HexColor("#4361ee"), spaceBefore=8
                )))

                if ml.get("model_type") == "forecast":
                    preds = data.get("predictions", [])
                    dates = data.get("dates", [])
                    mae = data.get("mae", 0)
                    r2 = data.get("r2_score", 0)
                    story.append(Paragraph(
                        f"Model Performance: MAE = {mae:,.0f}, R² = {r2:.3f}",
                        style_body
                    ))
                    for d, p in zip(dates, preds):
                        story.append(Paragraph(f"• {d}: Predicted {p:,.0f}", style_insight))

                elif ml.get("model_type") == "anomaly":
                    count = data.get("anomaly_count", 0)
                    pct = data.get("anomaly_pct", 0)
                    total = data.get("total_count", 0)
                    story.append(Paragraph(
                        f"Detected {count} anomalies out of {total} data points ({pct}%).",
                        style_body
                    ))

                elif ml.get("model_type") == "churn":
                    accuracy = data.get("accuracy", 0)
                    fi = data.get("feature_importance", [])
                    story.append(Paragraph(
                        f"Model Accuracy: {accuracy:.1%}. Top churn drivers:",
                        style_body
                    ))
                    for f in fi[:3]:
                        story.append(Paragraph(
                            f"• {f['feature']}: {f['importance']:.1%} importance",
                            style_insight
                        ))

                story.append(Spacer(1, 0.3*cm))

            story.append(PageBreak())

        # ── RECOMMENDATIONS ────────────────────────────────
        recommendations = state.get("recommendations", [])
        if recommendations:
            story.append(Paragraph("Strategic Recommendations", style_section_header))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e0e0e0")))
            story.append(Spacer(1, 0.3*cm))

            for i, rec in enumerate(recommendations[:3], 1):
                rec_data = [[
                    Paragraph(str(i), ParagraphStyle(
                        "Num", parent=styles["Normal"],
                        fontSize=18, fontName="Helvetica-Bold",
                        textColor=colors.HexColor("#4361ee"),
                        alignment=TA_CENTER,
                    )),
                    Paragraph(rec, style_body),
                ]]
                rec_table = Table(rec_data, colWidths=[1.5*cm, 14*cm])
                rec_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#f0f4ff")),
                    ("VALIGN",     (0, 0), (-1, -1), "TOP"),
                    ("PADDING",    (0, 0), (-1, -1), 10),
                    ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                    ("ROUNDEDCORNERS", [4]),
                ]))
                story.append(rec_table)
                story.append(Spacer(1, 0.3*cm))

        # ── FOOTER PAGE ────────────────────────────────────
        story.append(PageBreak())
        story.append(Spacer(1, 8*cm))
        story.append(Paragraph(
            "Generated by AI Data Analyst",
            ParagraphStyle("Footer", parent=styles["Normal"],
                fontSize=12, textColor=colors.HexColor("#666666"), alignment=TA_CENTER)
        ))
        story.append(Paragraph(
            "Powered by LangChain · Ollama · FastAPI",
            ParagraphStyle("Footer2", parent=styles["Normal"],
                fontSize=10, textColor=colors.HexColor("#999999"), alignment=TA_CENTER)
        ))

        # Build PDF
        doc.build(story)
        logger.info(f"[ReportGraph] PDF compiled: {pdf_path}")
        return {"pdf_path": pdf_path, "status": "complete"}

    except Exception as e:
        logger.error(f"[ReportGraph] compile_pdf failed: {e}", exc_info=True)
        return {"error": str(e), "status": "failed"}


def error_node(state: ReportState) -> dict:
    """Handles any node failure gracefully."""
    error = state.get("error", "Unknown error")
    logger.error(f"[ReportGraph] Error node reached: {error}")
    return {"status": "failed"}


# ════════════════════════════════════════════════════════════
# CONDITIONAL ROUTING
# ════════════════════════════════════════════════════════════

def should_continue(state: ReportState) -> str:
    """Route to error node if any previous node failed."""
    if state.get("error") or state.get("status") == "failed":
        return "error"
    return "continue"


# ════════════════════════════════════════════════════════════
# BUILD THE GRAPH
# ════════════════════════════════════════════════════════════

def build_report_graph() -> StateGraph:
    """
    Assemble the LangGraph StateGraph for report generation.
    
    Flow:
    gather_insights → check_ml → generate_charts → write_summary → compile_pdf
    
    Any node failure → error_node → END
    """
    graph = StateGraph(ReportState)

    # Add nodes
    graph.add_node("gather_insights", gather_insights_node)
    graph.add_node("check_ml",        check_ml_node)
    graph.add_node("generate_charts", generate_charts_node)
    graph.add_node("write_summary",   write_summary_node)
    graph.add_node("compile_pdf",     compile_pdf_node)
    graph.add_node("handle_error", error_node)

    # Entry point
    graph.set_entry_point("gather_insights")

    # Conditional edges after each node
    graph.add_conditional_edges(
        "gather_insights",
        should_continue,
        {"continue": "check_ml", "error": "handle_error"},
    )
    graph.add_conditional_edges(
        "check_ml",
        should_continue,
        {"continue": "generate_charts", "error": "handle_error"},
    )
    graph.add_conditional_edges(
        "generate_charts",
        should_continue,
        {"continue": "write_summary", "error": "handle_error"},
    )
    graph.add_conditional_edges(
        "write_summary",
        should_continue,
        {"continue": "compile_pdf", "error": "handle_error"},
    )

    # Terminal edges
    graph.add_edge("compile_pdf", END)
    graph.add_edge("handle_error", END)

    return graph.compile()


# Singleton compiled graph
report_pipeline = build_report_graph()