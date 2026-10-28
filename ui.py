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
.block-container, [data-testid="stMainBlockContainer"] { max-width: 1480px; padding: 1.5rem 2.5rem 4rem !important; }
[data-testid="stSidebar"] { width: 248px !important; min-width: 248px !important; }
[data-testid="stSidebarContent"] { padding: 0 6px; }

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

/* ---- cards: containers made with ui.card() ---- */
[class*="st-key-wfcard_"] { background: #fff; border: 1px solid var(--wf-line) !important; border-radius: 16px !important;
  padding: 22px 24px 30px !important; gap: 1rem; }
.stApp hr { margin: .75rem 0 !important; border-color: var(--wf-line-soft) !important; }
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
[data-baseweb="select"] div, [data-baseweb="input"] input, [data-baseweb="textarea"] textarea { font-size: 15px; }
[data-testid="stWidgetLabel"] { margin-bottom: 2px; }
[data-baseweb="select"] > div * { font-size: 15px !important; }
[data-testid="stNumberInputContainer"] { border: 1px solid var(--wf-field); border-radius: 10px; background: #fff; overflow: hidden; }
[data-testid="stNumberInputContainer"] [data-baseweb="input"] { border: 0 !important; }
[data-testid="stNumberInputContainer"]:focus-within { border-color: var(--wf-green); }
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
/* one-line labels: buttons share widths via equal columns, so wrapping only made them uneven */
.stButton > button p, .stDownloadButton > button p { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.stButton > button[kind="tertiary"], [data-testid="stBaseButton-tertiary"] { border: 0 !important; background: transparent !important;
  min-height: auto; padding: 4px 0; color: var(--wf-green) !important; font-weight: 700; }

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

/* traveller card header */
.wf-person { display: flex; align-items: center; gap: 12px; min-width: 0; }
.wf-av { width: 40px; height: 40px; border-radius: 20px; color: #fff; font-weight: 800; font-size: 16px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; }
.wf-person-name { font-size: 17px; font-weight: 800; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.wf-alias { font-size: 11px; font-weight: 700; color: #3F4F46; background: #F0F3F1; border-radius: 6px; padding: 4px 8px;
  white-space: nowrap; }
/* settings card captions sit tight under their toggle */
[class*="st-key-wfcard_"] [data-testid="stCaptionContainer"] p { font-size: 12.5px; }

/* ---- reusable blocks ---- */
.wf-card { background: #fff; border: 1px solid var(--wf-line); border-radius: 16px; padding: 20px 22px; }
.wf-title-block h1 { margin: 0 0 4px; }
.wf-title-block.solo h1 { margin: 0; padding: 0 !important; }
[data-testid="stMarkdown"]:has(.wf-title-block.solo), [data-testid="stMarkdownContainer"]:has(.wf-title-block.solo) {
  margin-bottom: 0 !important; }
/* phone-only pieces: the bottom tab bar, and the traveller buttons under the share bar */
.st-key-bottomnav, .st-key-share_btns { display: none !important; }
/* "Settings" is the phone tab bar's page; laptops don't list it */
[data-testid="stSidebar"] [role="radiogroup"] > label:last-child { display: none; }
.wf-tag-fixed .ph { display: none; }
.wf-loaded-wrap { text-align: right; }
/* the fold arrow on traveller cards is a phone-only control */
[class*="st-key-tr_"][class*="_tog"] { display: none; }
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
.wf-legend { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px 24px; }
.wf-legend > div { display: flex; align-items: center; gap: 10px; font-size: 14px; }
.wf-legend .sw { width: 12px; height: 12px; border-radius: 3px; flex-shrink: 0; }
.wf-legend .nm { font-weight: 600; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.wf-legend b { margin-left: auto; font-weight: 800; }
.wf-consent { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 10px 0 14px; }
.wf-consent > div { padding: 16px; border-radius: 14px; font-size: 13px; line-height: 1.75; }
.wf-consent .sent { background: #F3FAF6; border: 1px solid var(--wf-tint-border); color: #2F4A3B; }
.wf-consent .never { background: #FBF1EF; border: 1px solid #EFCFCA; color: #5B2C25; }
.wf-consent b { display: block; font-weight: 800; margin-bottom: 6px; }

/* ---- app header (keyed container) ---- */
.wf-brand { display: flex; align-items: center; gap: 14px; min-width: 0; }
.wf-name { font-size: 24px; font-weight: 800; color: var(--wf-green-dark); letter-spacing: -0.5px; }
.wf-tag { font-size: 14px; color: var(--wf-muted); padding-left: 14px; border-left: 1px solid var(--wf-line); }
.wf-pill { display: inline-flex; align-items: center; height: 36px; padding: 0 14px; border-radius: 18px;
  background: var(--wf-tint); color: var(--wf-green-dark); font-size: 13px; font-weight: 600; white-space: nowrap; }

/* top bar: pinned across the whole window, above the sidebar and the page */
:root { --wf-bar: 80px; }
.st-key-wf_header { position: fixed; top: 0; left: 0; right: 0; z-index: 999995; height: var(--wf-bar); margin: 0;
  background: #fff; border-bottom: 1px solid var(--wf-line); padding: 0 28px; justify-content: center; }
/* every item on one centred row: no markdown margins, columns centre their single child */
.st-key-wf_header [data-testid="stHorizontalBlock"] { flex-wrap: nowrap; align-items: center; }
.st-key-wf_header [data-testid="stColumn"] > [data-testid="stVerticalBlock"] { justify-content: center; gap: 0; }
.st-key-wf_header [data-testid="stMarkdownContainer"], .st-key-wf_header [data-testid="stMarkdown"],
.st-key-wf_header [data-testid="stElementContainer"] { margin: 0 !important; }
.st-key-wf_header [data-testid="stMarkdownContainer"] > div { margin: 0; }
.st-key-wf_header .wf-pill-wrap { display: flex; justify-content: flex-end; }
.st-key-wf_header .stButton > button { min-height: 42px; border-color: var(--wf-line); color: var(--wf-ink); font-weight: 700; }
[data-testid="stSidebar"] { padding-top: var(--wf-bar); }
.block-container, [data-testid="stMainBlockContainer"] { padding-top: calc(var(--wf-bar) + 1.75rem) !important; }
/* Streamlit's own bar sits under ours; keep its sidebar-expand arrow (phones need it), drop the menu */
[data-testid="stHeader"] { top: var(--wf-bar); background: transparent; pointer-events: none; }
[data-testid="stHeader"] button { pointer-events: auto; }
[data-testid="stMainMenu"], [data-testid="stToolbarActions"] { display: none; }
/* style-only markdown blocks take no space */
[data-testid="stElementContainer"]:has(style.wf-style), .stElementContainer:has(style.wf-style) { display: none; }

/* ---- left nav: radio group drawn as nav links ---- */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] { flex-direction: column; gap: 4px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label, .st-key-stepbar [data-testid="stRadio"] label {
  border-radius: 10px; cursor: pointer; margin: 0; align-items: center; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { height: 46px; padding: 0 14px; width: 100% !important; max-width: none; }
[data-testid="stSidebar"] [data-testid="stRadio"], [data-testid="stSidebar"] [data-testid="stRadio"] > div,
[data-testid="stSidebar"] [role="radiogroup"] { width: 100% !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label [data-testid="stMarkdownContainer"] p { display: flex; align-items: center; gap: 10px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label [data-testid="stIconMaterial"] { font-size: 20px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child,
.st-key-stepbar [data-testid="stRadio"] label > div:first-child { display: none; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background: var(--wf-bg); }
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) { background: var(--wf-tint); }
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p { color: var(--wf-green-dark); font-weight: 700; }
[data-testid="stSidebar"] [data-testid="stRadio"] label p { font-size: 15px; font-weight: 500; color: #3F4F46; }
[data-testid="stSidebarUserContent"] { padding-top: .25rem; }
[data-testid="stSidebarHeader"] { height: auto; padding-top: .5rem; padding-bottom: 0; }

/* ---- step bar ---- */
.st-key-stepbar { background: #fff; border: 1px solid var(--wf-line); border-radius: 14px; padding: 6px; }
.st-key-stepbar [role="radiogroup"] { display: flex !important; flex-wrap: nowrap; gap: 6px; width: 100%; }
.st-key-stepbar [role="radiogroup"] > label { flex: 1 1 0 !important; min-width: 0; }
.st-key-stepbar [data-testid="stRadio"], .st-key-stepbar [data-testid="stRadio"] > div { width: 100% !important; }
.st-key-stepbar [data-testid="stRadio"] label { height: 60px; padding: 0 16px; justify-content: flex-start; gap: 12px;
  width: 100% !important; max-width: none !important; }
.st-key-stepbar [data-testid="stRadio"] label:hover { background: var(--wf-bg); }
.st-key-stepbar [data-testid="stRadio"] label:has(input:checked) { background: var(--wf-green); }
.st-key-stepbar [data-testid="stRadio"] label p { font-size: 15px; font-weight: 700; text-align: left; line-height: 1.25; color: var(--wf-ink); }
.st-key-stepbar [data-testid="stRadio"] label p::after { display: block; font-size: 12.5px; font-weight: 500; color: var(--wf-muted);
  margin-top: 2px; }
.st-key-stepbar [data-testid="stRadio"] label::before { width: 28px; height: 28px; border-radius: 14px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 800;
  background: var(--wf-tint); color: var(--wf-green-dark); }
.st-key-stepbar [data-testid="stRadio"] label:has(input:checked) p { color: #fff; }
.st-key-stepbar [data-testid="stRadio"] label:has(input:checked) p::after { color: rgba(255, 255, 255, .85); }
.st-key-stepbar [data-testid="stRadio"] label:has(input:checked)::before { background: #fff; color: var(--wf-green); }

/* ---- must-visits ---- */
.wf-box-title { display: flex; align-items: center; gap: 10px; font-size: 17px; font-weight: 800; margin: 0; }
.wf-hint { font-size: 12.5px; color: var(--wf-muted); line-height: 1.45; margin-top: -12px; }
.wf-hint b { color: var(--wf-ink); }
[class*="st-key-fixedbox"] { background: var(--wf-bg); border-radius: 12px; padding: 14px; margin-top: 8px; }
[class*="st-key-fixedbox"] [data-baseweb="input"], [class*="st-key-fixedbox"] [data-baseweb="select"] > div { background: #fff !important; }
.wf-src { display: flex; gap: 6px; margin: 4px 0 8px; }
.wf-src span { font-size: 12px; font-weight: 600; padding: 5px 10px; border-radius: 7px; background: #F0F3F1; color: #3F4F46; }
.wf-src span.on { background: var(--wf-green); color: #fff; font-weight: 700; }
.wf-found { display: flex; gap: 12px; align-items: flex-start; padding: 14px; border-radius: 12px; border: 1px dashed #9CCFB1;
  background: #F3FAF6; font-size: 13px; color: #3F4F46; line-height: 1.5; }
.wf-found .ok { width: 32px; height: 32px; border-radius: 16px; background: var(--wf-green); color: #fff; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-weight: 800; }
.wf-found b { display: block; font-size: 14px; color: var(--wf-ink); }
.wf-list-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.wf-list-head .ttl { font-size: 17px; font-weight: 800; color: var(--wf-ink); }
.wf-list-head .ttl span { color: var(--wf-muted); font-weight: 600; }
.wf-list-head small { font-size: 12.5px; color: var(--wf-muted); }
[class*="st-key-mrow_"] { border-top: 1px solid var(--wf-line-soft); padding-top: 14px; }
[class*="st-key-mrow_"] .stButton > button { border-color: #E4B4AE; color: #A3291C; }
[class*="st-key-mrow_"] .stButton > button:hover { background: #FBF1EF; border-color: #A3291C; color: #A3291C; }
.wf-mrow { display: flex; align-items: center; gap: 14px; min-width: 0; }
.wf-mrow .ico { width: 40px; height: 40px; border-radius: 10px; background: var(--wf-tint); flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; }
.wf-mrow .txt { flex: 1; min-width: 0; }
.wf-mrow .tags { display: flex; align-items: center; gap: 14px; }
.wf-mrow .txt b { display: block; font-size: 15px; }
.wf-mrow .txt small { display: block; font-size: 12.5px; color: var(--wf-muted); margin-top: 2px; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap; }
.wf-tag-src { font-size: 12px; font-weight: 600; color: #3F4F46; background: #F0F3F1; padding: 5px 10px; border-radius: 7px; white-space: nowrap; }
.wf-tag-fixed { font-size: 12px; font-weight: 700; color: #fff; background: var(--wf-green-dark); padding: 5px 10px; border-radius: 7px; white-space: nowrap; }
.wf-tag-any { font-size: 12px; font-weight: 700; color: var(--wf-green-dark); background: var(--wf-tint); border: 1px solid var(--wf-tint-border);
  padding: 4px 10px; border-radius: 7px; white-space: nowrap; }

/* ---- privacy page ---- */
.st-key-wf_hero { background: var(--wf-green-dark); border-radius: 18px; padding: 28px 30px 36px; }
/* icon and title share a centred first row; the description sits under the title */
.wf-hero { display: grid; grid-template-columns: 48px 1fr; column-gap: 16px; align-items: center; }
.wf-hero p { grid-column: 2; }
.wf-hero .ico { width: 48px; height: 48px; border-radius: 14px; background: rgba(255, 255, 255, .14); flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; }
.wf-hero h2 { margin: 0; padding: 0 !important; color: #fff !important; font-size: 22px !important; }
.wf-hero p { margin: 8px 0 0; color: #CFE5D8; font-size: 14px; line-height: 1.55; }
.st-key-wf_hero .stButton > button { background: #fff; border: 0; color: #A3291C; font-weight: 700; }
.st-key-wf_hero .stButton > button:hover { background: #FBF1EF; color: #A3291C; }
[class*="st-key-wfcard_"] [data-testid="stJson"] { background: #F7F9F8; border: 1px solid var(--wf-line); border-radius: 12px;
  padding: 10px; max-height: 420px; overflow: auto; }
.st-key-wf_sent [data-testid="stJson"] { background: #F3FAF6; border-color: var(--wf-tint-border); }
.wf-checks { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.wf-checks li { display: flex; gap: 10px; align-items: flex-start; font-size: 13.5px; color: #3F4F46; line-height: 1.45; }
.wf-checks li::before { content: "✓"; width: 20px; height: 20px; border-radius: 10px; background: var(--wf-green); color: #fff;
  font-size: 11px; font-weight: 800; flex-shrink: 0; display: flex; align-items: center; justify-content: center; margin-top: 1px; }
.wf-alias-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px 18px; font-size: 13.5px; }
.wf-alias-grid div { display: flex; justify-content: space-between; gap: 8px; padding: 8px 10px; border-radius: 8px; background: var(--wf-bg); }
.wf-alias-grid b { color: var(--wf-green-dark); }
[class*="st-key-wfcard_"] table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
[class*="st-key-wfcard_"] th { text-align: left; font-size: 11px; font-weight: 700; letter-spacing: .6px; text-transform: uppercase;
  color: var(--wf-muted); background: transparent; border: 0; border-bottom: 1px solid var(--wf-line); padding: 8px 10px; }
[class*="st-key-wfcard_"] td { border: 0; border-bottom: 1px solid var(--wf-line-soft); padding: 11px 10px; vertical-align: top; }
[class*="st-key-wfcard_"] tr:last-child td { border-bottom: 0; }

/* ---- trip form pieces ---- */
.wf-eyebrow { font-size: 12px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: var(--wf-muted); margin: 2px 0 6px; }
.wf-loaded { font-size: 12px; font-weight: 600; color: var(--wf-green-dark); background: var(--wf-tint); padding: 6px 10px;
  border-radius: 8px; display: inline-block; }
.wf-wx-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 14px; }
.wf-wx { padding: 14px 16px; border-radius: 12px; background: var(--wf-bg); border: 1px solid #E6ECE8; display: flex;
  flex-direction: column; gap: 8px; font-size: 13px; color: #3F4F46; }
.wf-wx .top { display: flex; justify-content: space-between; }
.wf-wx .top span { font-size: 12px; color: var(--wf-muted); }
.wf-wx .temp { font-size: 14px; color: var(--wf-muted); }
.wf-wx .temp b { font-size: 24px; color: var(--wf-ink); }
.wf-wx .pop { display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 700; color: #24497F; }
.wf-wx .pop .wf-bar { background: #DCE6F2; height: 6px; }
.wf-wx .pop .wf-bar > span { background: #2D5BA8; height: 6px; }
[class*="wf_note"] { padding: 20px 22px; border-radius: 16px; background: var(--wf-tint); border: 1px solid var(--wf-tint-border); gap: .5rem; }
[class*="wf_note"] h4 { margin: 0; color: var(--wf-green-dark); font-size: 15px !important; }
[class*="wf_note"] p { margin: 0; font-size: 13px; color: #2F4A3B; line-height: 1.55; }
[class*="wf_note"] .stButton > button { justify-content: flex-start; }
/* Streamlit pulls text blocks up 1rem at the bottom; undo it here so the link sits clear of the paragraph */
[class*="wf_note"] [data-testid="stMarkdown"]:has(.wf-note-txt), [class*="wf_note"] [data-testid="stMarkdownContainer"]:has(.wf-note-txt) {
  margin-bottom: 0 !important; }
[class*="wf_note"] [data-testid="stElementContainer"]:has(.stButton) { margin-top: 4px; }
[class*="wf_note"] .stButton p { color: var(--wf-green); font-weight: 700; font-size: 13px; }

/* transport options as selectable cards */
.st-key-transport [data-testid="stCheckbox"] { width: 100%; border: 1px solid var(--wf-field); border-radius: 12px; height: 52px;
  padding: 0 16px; display: flex; align-items: center; background: #fff; }
.st-key-transport [data-testid="stCheckbox"]:has(input:checked) { border: 1.5px solid var(--wf-green); background: var(--wf-tint); }
.st-key-transport [data-testid="stCheckbox"] p { font-weight: 600; }

/* ---- laptop only ---- */
@media (min-width: 641px) {
  /* privacy page: the left card stretches to the combined height of the two cards beside it */
  .st-key-priv_row [data-testid="stHorizontalBlock"] { align-items: stretch; }
  .st-key-priv_row [data-testid="stColumn"]:first-child [data-testid="stVerticalBlock"],
  .st-key-priv_row [data-testid="stColumn"]:first-child [data-testid="stLayoutWrapper"] { height: 100%; }
  .st-key-trav_btns { flex-wrap: nowrap !important; }
}

/* ---- phone ---- */
@media (max-width: 640px) {
  .block-container { padding: .6rem 16px 4rem; }
  .wf-tag, .st-key-wf_header .wf-pill { display: none; }
  .st-key-wf_header { padding: 0 14px; }
  /* Streamlit stacks columns on phones by itself; only the top bar keeps its row */
  .st-key-wf_header [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 1 1 auto !important; }
  .st-key-wf_header [data-testid="stColumn"]:nth-child(2) { display: none; }
  .wf-name { font-size: 20px; }
  .wf-alias-grid { grid-template-columns: 1fr; }
  .st-key-stepbar [role="radiogroup"] { flex-direction: column; }
  .st-key-stepbar [data-testid="stRadio"] label { height: auto; min-height: 60px; padding: 12px 16px; }
  .wf-consent { grid-template-columns: 1fr; }

  /* no sidebar on phones: navigation is the bottom tab bar, and the right-hand panels live on its Settings page */
  [data-testid="stSidebar"], [data-testid="stExpandSidebarButton"], [data-testid="stColumn"]:has(.st-key-aside),
  .st-key-trav_btns { display: none !important; }
  .st-key-share_btns { display: flex !important; margin-top: 6px; }
  /* step footer: the empty middle column only spaces the buttons apart on laptops */
  .st-key-stepfoot [data-testid="stColumn"]:nth-child(2) { display: none; }
  .st-key-stepfoot [data-testid="stHorizontalBlock"] { gap: 10px !important; }
  .st-key-share_btns [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: 10px !important; }
  .st-key-share_btns [data-testid="stColumn"] { min-width: 0 !important; flex: 1 1 0 !important; width: auto !important; }
  .block-container, [data-testid="stMainBlockContainer"] { padding-bottom: 104px !important; }
  .st-key-bottomnav { display: grid !important; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 0 !important;
    position: fixed; left: 0; right: 0; bottom: 0; z-index: 999980; height: 68px; padding: 6px 4px;
    background: #fff; border-top: 1px solid var(--wf-line); box-shadow: 0 -4px 16px rgba(20, 34, 26, .06); }
  .st-key-bottomnav [data-testid="stElementContainer"] { width: auto !important; }
  /* icon above label: they sit in a span two levels inside the button */
  .st-key-bottomnav .stButton > button > div > span { flex-direction: column; align-items: center; gap: 2px; }
  .st-key-bottomnav .stButton > button { width: 100%; height: 56px; padding: 0 !important; color: var(--wf-muted) !important; }
  .st-key-bottomnav .stButton > button p { font-size: 12px; font-weight: 600; color: var(--wf-muted); }
  .st-key-bottomnav [data-testid="stIconMaterial"] { font-size: 24px; margin: 0 !important; }

  /* privacy hero: room between the text and the button */
  .st-key-wf_hero [data-testid="stElementContainer"]:has(.stButton) { margin-top: 20px; }
  /* buttons that follow a hint or a name row get a little air */
  [data-testid="stElementContainer"]:has(.wf-hint) + [data-testid="stElementContainer"]:has(.stButton) { margin-top: 12px; }
  [class*="st-key-tr_"][class*="_rm"] { margin-top: 10px; }

  /* trip details: compact, fields paired two-up like the phone mockup */
  [class*="st-key-wfcard_"] { padding: 18px 16px 24px !important; }
  [class*="st-key-wfcard_"] h2 { font-size: 22px !important; }
  [data-baseweb="input"], [data-baseweb="select"] > div { min-height: 40px; }
  [data-baseweb="select"] > div *, [data-baseweb="input"] input { font-size: 14px !important; }
  [data-testid="stWidgetLabel"] p { font-size: 12.5px; }
  .wf-loaded-wrap { text-align: left; }
  [class*="st-key-trow_"] [data-testid="stHorizontalBlock"], .st-key-transport [data-testid="stHorizontalBlock"] {
    flex-direction: row !important; flex-wrap: wrap !important; gap: .75rem !important; }
  [class*="st-key-trow_"] [data-testid="stColumn"], .st-key-transport [data-testid="stColumn"] {
    min-width: calc(50% - .375rem) !important; max-width: calc(50% - .375rem) !important;
    flex: 1 1 calc(50% - .375rem) !important; width: auto !important; }
  .st-key-trow_head [data-testid="stColumn"], .st-key-trow_where [data-testid="stColumn"]:first-child,
  .st-key-trow_when [data-testid="stColumn"]:last-child, .st-key-trow_budget [data-testid="stColumn"]:last-child {
    min-width: 100% !important; max-width: 100% !important; flex-basis: 100% !important; }
  .st-key-transport [data-testid="stCheckbox"] { height: 46px; padding: 0 12px; }

  /* traveller cards fold away with the arrow */
  [class*="st-key-tr_"][class*="_tog"] { display: block; margin-left: auto; }
  [class*="st-key-tr_"][class*="_tog"] [data-testid="stIconMaterial"] { font-size: 26px; }
  /* traveller profiles: one column, so drop the equal-height labels and tighten the spacing */
  [class*="st-key-tr_"][class*="interests"] [data-testid="stWidgetLabel"] { min-height: 0; }
  [class*="st-key-tr_"][class*="_body"], [class*="st-key-tr_"][class*="interests"] { gap: .35rem; }
  [class*="st-key-tr_"][class*="_body"] [data-testid="stHorizontalBlock"] { gap: .35rem !important; }
  [class*="st-key-tr_"][class*="_body"] [data-testid="stColumn"] > [data-testid="stVerticalBlock"] { gap: .35rem; }

  /* must-visit rows: name and tags on the left, a small Remove on the right */
  [class*="st-key-mrow_"] [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important;
    gap: 12px !important; }
  [class*="st-key-mrow_"] [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; }
  [class*="st-key-mrow_"] [data-testid="stColumn"]:first-child { flex: 1 1 auto !important; }
  [class*="st-key-mrow_"] [data-testid="stColumn"]:last-child { flex: 0 0 92px !important; max-width: 92px; }
  [class*="st-key-mrow_"] .stButton > button { min-height: 38px; padding: 0 10px; }
  [class*="st-key-mrow_"] .stButton > button > div > span { gap: 0; }
  [class*="st-key-mrow_"] .stButton > button > div > span > span:has([data-testid="stIconMaterial"]) { display: none; }
  .wf-tag-fixed { white-space: normal; }
  [class*="st-key-mrow_"] .stButton [data-testid="stIconMaterial"] { display: none; }
  .wf-mrow .ico, .wf-mrow .txt small, .wf-list-head small { display: none; }
  .wf-mrow { flex-wrap: wrap; row-gap: 8px; }
  .wf-mrow .txt { flex-basis: 100%; }
  .wf-mrow .tags { flex-basis: 100%; flex-wrap: wrap; gap: 6px; }
  .wf-mrow .wf-tag-src { order: 2; }
  .wf-tag-fixed .ph { display: inline; }

  /* weather: one swipeable row */
  .wf-wx-grid { display: flex; overflow-x: auto; scroll-snap-type: x mandatory; padding-bottom: 8px; }
  .wf-wx { flex: 0 0 150px; scroll-snap-align: start; }
}
</style>
"""


def reset_cards() -> None:
    st.session_state["_wf_cards"] = 0


def card():
    """A white bordered card. Keys come from a per-run counter so CSS can target them."""
    n = st.session_state.get("_wf_cards", 0) + 1
    st.session_state["_wf_cards"] = n
    return st.container(border=True, key=f"wfcard_{n}")


def inject_css() -> None:
    st.markdown(CSS.replace("<style>", '<style class="wf-style">', 1), unsafe_allow_html=True)


def style(css: str) -> None:
    """Page-specific CSS; its block is hidden so it adds no gap. Keep `css` free of blank lines."""
    st.markdown(f'<style class="wf-style">{css}</style>', unsafe_allow_html=True)


CHECK_SVG = ("url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
             "stroke='white' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12l5 5 9-10'/%3E%3C/svg%3E\")")


def stepbar_css(subtitles: list[str], current: int) -> None:
    """Number or tick circle and a subtitle under each step label; radio labels can only hold one line of text."""
    rules = []
    for n, sub in enumerate(subtitles, 1):
        sel = f'.st-key-stepbar [role="radiogroup"] > label:nth-child({n})'
        sub = re.sub(r'[\\"<>\n]', "", sub)
        rules.append(f'{sel} p::after {{ content: "{sub}"; }}')
        if n - 1 < current:
            rules.append(f"{sel}::before {{ content: ''; background: var(--wf-green) {CHECK_SVG} center / 16px no-repeat; }}")
        else:
            rules.append(f'{sel}::before {{ content: "{n}"; }}')
    style(" ".join(rules))


def hint(text: str, where=st) -> None:
    """Helper text tucked right under the field above it."""
    where.markdown(f'<div class="wf-hint">{text}</div>', unsafe_allow_html=True)


def brand_html(app_name: str, tagline: str) -> str:
    return f'<div class="wf-brand">{LOGO}<span class="wf-name">{app_name}</span><span class="wf-tag">{tagline}</span></div>'


def pill_html(summary: str) -> str:
    return f'<div class="wf-pill-wrap"><span class="wf-pill">{summary}</span></div>' if summary else ""


def eyebrow(text: str) -> None:
    st.markdown(f'<div class="wf-eyebrow">{text}</div>', unsafe_allow_html=True)


def page_title(title: str, sub: str = "") -> None:
    sub_html = f'<p class="wf-sub">{_bold(sub)}</p>' if sub else ""
    solo = "" if sub else " solo"  # a title on its own drops its bottom margin so it centres beside buttons
    st.markdown(f'<div class="wf-title-block{solo}"><h1>{title}</h1>{sub_html}</div>', unsafe_allow_html=True)


def subtitle(sub: str) -> None:
    """The line under a title, for when the title shares its row with buttons."""
    st.markdown(f'<p class="wf-sub">{_bold(sub)}</p>', unsafe_allow_html=True)


def _bold(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


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
