"""Visual layer for the refined Wayfare UI: global CSS plus small HTML helpers.

Design tokens follow the "Wayfare UI Screens" design (laptop + phone). Everything here is presentation
only; no planner logic lives in this module.
"""

import re

import streamlit as st

LOGO = ('<svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true"><circle cx="24" cy="10" r="4" fill="#9CCFB1"/>'
        '<path d="M2 28l10-14 6 8 4-5 10 11z" fill="#1E6B47"/></svg>')

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
  --wf-green: #1E6B47; --wf-green-dark: #155235; --wf-tint: #EBF5EF; --wf-tint-border: #CFE5D8;
  --wf-bg: #F5F8F6; --wf-line: #DFE7E2; --wf-line-soft: #EEF2F0; --wf-ink: #14221A; --wf-muted: #5E6E65;
  --wf-field: #D5DED9; --wf-amber-bg: #FDF1DC; --wf-amber-ink: #7A4107; --wf-red: #A3291C;
}

/* Not applied to spans: Streamlit's Material icons are spans with their own icon font. */
html, body, .stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp button, .stApp input, .stApp textarea, .stApp select, .stApp [data-baseweb="tab"] {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
}
[data-testid="stIconMaterial"], [data-testid="stIconMaterial"] * { font-family: 'Material Symbols Rounded' !important; }
.stApp { background: var(--wf-bg); color: var(--wf-ink); }
[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1280px; padding-top: 1.2rem; padding-bottom: 4rem; }

/* ---- headings ---- */
h1, h2, h3, h4 { letter-spacing: -0.4px; color: var(--wf-ink); font-weight: 800; }
h1 { font-size: 1.75rem !important; }
h2, [data-testid="stHeading"] h2 { font-size: 1.35rem !important; }
h3 { font-size: 1.05rem !important; }
h4 { font-size: 1rem !important; }
a { color: var(--wf-green); }
a:hover { color: var(--wf-green-dark); }

/* ---- navigation tabs: step bar on laptop, bottom bar on phone ---- */
[data-baseweb="tab-list"] { gap: 6px; padding: 6px; background: #fff; border: 1px solid var(--wf-line);
  border-radius: 14px; overflow-x: auto; }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none !important; }
button[data-baseweb="tab"] { height: 44px; padding: 0 16px; border-radius: 10px; color: #3F4F46; font-weight: 600;
  background: transparent; white-space: nowrap; }
