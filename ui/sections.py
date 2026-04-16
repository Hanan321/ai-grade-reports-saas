"""Small shared Streamlit section helpers."""

from __future__ import annotations

from html import escape

import streamlit as st


def render_validation_summary(title: str, messages: list[str], level: str) -> None:
    """Render compact validation feedback grouped by severity."""

    if not messages:
        return

    class_name = "validation-error" if level == "error" else "validation-warning"
    message_items = "".join(f"<li>{escape(message)}</li>" for message in messages)
    st.markdown(
        f"""
        <div class="validation-box {class_name}">
            <strong>{escape(title)}</strong>
            <ul>{message_items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
