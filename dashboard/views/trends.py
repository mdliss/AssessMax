"""Trends view – longitudinal analytics for classes and students."""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from components import (
    HeroBadge,
    MetricDatum,
    render_empty_state,
    render_metric_grid,
    render_notification,
    render_page_header,
    render_section_header,
)
from utils import create_trend_chart, format_skill_name

SKILLS = ["empathy", "adaptability", "collaboration", "communication", "self_regulation"]


def show_trends() -> None:
    """Display trend analysis with multi-week rollups."""

    with st.container():
        st.markdown("<div class='pulse-form drop-in'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 1, 1], gap="large")
        with col1:
            time_range = st.select_slider(
                "Window",
                options=[4, 8, 12],
                value=8,
                format_func=lambda x: f"{x} week window",
                help="Select the time horizon for the trend analysis.",
            )
        with col2:
            view_type = st.radio(
                "View Mode",
                ["Class", "Student"],
                index=0,
                help="Toggle between class-wide and individual insights.",
            )
        with col3:
            smoothing = st.selectbox(
                "Smoothing",
                ["Simple Moving Average", "Exponential"],
                help="Choose the smoothing algorithm for trend lines.",
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='pulse-divider'></div>", unsafe_allow_html=True)

    if view_type == "Class":
        _render_class_trends(time_range, smoothing)
    else:
        _render_student_trends(time_range, smoothing)


def _render_class_trends(time_range: int, smoothing: str) -> None:
    with st.container():
        st.markdown("<div class='pulse-form drop-in'>", unsafe_allow_html=True)
        class_id = st.text_input(
            "Class Identifier",
            value="MS-7A",
            help="Enter the cohort identifier to visualize. Defaults to synthetic class data.",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if not class_id:
        render_empty_state("Awaiting Class Identifier", "Provide a class ID to build the timeline.")
        return

    df = _generate_trend_dataframe(time_range, seed=hash(class_id) % 1_000_000)
    render_notification(
        "Using synthetic class telemetry aligned with rubric expectations. Connect the backend API to stream real data.",
        label="Demo Mode",
    )

    cohort_metrics = _calculate_cohort_metrics(df)
    render_page_header(
        "Trend Horizon",
        f"Cohort momentum for {class_id}.",
        badges=[
            HeroBadge(label="Window", value=f"{time_range} weeks", tone="accent"),
            HeroBadge(label="View", value="Class", tone="neutral"),
            HeroBadge(label="Smoothing", value=smoothing, tone="neutral"),
        ],
    )
    render_section_header("Momentum Summary", "Window-level indicators for this class.")
    render_metric_grid(
        [
            MetricDatum("Window Span", f"{time_range} weeks", caption="Trend horizon"),
            MetricDatum("Top Skill Momentum", cohort_metrics["top_skill"], delta=f"{cohort_metrics['top_delta']:+.1f}", delta_variant="up"),
            MetricDatum("Participation", f"{cohort_metrics['participation']}%", caption="Roster coverage"),
            MetricDatum("Average Growth", f"{cohort_metrics['avg_growth']:+.1f}", caption="All skills Δ"),
        ],
        columns=4,
    )

    render_section_header("Multi-skill Overlay", "Track each skill's contribution over time.")
    overlay_fig = px.line(
        df.melt(id_vars="assessed_on", value_vars=SKILLS, var_name="skill", value_name="score"),
        x="assessed_on",
        y="score",
        color="skill",
        color_discrete_sequence=[ "#14b8a6", "#0ea5e9", "#6366f1", "#f472b6", "#f97316" ],
        markers=True,
    )
    overlay_fig.update_traces(marker=dict(size=6, line=dict(width=1, color="rgba(255,255,255,0.85)")))
    overlay_fig.update_layout(
        hovermode="x unified",
        xaxis_title="Assessment Date",
        yaxis_title="Average Score",
        template="plotly_white",
        paper_bgcolor="rgba(255,255,255,0.95)",
        plot_bgcolor="rgba(248,249,250,0.85)",
        font=dict(color="#374151", family="Roboto Mono"),
        legend_title_text="Skill",
    )
    st.plotly_chart(overlay_fig, use_container_width=True, theme=None)

    render_section_header("Skill Spotlight", "Inspect skills individually for deeper insights.")
    tabs = st.tabs([format_skill_name(skill) for skill in SKILLS])
    for tab, skill in zip(tabs, SKILLS):
        with tab:
            fig = create_trend_chart(df, skill, title=f"{format_skill_name(skill)} Momentum")
            st.plotly_chart(fig, use_container_width=True, theme=None)


def _render_student_trends(time_range: int, smoothing: str) -> None:
    with st.container():
        st.markdown("<div class='pulse-form drop-in'>", unsafe_allow_html=True)
        student_id = st.text_input(
            "Student UUID",
            value="550e8400-e29b-41d4-a716-446655440001",
            help="Paste a student UUID. Defaults to a synthetic exemplar for demo mode.",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if not student_id:
        render_empty_state("Awaiting Student Identifier", "Enter a student UUID to examine their progression.")
        return

    df = _generate_trend_dataframe(time_range, seed=hash(student_id) % 1_000_000 + 42)
    render_notification(
        "Streaming rubric-compliant synthetic data. Connect the assessments API for real learner trajectories.",
        label="Demo Mode",
    )

    momentum = _calculate_student_momentum(df)
    render_page_header(
        "Trend Horizon",
        f"Personal momentum for learner {student_id[:8].upper()}…",
        badges=[
            HeroBadge(label="Window", value=f"{time_range} weeks", tone="accent"),
            HeroBadge(label="View", value="Student", tone="neutral"),
            HeroBadge(label="Student", value=student_id[:8].upper(), tone="neutral"),
            HeroBadge(label="Smoothing", value=smoothing, tone="neutral"),
        ],
    )
    render_section_header("Momentum Summary", "Individual trend indicators over the selected window.")
    render_metric_grid(
        [
            MetricDatum("Momentum Skill", momentum["focus_skill"], delta=f"{momentum['delta']:+.1f}", delta_variant="up"),
            MetricDatum("Latest Score", f"{momentum['latest']:.1f}", caption="Peak skill"),
            MetricDatum("Confidence Window", f"{momentum['stability']}%", caption="Score stability range"),
            MetricDatum("Sessions Analyzed", str(len(df)), caption="Assessments"),
        ],
        columns=4,
    )

    render_section_header("Personal Trendlines", "Skill-by-skill trajectories for the selected learner.")
    tabs = st.tabs([format_skill_name(skill) for skill in SKILLS])
    for tab, skill in zip(tabs, SKILLS):
        with tab:
            fig = create_trend_chart(df, skill, title=f"{format_skill_name(skill)} Progression")
            st.plotly_chart(fig, use_container_width=True, theme=None)


def _generate_trend_dataframe(weeks: int, seed: int) -> pd.DataFrame:
    """Generate synthetic trend data for each skill."""

    random.seed(seed)
    base_date = date.today()
    rows: list[dict[str, Any]] = []

    score_baseline = {skill: random.uniform(60, 80) for skill in SKILLS}

    for week in range(weeks):
        assessed_on = base_date - timedelta(days=7 * (weeks - week - 1))
        row = {"assessed_on": assessed_on}
        for skill in SKILLS:
            drift = random.uniform(-2.5, 3.5)
            previous = rows[-1][skill] if rows else score_baseline[skill]
            score = max(55, min(previous + drift, 98))
            row[skill] = round(score, 1)
        rows.append(row)

    df = pd.DataFrame(rows)
    df["assessed_on"] = pd.to_datetime(df["assessed_on"])
    return df


def _calculate_cohort_metrics(df: pd.DataFrame) -> dict[str, Any]:
    deltas = {skill: df[skill].iloc[-1] - df[skill].iloc[0] for skill in SKILLS}
    top_skill = max(deltas, key=deltas.get)
    participation = random.randint(88, 97)
    avg_growth = sum(deltas.values()) / len(deltas)
    return {
        "top_skill": format_skill_name(top_skill),
        "top_delta": deltas[top_skill],
        "participation": participation,
        "avg_growth": avg_growth,
    }


def _calculate_student_momentum(df: pd.DataFrame) -> dict[str, Any]:
    latest_scores = {skill: df[skill].iloc[-1] for skill in SKILLS}
    focus_skill = max(latest_scores, key=latest_scores.get)
    delta = latest_scores[focus_skill] - df[focus_skill].iloc[0]
    stability = round(
        (df[focus_skill].rolling(window=3, min_periods=1).std().fillna(0).mean() / latest_scores[focus_skill]) * 100,
        1,
    )
    return {
        "focus_skill": format_skill_name(focus_skill),
        "delta": delta,
        "latest": latest_scores[focus_skill],
        "stability": max(0, 100 - stability),
    }
