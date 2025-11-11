"""Shared UI components for the PulseMax dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import streamlit as st


@dataclass(frozen=True)
class HeroBadge:
    """Badge descriptor for hero sections."""

    label: str
    value: str | None = None
    tone: str = "accent"  # accent | danger | neutral


@dataclass(frozen=True)
class MetricDatum:
    """Data needed to render a compact metric card."""

    label: str
    value: str
    delta: str | None = None
    delta_variant: str = "neutral"  # options: up, down, neutral
    caption: str | None = None


THEME_PATH = Path(__file__).parent / "styles" / "pulsemax.css"


def inject_theme() -> None:
    """Load the PulseMax CSS theme into the active Streamlit app."""

    if "pulsemax_theme_loaded" in st.session_state:
        return

    theme_css = THEME_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{theme_css}</style>", unsafe_allow_html=True)
    st.session_state["pulsemax_theme_loaded"] = True


def render_page_header(
    title: str,
    subtitle: str | None = None,
    badges: Iterable[HeroBadge] | None = None,
) -> None:
    """Render a hero header with optional badges."""

    badge_html = ""
    if badges:
        badge_fragments = []
        for badge in badges:
            tone_class = f"pulse-badge {badge.tone}"
            badge_value = f"<strong>{badge.value}</strong>" if badge.value else ""
            badge_fragments.append(
                f"<span class='{tone_class}'>{badge_value} {badge.label}</span>"
            )
        badge_html = "<div class='pulse-hero-badges'>" + " ".join(badge_fragments) + "</div>"

    subtitle_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"""
        <section class="pulse-hero drop-in">
            <div class="pulse-subheading">PulseMax</div>
            <h1>{title}</h1>
            {subtitle_html}
            {badge_html}
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_logo_badge(title: str, subtitle: str | None = None) -> None:
    """Backward compatible wrapper around render_page_header."""

    render_page_header(title=title, subtitle=subtitle)


def render_section_header(title: str, description: str | None = None) -> None:
    """Render a standardized section heading."""

    description_html = f"<p>{description}</p>" if description else ""
    st.markdown(
        f"""
        <div class="drop-in">
            <div class="pulse-subheading">{title}</div>
            {description_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(message: str, help_text: str | None = None) -> None:
    """Render an empty-state card."""

    help_html = f"<span>{help_text}</span>" if help_text else ""
    st.markdown(
        f"""
        <div class="pulse-empty-state drop-in">
            <strong>{message}</strong>
            {help_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_grid(metrics: Iterable[MetricDatum], columns: int = 4) -> None:
    """Render metrics in a responsive grid of Pulse cards."""

    metric_list = list(metrics)
    if not metric_list:
        return

    cols = st.columns(min(columns, len(metric_list)))
    for ordinal, metric in enumerate(metric_list):
        col = cols[ordinal % len(cols)]
        with col:
            _render_metric_card(metric, 0.15 * ordinal)


def _render_metric_card(metric: MetricDatum, delay: float) -> None:
    """Render a single metric card."""

    delta_icon = ""
    delta_class = "pulse-badge neutral"
    if metric.delta:
        if metric.delta_variant == "up":
            delta_icon = "▲"
            delta_class = "pulse-badge"
        elif metric.delta_variant == "down":
            delta_icon = "▼"
            delta_class = "pulse-badge danger"

    caption_html = (
        f"<span class='pulse-subheading'>{metric.caption}</span>"
        if metric.caption
        else ""
    )

    st.markdown(
        f"""
        <div class="pulse-card drop-in delay-{min(int(delay * 10)+1, 5)}">
            {caption_html}
            <div class="pulse-metric-value">{metric.value}</div>
            <div class="pulse-pill">{metric.label}</div>
            {'<div class="pill-group"><span class="' + delta_class + f'">{delta_icon} {metric.delta}</span></div>' if metric.delta else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_notification(message: str, label: str = "Status") -> None:
    """Render a dismiss-less notification banner."""

    st.markdown(
        f"""
        <div class="notification-banner drop-in delay-1">
            <div>
                <div class="label">{label}</div>
                <strong>{message}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Render the shared PulseMax footer."""

    st.markdown(
        """
        <footer>
            <div class="footer-grid">
                <span>PulseMax &bull; Middle School Non-Academic Skills Engine</span>
                <span>Designed with empathy-first analytics.</span>
                <span>Build {version} · Crafted for deployment ready reviews.</span>
            </div>
        </footer>
        """.format(version="2024.12"),
        unsafe_allow_html=True,
    )
