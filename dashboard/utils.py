"""Utility functions for the dashboard"""

import io
from datetime import date
from typing import Any
from uuid import UUID

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def format_skill_name(skill: str) -> str:
    """Format skill name for display"""
    return skill.replace("_", " ").title()


def get_skill_color(skill: str) -> str:
    """Get consistent color for each skill"""
    colors_map = {
        "empathy": "#FF6B6B",
        "adaptability": "#4ECDC4",
        "collaboration": "#45B7D1",
        "communication": "#FFA07A",
        "self_regulation": "#98D8C8",
    }
    return colors_map.get(skill, "#999999")


def create_skill_chart(data: dict[str, float], title: str = "Skill Scores") -> go.Figure:
    """
    Create a radar chart for skill scores

    Args:
        data: Dictionary of skill names to scores (0-100)
        title: Chart title

    Returns:
        Plotly figure object
    """
    skills = [format_skill_name(k) for k in data.keys()]
    values = list(data.values())

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=skills,
            fill="toself",
            name="Scores",
            line=dict(color="#14b8a6", width=3),
            fillcolor="rgba(20, 184, 166, 0.32)",
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickmode="linear",
                tick0=0,
                dtick=20,
                gridcolor="rgba(38, 38, 38, 0.7)",
                linecolor="rgba(38, 38, 38, 0.7)",
                tickfont=dict(color="#b3b3b3"),
            ),
            angularaxis=dict(
                tickfont=dict(color="#d1d5db", size=11, family="Roboto Mono"),
            ),
        ),
        showlegend=False,
        title=dict(text=title, x=0.5, xanchor="center", font=dict(color="#ffffff", size=18)),
        margin=dict(l=45, r=45, t=70, b=45),
        height=400,
    )

    _apply_dark_plot_theme(fig)
    return fig


def create_trend_chart(
    df: pd.DataFrame, skill: str, title: str = "Skill Trend"
) -> go.Figure:
    """
    Create a line chart showing skill score trends over time

    Args:
        df: DataFrame with 'assessed_on' and skill score columns
        skill: Skill name
        title: Chart title

    Returns:
        Plotly figure object
    """
    fig = px.line(
        df,
        x="assessed_on",
        y=skill,
        title=title,
        labels={"assessed_on": "Date", skill: "Score (0-100)"},
        markers=True,
    )

    fig.update_traces(
        line=dict(color=get_skill_color(skill), width=3),
        marker=dict(size=9, line=dict(width=1.5, color="rgba(255,255,255,0.85)")),
        hovertemplate="<b>%{y:.1f}</b><br>%{x|%Y-%m-%d}<extra></extra>",
    )

    fig.update_layout(
        hovermode="x unified",
        xaxis_title="Assessment Date",
        yaxis_title="Score",
        yaxis_range=[0, 100],
        xaxis=dict(
            gridcolor="rgba(38, 38, 38, 0.6)",
            tickfont=dict(color="#b3b3b3", family="Roboto Mono"),
        ),
        yaxis=dict(
            gridcolor="rgba(38, 38, 38, 0.6)",
            tickfont=dict(color="#b3b3b3", family="Roboto Mono"),
        ),
        height=400,
    )

    _apply_dark_plot_theme(fig)
    return fig


def export_to_csv(data: list[dict[str, Any]], filename: str = "export.csv") -> bytes:
    """
    Export data to CSV format

    Args:
        data: List of dictionaries to export
        filename: Output filename

    Returns:
        CSV data as bytes
    """
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode("utf-8")


def export_to_pdf(
    title: str,
    data: list[dict[str, Any]],
    class_id: str | None = None,
    student_name: str | None = None,
) -> bytes:
    """
    Export data to PDF format

    Args:
        title: PDF title
        data: List of dictionaries to export
        class_id: Optional class ID
        student_name: Optional student name

    Returns:
        PDF data as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#14b8a6"),
        spaceAfter=20,
    )

    # Add title
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.2 * inch))

    # Add metadata
    if class_id:
        story.append(Paragraph(f"<b>Class ID:</b> {class_id}", styles["Normal"]))
    if student_name:
        story.append(Paragraph(f"<b>Student:</b> {student_name}", styles["Normal"]))

    story.append(Spacer(1, 0.3 * inch))

    # Convert data to table
    if data:
        df = pd.DataFrame(data)

        # Create table data
        table_data = [df.columns.tolist()] + df.values.tolist()

        # Create table
        table = Table(table_data)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#14b8a6")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#1f1f1f")),
                    ("TEXTCOLOR", (0, 1), (-1, -1), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#0d9488")),
                ]
            )
        )

        story.append(table)

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def format_date(d: date | str) -> str:
    """Format date for display"""
    if isinstance(d, str):
        return d
    return d.strftime("%Y-%m-%d")


def parse_uuid(uuid_str: str) -> UUID:
    """Parse UUID string safely"""
    try:
        return UUID(uuid_str)
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid UUID: {uuid_str}")


def _apply_dark_plot_theme(fig: go.Figure) -> None:
    """Apply the PulseMax dark theme to a Plotly figure in-place."""

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(20,20,20,0.78)",
        font=dict(color="#d1d5db", family="Roboto Mono"),
        legend=dict(
            bgcolor="rgba(20,20,20,0.6)",
            bordercolor="rgba(38,38,38,0.6)",
            borderwidth=1,
        ),
    )