button[data-baseweb="tab"]:hover { background: var(--wf-bg); color: var(--wf-ink); }
button[data-baseweb="tab"][aria-selected="true"] { background: var(--wf-green); color: #fff; }
button[data-baseweb="tab"][aria-selected="true"] p { color: #fff; font-weight: 700; }
button[data-baseweb="tab"] p { font-size: 14px; }
[data-baseweb="tab-panel"] { padding-top: 1.1rem; }

/* ---- cards: every bordered container ---- */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) {
  background: #fff; border-color: var(--wf-line) !important; border-radius: 16px !important; }
[data-testid="stExpander"] { background: #fff; border: 1px solid var(--wf-line); border-radius: 12px; }
[data-testid="stExpander"] summary { font-weight: 600; }
[data-testid="stAlert"] { border-radius: 12px; }

/* ---- metrics ---- */
[data-testid="stMetric"] { background: #fff; border: 1px solid var(--wf-line); border-radius: 14px; padding: 14px 16px; }
[data-testid="stMetricLabel"] p { font-size: 11px; font-weight: 700; letter-spacing: .6px; text-transform: uppercase;
  color: var(--wf-muted); }
[data-testid="stMetricValue"] { font-weight: 800; font-size: 1.35rem; }

/* ---- form fields: 44px, 10px radius ---- */
[data-testid="stWidgetLabel"] p { font-size: 13px; font-weight: 600; color: var(--wf-ink); }
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {
  border-radius: 10px !important; border-color: var(--wf-field) !important; background: #fff !important; }
[data-baseweb="input"], [data-baseweb="select"] > div { min-height: 44px; }
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within { border-color: var(--wf-green) !important; }
[data-testid="stSlider"] [role="slider"] { background: var(--wf-green); }
[data-testid="stCaptionContainer"], .stCaption { color: var(--wf-muted); }

/* ---- buttons ---- */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
  min-height: 44px; border-radius: 10px; font-weight: 600; font-size: 14px; border: 1px solid var(--wf-green);
  background: #fff; color: var(--wf-green); }
.stButton > button:hover, .stDownloadButton > button:hover { background: var(--wf-tint); border-color: var(--wf-green-dark);
  color: var(--wf-green-dark); }
.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"] { background: var(--wf-green) !important;
  color: #fff !important; border-color: var(--wf-green) !important; }
.stButton > button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover { background: var(--wf-green-dark) !important; }
.stButton > button:disabled { opacity: .45; }

/* ---- segmented controls (radio horizontal, pills) ---- */
[data-testid="stRadio"] [role="radiogroup"][aria-orientation="horizontal"], [data-testid="stRadio"] > div[role="radiogroup"] { gap: 6px; }
[data-testid="stPills"] button, [data-testid="stSegmentedControl"] button { border-radius: 10px; min-height: 40px; font-weight: 600; }

/* ---- sidebar as a white side panel ---- */
[data-testid="stSidebar"] { background: #fff; border-right: 1px solid var(--wf-line); }
[data-testid="stSidebar"] h1 { font-size: 1.3rem !important; color: var(--wf-green-dark); }
[data-testid="stSidebar"] h3 { font-size: .8rem !important; letter-spacing: 1px; text-transform: uppercase; color: var(--wf-muted); }

/* interest sliders: reserve two label lines so every slider in the row lines up */
[class*="st-key-tr_"][class*="interests"] [data-testid="stWidgetLabel"] { min-height: 2.8em; align-items: flex-start; }
[data-testid="stCaptionContainer"] { opacity: 1; }
[data-testid="stCaptionContainer"] p { margin-bottom: .6rem; line-height: 1.45; }

/* ---- reusable blocks ---- */
.wf-card { background: #fff; border: 1px solid var(--wf-line); border-radius: 16px; padding: 20px 22px; }
.wf-title-block h1 { margin: 0 0 4px; }
.wf-sub { color: var(--wf-muted); font-size: 14px; margin: 0 0 12px; }
.wf-chip { display: inline-block; font-size: 12px; font-weight: 600; padding: 5px 10px; border-radius: 8px;
  background: var(--wf-tint); color: var(--wf-green-dark); margin: 0 6px 6px 0; }
.wf-chip.warn { background: var(--wf-amber-bg); color: var(--wf-amber-ink); }
.wf-opt-head { padding: 18px 20px; border-radius: 14px 14px 0 0; }
.wf-opt-letter { font-size: 12px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; }
.wf-opt-name { font-size: 21px; font-weight: 800; margin: 4px 0 0; }
.wf-badge { font-size: 11px; font-weight: 800; color: #fff; background: var(--wf-green-dark); padding: 4px 9px;
  border-radius: 6px; float: right; }
.wf-stat-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; padding: 14px 4px; }
.wf-stat-k { font-size: 11px; font-weight: 700; color: var(--wf-muted); text-transform: uppercase; letter-spacing: .6px; }
.wf-stat-v { font-size: 18px; font-weight: 800; margin-top: 2px; }
.wf-bar { height: 8px; border-radius: 4px; background: var(--wf-line-soft); overflow: hidden; flex: 1; }
.wf-bar > span { display: block; height: 8px; border-radius: 4px; background: var(--wf-green); }
.wf-row { display: flex; align-items: center; gap: 10px; font-size: 13px; margin: 6px 0; }
.wf-row .n { width: 72px; flex-shrink: 0; }
.wf-row .v { width: 34px; text-align: right; font-weight: 700; font-size: 12px; }
.wf-share { display: flex; height: 16px; border-radius: 8px; overflow: hidden; gap: 2px; margin: 8px 0 10px; }
.wf-consent { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 10px 0 14px; }
.wf-consent > div { padding: 16px; border-radius: 14px; font-size: 13px; line-height: 1.75; }
.wf-consent .sent { background: #F3FAF6; border: 1px solid var(--wf-tint-border); color: #2F4A3B; }
.wf-consent .never { background: #FBF1EF; border: 1px solid #EFCFCA; color: #5B2C25; }
.wf-consent b { display: block; font-weight: 800; margin-bottom: 6px; }

/* ---- app header (keyed container) ---- */
.st-key-wf_header { background: #fff; border: 1px solid var(--wf-line); border-radius: 16px; padding: 10px 22px; margin-bottom: 14px; }
.wf-brand { display: flex; align-items: center; gap: 14px; min-width: 0; }
.wf-name { font-size: 24px; font-weight: 800; color: var(--wf-green-dark); letter-spacing: -0.5px; }
.wf-tag { font-size: 14px; color: var(--wf-muted); padding-left: 14px; border-left: 1px solid var(--wf-line); }
.wf-pill { display: inline-flex; align-items: center; height: 36px; padding: 0 14px; border-radius: 18px;
  background: var(--wf-tint); color: var(--wf-green-dark); font-size: 13px; font-weight: 600; white-space: nowrap; }

/* ---- left nav: radio group drawn as nav links ---- */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] { flex-direction: column; gap: 4px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label, .st-key-stepbar [data-testid="stRadio"] label {
  border-radius: 10px; cursor: pointer; margin: 0; align-items: center; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { height: 44px; padding: 0 14px; width: 100%; }
[data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child,
.st-key-stepbar [data-testid="stRadio"] label > div:first-child { display: none; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background: var(--wf-bg); }
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) { background: var(--wf-tint); }
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p { color: var(--wf-green-dark); font-weight: 700; }
[data-testid="stSidebar"] [data-testid="stRadio"] label p { font-size: 14px; font-weight: 500; color: #3F4F46; }

/* ---- step bar ---- */
.st-key-stepbar { background: #fff; border: 1px solid var(--wf-line); border-radius: 14px; padding: 6px; }
.st-key-stepbar [role="radiogroup"] { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; width: 100%; }
.st-key-stepbar [data-testid="stRadio"] label { height: 52px; padding: 0 14px; justify-content: center; width: 100%; }
.st-key-stepbar [data-testid="stRadio"] label:hover { background: var(--wf-bg); }
.st-key-stepbar [data-testid="stRadio"] label:has(input:checked) { background: var(--wf-green); }
.st-key-stepbar [data-testid="stRadio"] label:has(input:checked) p { color: #fff; font-weight: 700; }
.st-key-stepbar [data-testid="stRadio"] label p { font-size: 14px; font-weight: 600; text-align: center; }

/* ---- trip form pieces ---- */
.wf-eyebrow { font-size: 12px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: var(--wf-muted); margin: 2px 0 6px; }
.wf-loaded { font-size: 12px; font-weight: 600; color: var(--wf-green-dark); background: var(--wf-tint); padding: 6px 10px;
  border-radius: 8px; display: inline-block; }
.wf-wx-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.wf-wx { padding: 14px 16px; border-radius: 12px; background: var(--wf-bg); border: 1px solid #E6ECE8; display: flex;
  flex-direction: column; gap: 8px; font-size: 13px; color: #3F4F46; }
.wf-wx .top { display: flex; justify-content: space-between; }
.wf-wx .top span { font-size: 12px; color: var(--wf-muted); }
.wf-wx .temp { font-size: 14px; color: var(--wf-muted); }
.wf-wx .temp b { font-size: 24px; color: var(--wf-ink); }
.wf-wx .pop { display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 700; color: #24497F; }
.wf-wx .pop .wf-bar { background: #DCE6F2; height: 6px; }
.wf-wx .pop .wf-bar > span { background: #2D5BA8; height: 6px; }
.wf-note { padding: 20px; border-radius: 16px; background: var(--wf-tint); border: 1px solid var(--wf-tint-border); }
.wf-note h4 { margin: 0 0 8px; color: var(--wf-green-dark); font-size: 15px !important; }
.wf-note p { margin: 0; font-size: 13px; color: #2F4A3B; line-height: 1.55; }

/* transport options as selectable cards */
.st-key-transport [data-testid="stCheckbox"] { border: 1px solid var(--wf-field); border-radius: 12px; height: 52px;
  padding: 0 16px; display: flex; align-items: center; background: #fff; }
.st-key-transport [data-testid="stCheckbox"]:has(input:checked) { border: 1.5px solid var(--wf-green); background: var(--wf-tint); }
.st-key-transport [data-testid="stCheckbox"] p { font-weight: 600; }

/* ---- phone ---- */
@media (max-width: 640px) {
  .block-container { padding: .6rem 16px 4rem; }
  .wf-tag { display: none; }
  .st-key-wf_header { padding: 10px 14px; }
  .wf-name { font-size: 20px; }
  .st-key-stepbar [role="radiogroup"] { grid-template-columns: 1fr; }
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: .75rem; }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: calc(50% - .5rem); flex: 1 1 calc(50% - .5rem); }
  .wf-consent { grid-template-columns: 1fr; }
}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def brand_html(app_name: str, tagline: str) -> str:
    return f'<div class="wf-brand">{LOGO}<span class="wf-name">{app_name}</span><span class="wf-tag">{tagline}</span></div>'


def pill_html(summary: str) -> str:
    return f'<span class="wf-pill">{summary}</span>' if summary else ""


def eyebrow(text: str) -> None:
    st.markdown(f'<div class="wf-eyebrow">{text}</div>', unsafe_allow_html=True)


def page_title(title: str, sub: str = "") -> None:
    sub = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", sub)
    st.markdown(f'<div class="wf-title-block"><h1>{title}</h1><p class="wf-sub">{sub}</p></div>', unsafe_allow_html=True)


def bar_row(name: str, value: float, color: str = "#1E6B47") -> str:
    v = max(0, min(100, round(value)))
    return (f'<div class="wf-row"><span class="n">{name}</span><div class="wf-bar"><span style="width:{v}%;background:{color}">'
            f'</span></div><span class="v">{v}</span></div>')


CONSENT_HTML = """
<div class="wf-consent">
<div class="sent"><b>Sent</b>City, dates, day hours, budget<br>Interest scores as Traveller A, B, C…<br>
Group-level dietary &amp; access needs<br>Must-visit place names</div>
<div class="never"><b>Never sent</b>Names and emails<br>Booking references, account IDs<br>
Exact hotel address<br>Links you pasted</div>
</div>
"""
