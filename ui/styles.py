"""Shared Streamlit page styling."""

from __future__ import annotations

import streamlit as st

from config.default_config import AppConfig


def render_page_styles(app_config: AppConfig) -> None:
    """Add light product styling without overwhelming Streamlit defaults."""

    primary = app_config.branding.primary_color
    accent = app_config.branding.accent_color
    st.markdown(
        f"""
        <style>
        :root {{
            --app-bg: #f6f8fb;
            --surface: #ffffff;
            --surface-soft: #f9fbff;
            --border: #d9e2ef;
            --border-strong: #c7d3e3;
            --text: #111827;
            --muted: #5b677a;
            --accent: {primary};
            --accent-strong: {accent};
            --accent-soft: #eaf2ff;
            --danger-soft: #fff1f2;
            --danger: #b42318;
            --warning-soft: #fff8e6;
            --warning: #9a6700;
        }}
        .stApp,
        [data-testid="stAppViewContainer"] {{
            background:
                linear-gradient(
                    rgba(246, 248, 251, 0.48),
                    rgba(246, 248, 251, 0.48)
                ),
                url("https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&w=1800&q=80");
            background-attachment: fixed;
            background-color: var(--app-bg);
            background-position: center;
            background-size: cover;
            color: var(--text);
        }}
        section[data-testid="stMain"],
        div[data-testid="stMainBlockContainer"] {{
            background: transparent;
        }}
        [data-testid="stHeader"] {{
            background: rgba(246, 248, 251, 0.68);
            backdrop-filter: blur(4px);
        }}
        [data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 0.86);
        }}
        .block-container {{
            background: rgba(255, 255, 255, 0.76);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 14px 40px rgba(17, 24, 39, 0.06);
            backdrop-filter: blur(2px);
            margin-top: 1.5rem;
            margin-bottom: 1.5rem;
            padding-top: 2rem;
        }}
        h1, h2, h3, h4, h5, h6, p, label, span {{
            color: var(--text);
        }}
        div[data-testid="stFileUploader"] section {{
            background: var(--surface-soft);
            border-color: var(--border-strong);
            border-radius: 8px;
        }}
        div[data-testid="stDataFrame"] {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 6px 18px rgba(17, 24, 39, 0.04);
            overflow: hidden;
        }}
        div[data-testid="stMetric"] {{
            background: var(--surface-soft);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.75rem 1rem;
        }}
        div[data-testid="stMetricLabel"] {{
            color: var(--muted);
        }}
        div[data-baseweb="select"] > div {{
            background: var(--surface);
            border-color: var(--border-strong);
            color: var(--text);
            border-radius: 8px;
        }}
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] input {{
            color: var(--text);
        }}
        div[data-baseweb="popover"],
        ul[data-testid="stVirtualDropdown"] {{
            background: var(--surface);
            color: var(--text);
        }}
        div[data-testid="stButton"] > button,
        div[data-testid="stDownloadButton"] > button {{
            background: var(--surface);
            border: 1px solid #bdd4f8;
            border-radius: 8px;
            color: var(--accent);
            font-weight: 650;
            box-shadow: 0 3px 10px rgba(37, 99, 235, 0.08);
        }}
        div[data-testid="stButton"] > button:hover,
        div[data-testid="stDownloadButton"] > button:hover {{
            background: var(--accent-soft);
            border-color: #8db7f4;
            color: var(--accent-strong);
        }}
        div[data-testid="stButton"] > button[kind="primary"] {{
            background: var(--accent-soft);
            border-color: #8db7f4;
            color: var(--accent-strong);
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.12);
        }}
        div[data-baseweb="tab-list"] {{
            background: var(--surface-soft);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.25rem;
        }}
        button[data-baseweb="tab"] {{
            border-radius: 8px;
            color: var(--muted);
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            background: var(--accent-soft);
            color: var(--accent);
        }}
        div[data-testid="stAlert"] {{
            background: var(--surface-soft);
            color: var(--text);
            border-radius: 8px;
        }}
        .validation-box {{
            border: 1px solid var(--border);
            border-left-width: 5px;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            margin: 0.75rem 0;
            background: var(--surface-soft);
            color: var(--text);
        }}
        .validation-box strong {{
            display: block;
            margin-bottom: 0.35rem;
        }}
        .validation-error {{
            border-left-color: var(--danger);
            background: var(--danger-soft);
        }}
        .validation-warning {{
            border-left-color: var(--warning);
            background: var(--warning-soft);
        }}
        .muted-note {{
            color: var(--muted);
            font-size: 0.95rem;
        }}
        .brand-header {{
            border-bottom: 1px solid var(--border);
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
        }}
        .brand-kicker {{
            color: var(--accent);
            font-size: 0.82rem;
            font-weight: 700;
            text-transform: uppercase;
        }}
        div[data-testid="stMetricValue"] {{
            font-size: 1.6rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
