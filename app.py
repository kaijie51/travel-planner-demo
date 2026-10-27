"""Streamlit front end for the AI group itinerary planner demo.

Run locally:  streamlit run app.py
"""

import copy
import html
import json
import uuid
from datetime import date, datetime, time, timedelta

import pandas as pd
import pydeck as pdk
import streamlit as st

import ai
import scoring
import ui
from ai import AIError
from config import (APP_NAME, CROWD_LABELS, INTEREST_LABELS, INTERESTS, MODEL, PACE_LABELS,
                    STRATEGIES, TAGLINE, TRANSPORT_ICONS, TRANSPORT_MODES)
from demo import DEMO_LINK, DEMO_SCRIPT, demo_state
from privacy import aliases, build_payload, clean_url, normalised_weights, scrub
from weather import forecast

st.set_page_config(page_title=f"{APP_NAME} · AI group trip planner", page_icon="🧭", layout="wide")

DAY_COLORS = [[30, 107, 71], [45, 91, 168], [180, 83, 42], [107, 79, 160], [214, 39, 40], [140, 86, 75], [23, 190, 207]]
TRAVELLER_COLORS = ["#1E6B47", "#2D5BA8", "#B4532A", "#6B4FA0", "#B8860B", "#0E7490", "#9D174D"]
OPTION_BANDS = [("#EBF5EF", "#155235"), ("#E8EFFA", "#1F3F78"), ("#FDF1DC", "#7A4107")]
KIND_ICON = {"activity": "📍", "meal": "🍽️", "rest": "☕"}
CROWD_BADGE = {"low": ":green-badge[👥 low crowd]", "moderate": ":orange-badge[👥 moderate crowd]", "high": ":red-badge[👥 busy]"}
CONF_BADGE = {"high": "", "medium": ":gray-badge[ℹ️ verify details]", "low": ":red-badge[⚠️ low-confidence info]"}
NAV = ["Plan trip", "Itineraries", "Explore", "Privacy & data"]
NAV_ICONS = {"Plan trip": "luggage", "Itineraries": "map", "Explore": "explore", "Privacy & data": "lock"}
STEPS = ["Trip details", "Travellers", "Must-visits"]
VERIFY_NOTE = ("Venue details (hours, prices, crowd levels, coordinates) come from Claude's general knowledge, "
               "not live data. Verify before booking.")


# ---------------------------------------------------------------- helpers

def uid() -> str:
    return uuid.uuid4().hex[:8]


def md(text: str) -> str:
    """Escape '$' so prices like S$10 aren't rendered as LaTeX."""
    return (text or "").replace("$", "\\$")


def to_time(s: str) -> time:
    h, m = (int(x) for x in s.split(":")[:2])
    return time(h, m)


def minutes_between(a: str, b: str) -> int:
    try:
        ta, tb = to_time(a), to_time(b)
        return max(15, (tb.hour * 60 + tb.minute) - (ta.hour * 60 + ta.minute))
    except ValueError:
        return 60


def fmt_date(iso: str) -> str:
    try:
        return date.fromisoformat(iso).strftime("%a %d %b")
    except ValueError:
        return iso


def trip_dates(t: dict) -> list[str]:
    return [(t["start_date"] + timedelta(days=i)).isoformat() for i in range(int(t["num_days"]))]


def money(x: float) -> str:
    return f"{st.session_state.trip['currency']} {x:,.0f}"


def blank_state() -> dict:
    return {
        "trip": {
            "destination": "", "start_date": date.today() + timedelta(days=7), "num_days": 3,
            "day_start": "09:00", "day_end": "21:00", "budget": 500, "currency": "SGD",
            "transport_modes": ["Walk", "Public transport"], "accommodation": "", "crowd_tolerance": 3,
            "dietary": "", "notes": "",
        },
        "travellers": [{"id": uid(), "name": "You", "weight": 1.0, "pace": 3, "dietary": "", "mobility": "",
                        "interests": {d: 3 for d in INTERESTS}}],
        "anchors": [],
    }


def reset_plan_state():
    ss = st.session_state
    ss.options, ss.confirmed, ss.pending_replan = [], None, None
    ss.swaps, ss.contrast, ss.extracted, ss.explore = {}, None, None, None
    ss.avoid = []
    ss.pop("sel_radio", None)


def init():
    ss = st.session_state
    if "ver" in ss:
        return
    ss.ver, ss.link_ver = 0, 0
    ss.link_url, ss.link_caption = "", ""
    ss.update(demo_state())  # Singapore sample is preloaded
    ss.call_log, ss.last_sent = [], None
    ss.consent_ai, ss.consent_personal = False, True
    ss.n_options, ss.effort = 3, "low"
    ss.nav, ss.step, ss.loaded, ss.show_script = NAV[0], STEPS[0], "Local Singapore demo", False
    reset_plan_state()


def load_demo():
    st.session_state.update(demo_state())
    st.session_state.ver += 1
    st.session_state.loaded = "Local Singapore demo"
    reset_plan_state()


def clear_all():
    st.session_state.update(blank_state())
    st.session_state.ver += 1
    st.session_state.loaded = "Blank trip"
    st.session_state.call_log, st.session_state.last_sent = [], None
    reset_plan_state()


def current_payload(extra_anchors: list[dict] | None = None, extra_notes: str = ""):
    ss = st.session_state
    trip = dict(ss.trip, dates=trip_dates(ss.trip))
    if extra_notes:
        trip["notes"] = (trip.get("notes", "") + "\n" + extra_notes).strip()
    return build_payload(trip, ss.travellers, ss.anchors + (extra_anchors or []), ss.consent_personal)


def log_call(purpose: str, meta: dict | None):
    if meta:
        st.session_state.call_log.append({"time": datetime.now().strftime("%H:%M:%S"), "purpose": purpose, **meta})


def ai_ready() -> bool:
    if not ai.get_api_key():
        st.error("No Claude API key configured. See README → *API key*.")
        return False
    if not st.session_state.consent_ai:
        with st.container(border=True):
            st.markdown("### Before we plan with AI")
            st.markdown("Wayfare will send a de-identified version of your trip to Anthropic's Claude API to build your "
                        "itineraries. Here is what that means.")
            st.markdown(ui.CONSENT_HTML, unsafe_allow_html=True)
            st.caption("Processed abroad by the AI provider. Used only to plan this trip: no model training, no marketing. "
                       "Nothing is stored on our servers; closing the tab deletes it.")
            st.button("Allow and generate", key="agree_btn", type="primary",
                      on_click=lambda: st.session_state.update(consent_ai=True))
        return False
    return True


def run_ai(purpose: str, fn, *args):
    try:
        with st.spinner(f"Asking Claude: {purpose.lower()}…"):
            result, meta = fn(*args)
    except AIError as e:
        st.error(str(e))
        return None
    log_call(purpose, meta)
    return result


def prepare_option(option: dict) -> dict:
    for day in option["days"]:
        for s in day["stops"]:
            s.setdefault("_uid", uid())
            s.setdefault("_mode_idx", 0)
    return option


def selected_entry():
    ss = st.session_state
    ok = [e for e in ss.options if e["option"]]
    if not ok:
        return None
    return ok[min(ss.get("sel_radio", 0), len(ok) - 1)]


# ---------------------------------------------------------------- navigation, header, right-hand panels

def go_nav(name: str):
    st.session_state.nav = name


def go_step(i: int):
    st.session_state.step = STEPS[i]


def keep_widget_state():
    """Widgets that only render on some pages would lose their value when hidden; re-assigning keeps it."""
    ss = st.session_state
    for k in ("consent_ai", "consent_personal", "n_options", "effort", "show_script", "step", "sel_radio"):
        if k in ss:
            ss[k] = ss[k]


def sidebar():
    with st.sidebar:
        st.radio("Main navigation", NAV, key="nav", label_visibility="collapsed",
                 format_func=lambda n: f":material/{NAV_ICONS[n]}: {n}")
        st.divider()
        st.toggle("Presenter script", key="show_script", help="Show or hide the demo talking points.")
        if st.session_state.show_script:
            st.markdown(DEMO_SCRIPT)


def header():
    ss = st.session_state
    t = ss.trip
    parts = [t["destination"] or "New trip"]
    if t["destination"]:
        end = t["start_date"] + timedelta(days=int(t["num_days"]) - 1)
        parts.append(f"{t['start_date'].day} {t['start_date']:%b}–{end.day} {end:%b}")
    n = len(ss.travellers)
    parts.append(f"{n} traveller{'s' if n != 1 else ''}")
    with st.container(key="wf_header"):
        c1, c2, c3 = st.columns([3.2, 2.2, 1.3], vertical_alignment="center")
        c1.markdown(ui.brand_html(APP_NAME, "Plan together. Explore further."), unsafe_allow_html=True)
        c2.markdown(ui.pill_html(" · ".join(parts)), unsafe_allow_html=True)
        c3.button("Privacy & data", icon=":material/verified_user:", on_click=go_nav, args=("Privacy & data",), width="stretch")


def quick_start():
    with st.container(border=True):
        st.markdown("#### Quick start")
        st.caption("Try a filled-in demo or start fresh.")
        st.button("Local Singapore demo", on_click=load_demo, type="primary", width="stretch")
        st.button("Blank trip", on_click=clear_all, width="stretch")


def planner_settings():
    with st.container(border=True):
        st.markdown("#### Planner settings")
        st.toggle("AI generation", key="consent_ai")
        st.caption("Allow trip details (de-identified) to be sent to Anthropic's Claude API.")
        st.toggle("Personalisation", key="consent_personal")
        st.caption("Send each traveller's interest profile (under an alias). Off = generic plan.")
        st.divider()
        st.slider("Itinerary options to generate", 1, 3, key="n_options",
                  help="Each option is one parallel Claude call with a different planning strategy.")
        st.select_slider("Reasoning effort", ["low", "medium", "high"], key="effort",
                         help="Higher = more careful plans but slower. 'low' keeps live demos snappy.")
        st.caption(f"Model: `{MODEL}` · " + ("API key found" if ai.get_api_key() else "no API key"))
        st.button("Clear all my data", icon=":material/delete:", on_click=clear_all, width="stretch",
                  help="Deletes everything in this session. Nothing is stored server-side.")


def privacy_note():
    st.markdown('<div class="wf-note"><h4>The AI sees the trip, never the people</h4><p>Names become aliases, emails and '
                'booking references are stripped, and nothing is stored on a server.</p></div>', unsafe_allow_html=True)
    st.button("See exactly what gets sent", on_click=go_nav, args=("Privacy & data",), type="tertiary")


def step_footer(i: int):
    c1, c2, c3 = st.columns([1.2, 2, 1.6], vertical_alignment="center")
    if i > 0:
        c1.button("Back", key=f"back{i}", on_click=go_step, args=(i - 1,), width="stretch")
    c2.caption(f"Step {i + 1} of {len(STEPS)}")
    if i < len(STEPS) - 1:
        c3.button(f"Next: {STEPS[i + 1]}", key=f"next{i}", type="primary", on_click=go_step, args=(i + 1,), width="stretch")
    else:
        c3.button("Go to itineraries", key="to_plan", type="primary", on_click=go_nav, args=("Itineraries",), width="stretch")


def plan_trip_page():
    ss = st.session_state
    main_col, aside = st.columns([3.2, 1], gap="large")
    with main_col:
        ui.page_title("Plan a group trip", "Fill in three short steps. Wayfare weighs everyone's interests and builds up to "
                      "three itinerary options.")
        with st.container(key="stepbar"):
            st.radio("Steps", STEPS, key="step", horizontal=True, label_visibility="collapsed",
                     format_func=lambda n: f"{STEPS.index(n) + 1} · {n}")
        i = STEPS.index(ss.step)
        (trip_tab, travellers_tab, anchors_tab)[i]()
        step_footer(i)
    with aside:
        quick_start()
        planner_settings()
        privacy_note()


# ---------------------------------------------------------------- tab: trip

def req(label: str) -> str:
    return f"{label} :red[*]"


def trip_tab():
    ss, v = st.session_state, st.session_state.ver
    t = ss.trip
    with st.container(border=True):
        c1, c2 = st.columns([3, 1.6], vertical_alignment="top")
        c1.markdown("## Trip details")
        c1.caption("Fields marked :red[*] are required.")
        c2.markdown(f'<div style="text-align:right"><span class="wf-loaded">Loaded: {html.escape(ss.loaded)}</span></div>',
                    unsafe_allow_html=True)

        ui.eyebrow("Where & when")
        c1, c2, c3 = st.columns(3)
        t["destination"] = c1.text_input(req("Destination city"), t["destination"], key=f"dest{v}", placeholder="e.g. Tokyo")
        t["start_date"] = c2.date_input(req("Start date"), t["start_date"], key=f"start{v}")
        t["num_days"] = c3.number_input(req("Number of days"), 1, 7, int(t["num_days"]), key=f"ndays{v}")
        last = t["start_date"] + timedelta(days=int(t["num_days"]) - 1)
        c3.caption(f"{t['start_date']:%a %d} – {last:%a %d %b}")
        c1, c2, c3 = st.columns(3)
        t["day_start"] = c1.time_input(req("Day starts"), to_time(t["day_start"]), key=f"ds{v}", step=1800).strftime("%H:%M")
        t["day_end"] = c2.time_input(req("Day ends"), to_time(t["day_end"]), key=f"de{v}", step=1800).strftime("%H:%M")
        t["accommodation"] = c3.text_input(req("Accommodation"), t["accommodation"], key=f"acc{v}",
                                           placeholder="Hotel name or area")
        c3.caption("Each day starts and ends here. Area is enough, no exact address needed.")

        st.divider()
        ui.eyebrow("Budget & crowds")
        c1, c2, c3 = st.columns([2, 1, 3])
        t["budget"] = c1.number_input(req("Budget per person, whole trip"), 0, 100000, int(t["budget"]), 50, key=f"bud{v}")
        c1.caption("Excludes accommodation. Food, tickets and transport.")
        currencies = list(dict.fromkeys([t["currency"], "SGD", "MYR", "USD", "EUR", "GBP", "JPY", "AUD"]))
        t["currency"] = c2.selectbox(req("Currency"), currencies, key=f"cur{v}")
        t["crowd_tolerance"] = c3.select_slider("Crowd tolerance", list(CROWD_LABELS), t["crowd_tolerance"],
                                                format_func=CROWD_LABELS.get, key=f"crowd{v}")

        st.divider()
        ui.eyebrow("Allowed transport *")
        with st.container(key="transport"):
            cols = st.columns(len(TRANSPORT_MODES))
            t["transport_modes"] = [m for col, m in zip(cols, TRANSPORT_MODES)
                                    if col.checkbox(m, m in t["transport_modes"], key=f"tm_{m}{v}")]
        if not t["transport_modes"]:
            st.warning("Pick at least one transport mode.")

        st.divider()
        c1, c2 = st.columns(2)
        t["dietary"] = c1.text_input("Group-wide dietary requirements (optional)", t["dietary"], key=f"diet{v}")
        c1.caption("Applied to every meal stop. Individual needs go in each traveller profile.")
        t["notes"] = c2.text_area("Anything else the planner should know? (optional)", t["notes"], key=f"notes{v}",
                                  height=88, max_chars=500)
        c2.caption("Emails and names here are removed before sending.")

    with st.container(border=True):
        st.markdown(f"#### Weather outlook{' · ' + t['destination'] if t['destination'] else ''}")
        if not t["destination"]:
            st.info("Enter a destination to load the forecast.")
            return
        st.caption("Open-Meteo forecast for your travel dates. Wet days get indoor backups.")
        wx = forecast(t["destination"], t["start_date"], int(t["num_days"]))
        if wx["days"]:
            cards = ""
            for n, d in enumerate(trip_dates(t), 1):
                w = wx["days"].get(d)
                if not w:
                    continue
                p = int(w["rain_prob"])
                cards += (f'<div class="wf-wx"><div class="top"><b>{fmt_date(d)}</b><span>Day {n}</span></div>'
                          f'<div class="temp"><b>{w["tmax"]:.0f}°</b> / {w["tmin"]:.0f}°</div><div>{html.escape(str(w["summary"]))}</div>'
                          f'<div class="pop"><div class="wf-bar"><span style="width:{p}%"></span></div>PoP {p}%</div></div>')
            st.markdown(f'<div class="wf-wx-grid">{cards}</div>', unsafe_allow_html=True)
        st.caption(f"Source: {wx['source']}. {wx['note']}")


# ---------------------------------------------------------------- tab: travellers

def remove_traveller(tid: str):
    st.session_state.travellers = [t for t in st.session_state.travellers if t["id"] != tid]


def add_traveller():
    st.session_state.travellers.append({"id": uid(), "name": f"Traveller {len(st.session_state.travellers) + 1}",
                                        "weight": 1.0, "pace": 3, "dietary": "", "mobility": "",
                                        "interests": {d: 3 for d in INTERESTS}})


def equal_weights():
    for t in st.session_state.travellers:
        t["weight"] = 1.0
        st.session_state.pop(f"tr_{t['id']}_weight", None)


def travellers_tab():
    ss = st.session_state
    ui.page_title("Travellers", "One profile per person. Rate interests 0 (skip) to 5 (love it). **Influence weight** "
                  "lets the group decide whose preferences count more; keep them equal for an even split.")
    w = normalised_weights(ss.travellers)
    with st.container(border=True):
        st.markdown("**Influence share in the group**")
        st.markdown('<div class="wf-share">' + "".join(
            f'<div style="width:{x * 100:.1f}%;background:{TRAVELLER_COLORS[i % len(TRAVELLER_COLORS)]}"></div>'
            for i, x in enumerate(w)) + "</div>", unsafe_allow_html=True)
        st.markdown('<div class="wf-legend">' + "".join(
            f'<div><span class="sw" style="background:{TRAVELLER_COLORS[i % len(TRAVELLER_COLORS)]}"></span>'
            f'<span class="nm">{html.escape(t["name"])}</span><b>{x * 100:.0f}%</b></div>'
            for i, (t, x) in enumerate(zip(ss.travellers, w))) + "</div>", unsafe_allow_html=True)
    for tr in ss.travellers:
        k = f"tr_{tr['id']}_"
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1], vertical_alignment="bottom")
            tr["name"] = c1.text_input("Name (stays on this device)", tr["name"], key=k + "name")
            tr["weight"] = c2.slider("Influence weight", 0.0, 1.0, float(tr["weight"]), 0.1, key=k + "weight")
            tr["pace"] = c3.select_slider("Preferred pace", list(PACE_LABELS), tr["pace"], format_func=PACE_LABELS.get, key=k + "pace")
            c4.button("Remove", key=k + "rm", on_click=remove_traveller, args=(tr["id"],), disabled=len(ss.travellers) == 1)
            with st.container(key=k + "interests"):
                cols = st.columns(len(INTERESTS))
                for col, d in zip(cols, INTERESTS):
                    tr["interests"][d] = col.slider(INTEREST_LABELS[d], 0, 5, int(tr["interests"][d]), key=k + d)
            c1, c2 = st.columns(2)
            tr["dietary"] = c1.text_input("Dietary needs", tr["dietary"], key=k + "diet", placeholder="e.g. vegetarian, halal")
            tr["mobility"] = c2.text_input("Accessibility needs", tr["mobility"], key=k + "mob", placeholder="e.g. avoid stairs")

    c1, c2, _ = st.columns([1, 1, 3])
    c1.button("Add traveller", icon=":material/add:", on_click=add_traveller, type="primary", width="stretch")
    c2.button("Reset to equal weights", icon=":material/restart_alt:", on_click=equal_weights, width="stretch")


# ---------------------------------------------------------------- tab: must-visits

def remove_anchor(aid: str):
    st.session_state.anchors = [a for a in st.session_state.anchors if a["id"] != aid]


def add_anchor(name: str, kind: str = "flexible", d: str = "", t: str = "", duration: int = 60, note: str = "", url: str = ""):
    st.session_state.anchors.append({"id": uid(), "name": name, "kind": kind, "date": d, "time": t,
                                     "duration_min": duration, "note": note, "source_url": url})


def fill_demo_link():
    ss = st.session_state
    ss.link_url, ss.link_caption = DEMO_LINK["url"], DEMO_LINK["caption"]
    ss.link_ver += 1


def anchors_tab():
    ss = st.session_state
    dates = trip_dates(ss.trip)
    ui.page_title("Must-visits", "Optional. Add anything the plan has to include: type it in, or paste a TikTok, "
                  "Instagram or web link. **Fixed** = non-negotiable date and time (e.g. pre-booked tickets). "
                  "**Any day** = must be included, the AI picks when.")
    if not ss.anchors:
        st.info("No must-visits yet. Add one below or import from a link.")
    for a in ss.anchors:
        k = f"an_{a['id']}_"
        with st.container(border=True):
            c1, c2, c3, c4, c5, c6 = st.columns([3, 1.6, 1.6, 1.2, 1.2, 0.8], vertical_alignment="bottom")
            a["name"] = c1.text_input("Place / activity", a["name"], key=k + "name")
            a["kind"] = c2.radio("Type", ["fixed", "flexible"], ["fixed", "flexible"].index(a["kind"]), key=k + "kind",
                                 format_func={"fixed": "🔒 Fixed", "flexible": "📌 Any day"}.get)
            if a["kind"] == "fixed":
                idx = dates.index(a["date"]) if a["date"] in dates else 0
                if a["date"] and a["date"] not in dates:
                    c3.caption("⚠️ date outside trip, moved to Day 1")
                a["date"] = c3.selectbox("Date", dates, idx, key=k + "date",
                                         format_func=lambda d: f"Day {dates.index(d) + 1} · {fmt_date(d)}")
                a["time"] = c4.time_input("Start", to_time(a["time"] or "10:00"), key=k + "time", step=900).strftime("%H:%M")
            else:
                c3.caption("Any day")
            a["duration_min"] = c5.number_input("Minutes", 15, 600, int(a["duration_min"]), 15, key=k + "dur")
            c6.button("✕", key=k + "rm", on_click=remove_anchor, args=(a["id"],), help="Remove")
            if a.get("note") or a.get("source_url"):
                st.caption(f"📝 {a['note']}" + (f" · source: {a['source_url']}" if a.get("source_url") else ""))

    with st.expander("➕ Add a must-visit manually"):
        with st.form("add_anchor", clear_on_submit=True, border=False):
            c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, 1.2, 1.2])
            name = c1.text_input("Place / activity")
            kind = c2.radio("Type", ["flexible", "fixed"], format_func={"fixed": "🔒 Fixed", "flexible": "📌 Any day"}.get)
            d = c3.selectbox("Date (if fixed)", dates, format_func=fmt_date)
            t = c4.time_input("Start (if fixed)", time(10, 0), step=900)
            dur = c5.number_input("Minutes", 15, 600, 90, 15)
            note = st.text_input("Note (optional)")
            if st.form_submit_button("Add") and name.strip():
                add_anchor(name.strip(), kind, d if kind == "fixed" else "", t.strftime("%H:%M") if kind == "fixed" else "", dur, note)
                st.rerun()

    st.divider()
    st.markdown("#### Import from a link")
    st.caption("Paste the link and the caption (or what you remember). Claude identifies the place. Tracking parameters "
               "are stripped from the link, and the link itself is never fetched.")
    lv = ss.link_ver
    url = st.text_input("Link", ss.link_url, key=f"lurl{lv}", placeholder="https://www.tiktok.com/@…")
    cap = st.text_area("Caption / description", ss.link_caption, key=f"lcap{lv}", height=70)
    c1, c2, _ = st.columns([1.3, 1.3, 3])
    c1.button("Use demo Instagram link", on_click=fill_demo_link, width="stretch")
    if c2.button("🔎 Identify place", type="primary", disabled=not (url or cap), width="stretch") and ai_ready():
        log = []
        res = run_ai("Identify place from link", ai.extract_link, clean_url(url),
                     scrub(cap, ss.travellers, log, "caption"), ss.trip["destination"])
        if res:
            ss.extracted = {"place": res.model_dump(), "url": clean_url(url)}

    if ss.extracted:
        p = ss.extracted["place"]
        with st.container(border=True):
            if not p["found"]:
                st.warning(f"Couldn't identify a specific place. {md(p['notes'])}")
            else:
                conf_color = "green" if p["confidence"] == "high" else "orange"
                st.markdown(f"**{md(p['place_name'])}** · {md(p['area'])}, {md(p['city'])}  \n"
                            f":blue-badge[{md(p['category'])}] :gray-badge[~{p['suggested_duration_min']} min] "
                            f":{conf_color}-badge[confidence: {p['confidence']}]")
                st.write(md(p["why_people_go"]))
                if p["notes"]:
                    st.caption(md(p["notes"]))
                if not p["matches_destination"]:
                    st.warning(f"This doesn't look like it's in {ss.trip['destination']}.")
                c1, c2, _ = st.columns([1.4, 1.4, 3])
                if c1.button("📌 Add as must-visit (any day)"):
                    add_anchor(p["place_name"], "flexible", duration=p["suggested_duration_min"],
                               note=f"Imported from link: {p['why_people_go']}", url=ss.extracted["url"])
                    ss.extracted = None
                    st.rerun()
                if c2.button("🔒 Add as fixed (set time above)"):
                    add_anchor(p["place_name"], "fixed", dates[0], "10:00", p["suggested_duration_min"],
                               note="Imported from link", url=ss.extracted["url"])
                    ss.extracted = None
                    st.rerun()


# ---------------------------------------------------------------- map

def plan_map(option: dict, height: int = 420):
    points, paths = [], []
    hotel = [option["hotel_lon"], option["hotel_lat"]]
    for i, d in enumerate(option["days"]):
        color = DAY_COLORS[i % len(DAY_COLORS)]
        path = [hotel]
        for s in d["stops"]:
            points.append({"lon": s["lon"], "lat": s["lat"], "color": color,
                           "name": f"Day {d['day_number']} · {s['start_time']} {s['name']}"})
            path.append([s["lon"], s["lat"]])
        path.append(hotel)
        paths.append({"path": path, "color": color, "name": f"Day {d['day_number']} route"})
    points.append({"lon": hotel[0], "lat": hotel[1], "color": [20, 20, 20], "name": "🏨 Accommodation"})
    lats, lons = [p["lat"] for p in points], [p["lon"] for p in points]
    span = max(max(lats) - min(lats), max(lons) - min(lons))
    zoom = 12 if span < 0.08 else 11 if span < 0.2 else 10 if span < 0.45 else 9 if span < 1 else 7
    st.pydeck_chart(pdk.Deck(
        layers=[
            pdk.Layer("PathLayer", paths, get_path="path", get_color="color", width_min_pixels=3, opacity=0.55, pickable=True),
            pdk.Layer("ScatterplotLayer", points, get_position="[lon, lat]", get_fill_color="color", get_radius=40,
                      radius_min_pixels=6, stroked=True, get_line_color=[255, 255, 255], line_width_min_pixels=1, pickable=True),
        ],
        initial_view_state=pdk.ViewState(latitude=sum(lats) / len(lats), longitude=sum(lons) / len(lons), zoom=zoom),
        tooltip={"text": "{name}"},
    ), height=height)
    legend = " ".join(
        f"<span style='color:rgb({c[0]},{c[1]},{c[2]});font-weight:600'>● Day {i + 1}</span>"
        for i, c in enumerate(DAY_COLORS[: len(option["days"])])
    )
    st.markdown(legend + " &nbsp; ● Accommodation · <span style='opacity:.7'>locations approximate</span>", unsafe_allow_html=True)


# ---------------------------------------------------------------- tab: plan

def remove_stop(day: dict, stop_uid: str):
    stop = next(s for s in day["stops"] if s["_uid"] == stop_uid)
    day["stops"] = [s for s in day["stops"] if s["_uid"] != stop_uid]
    st.session_state.avoid.append(stop["name"])
    day["_edited"] = True


def apply_swap(day: dict, stop_uid: str, alt: dict):
    i = next(i for i, s in enumerate(day["stops"]) if s["_uid"] == stop_uid)
    st.session_state.avoid.append(day["stops"][i]["name"])
    day["stops"][i] = prepare_option({"days": [{"stops": [dict(alt)]}]})["days"][0]["stops"][0]
    st.session_state.swaps.pop(stop_uid, None)


def compare_text(sel: dict, other: dict, label: str) -> str:
    bits = []
    d_nsw = (other["nsw"] - sel["nsw"]) * 100
    d_min = (other["min"] - sel["min"]) * 100
    d_cost = other["total_cost"] - sel["total_cost"]
    d_transit = other["transit_min"] - sel["transit_min"]
    if abs(d_nsw) >= 1:
        bits.append(f"fair group score {'+' if d_nsw > 0 else ''}{d_nsw:.0f}")
    if abs(d_min) >= 2:
        bits.append(f"least-satisfied member {'+' if d_min > 0 else ''}{d_min:.0f} pts")
    if abs(d_cost) >= 5:
        bits.append(f"{money(abs(d_cost))} {'more' if d_cost > 0 else 'cheaper'} pp")
    if abs(d_transit) >= 15:
        bits.append(f"{abs(d_transit)} min {'more' if d_transit > 0 else 'less'} in transit")
    if other["hidden_gems"] != sel["hidden_gems"]:
        bits.append(f"{other['hidden_gems']} vs {sel['hidden_gems']} local hidden gems")
    return f"**{label}**: " + (", ".join(bits) if bits else "very similar on all measured criteria") + "."


def fairness_panel(option: dict, summary: dict):
    ss = st.session_state
    st.markdown("#### ⚖️ Group balance")
    c1, c2, c3 = st.columns(3)
    c1.metric("Fair group score", f"{summary['nsw'] * 100:.0f}", help="Weighted Nash social welfare: high only when every member is reasonably served.")
    c2.metric("Least-satisfied member", f"{summary['min'] * 100:.0f}")
    c3.metric("Evenness (Jain)", f"{summary['jain']:.2f}", help="1.00 = perfectly even. On its own it can't tell 'everyone happy' from 'everyone unhappy', so it's shown alongside the fair score.")
    show = st.toggle("Show per-traveller match (visible to the whole group)", True, key="show_individual")
    if show:
        df = pd.DataFrame({
            "Traveller": [t["name"] for t in ss.travellers],
            "Weight": [f"{w * 100:.0f}%" for w in summary["weights"]],
            "Preference match": [s * 100 for s in summary["satisfaction"]],
        })
        st.dataframe(df, hide_index=True, width="stretch", column_config={
            "Preference match": st.column_config.ProgressColumn(format="%.0f", min_value=0, max_value=100)})
    st.caption(md(option["group_balance_note"]))
    with st.expander("How are these scores calculated?"):
        st.markdown(
            "Computed in the app from your settings, not by the AI:\n"
            "- Claude tags every stop with how strongly it serves each interest (0–1).\n"
            "- **Match** for a traveller = the stop's tags averaged over that traveller's interest ratings, then averaged over all stops.\n"
            "- **Fair group score** = weighted geometric mean of members' matches (weighted Nash social welfare). "
            "One unhappy member pulls it down sharply, so a plan can't win by serving only the majority.\n"
            "- **Jain's index** measures evenness only. Everyone could be equally dissatisfied, so we never use it alone.\n"
            "- Changing influence weights tilts the score towards higher-weighted members.")


def render_stop(day: dict, si: int, stop: dict, prev_leg: dict | None):
    ss = st.session_state
    u = stop["_uid"]
    with st.container(border=True):
        c1, c2, c3 = st.columns([0.9, 6, 1.6])
        c1.markdown(f"**{stop['start_time']}**  \n<span style='opacity:.6'>{stop['end_time']}</span>", unsafe_allow_html=True)
        badges = []
        if stop["is_anchor"]:
            badges.append(":violet-badge[🔒 your must-visit]")
        elif stop.get("_locked"):
            badges.append(":violet-badge[🔒 locked]")
        if stop["hidden_gem"]:
            badges.append(":green-badge[💎 local gem]")
        badges.append(CROWD_BADGE[stop["crowd_level"]])
        badges.append(":blue-badge[🏠 indoor]" if stop["indoor"] else ":gray-badge[🌤 outdoor]")
        badges.append(f":gray-badge[{money(stop['est_cost_per_person'])} pp]")
        if CONF_BADGE[stop["info_confidence"]]:
            badges.append(CONF_BADGE[stop["info_confidence"]])
        c2.markdown(f"**{KIND_ICON[stop['kind']]} {md(stop['name'])}** · {md(stop['area'])}  \n" + " ".join(badges))
        c2.markdown(md(stop["description"]) + "  \n" + " ".join(f":small[✓ {md(w)}]" for w in stop["why"]))
        if stop["caution"]:
            c2.warning(md(stop["caution"]), icon="⚠️")
        with c3:
            if not stop["is_anchor"]:
                stop["_locked"] = st.toggle("Lock", stop.get("_locked", False), key=f"lock_{u}",
                                            help="Keep this stop when regenerating.")
            if st.button("🔄 Swap", key=f"swap_{u}", width="stretch", disabled=stop["is_anchor"]) and ai_ready():
                res = run_ai(f"Alternatives for {stop['name']}", ai.swap_alternatives, current_payload()[0], day, stop)
                if res:
                    ss.swaps[u] = [a.model_dump() for a in res.alternatives]
            st.button("🗑️ Remove", key=f"rm_{u}", on_click=remove_stop, args=(day, u), width="stretch",
                      disabled=stop["is_anchor"])
        with st.expander("Why this stop? Score breakdown & sources"):
            rows = scoring.stop_breakdown(stop, prev_leg, ss.travellers, dict(ss.trip, dates=trip_dates(ss.trip)))
            st.dataframe(pd.DataFrame(rows, columns=["Criterion", "Value"]), hide_index=True, width="stretch")
            st.markdown(f"**Booking:** {md(stop['booking_info'])}  \n**Info confidence:** {stop['info_confidence']}")
            st.caption(f"Source: Claude general knowledge (not live data). {VERIFY_NOTE}")
        if u in ss.swaps:
            st.markdown("**Alternatives for this slot**")
            for j, alt in enumerate(ss.swaps[u]):
                a = alt["stop"]
                ac1, ac2 = st.columns([6, 1.3])
                ac1.markdown(f"{KIND_ICON[a['kind']]} **{md(a['name'])}** · {md(a['area'])} · {a['start_time']}–{a['end_time']} · "
                             f"{money(a['est_cost_per_person'])} · {CROWD_BADGE[a['crowd_level']]}"
                             f"{' :green-badge[💎 local gem]' if a['hidden_gem'] else ''}  \n_{md(alt['vs_current'])}_")
                ac2.button("Use this", key=f"use_{u}_{j}", on_click=apply_swap, args=(day, u, a), width="stretch")
            st.button("Keep current", key=f"keep_{u}", on_click=lambda: ss.swaps.pop(u, None))


def leg_picker(stop: dict):
    legs = stop["transport_to_next"]
    if not legs:
        return
    labels = [f"{TRANSPORT_ICONS[l['mode']]} {l['mode']} · {l['duration_min']} min · {money(l['cost'])}" for l in legs]
    idx = st.radio("Getting to the next stop", range(len(legs)), min(stop.get("_mode_idx", 0), len(legs) - 1),
                   format_func=lambda i: labels[i] + (" (recommended)" if i == 0 else ""), horizontal=True,
                   key=f"leg_{stop['_uid']}", label_visibility="collapsed")
    stop["_mode_idx"] = idx
    st.caption(f"↓ {md(legs[idx]['details'])}")


def render_day(day: dict, wx: dict):
    ss = st.session_state
    w = wx["days"].get(day["date"])
    c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
    c1.markdown(f"### {md(day['theme'])}\n{fmt_date(day['date'])}"
                + (f" · {w['summary']} {w['tmin']:.0f}–{w['tmax']:.0f}°C, 🌧 {w['rain_prob']}%" if w else ""))
    c2.metric("Cost pp", money(scoring.day_cost(day)))
    c3.metric("In transit", f"{scoring.day_transit_min(day)} min")
    c4.metric("Walking", f"{day['walking_km']:.1f} km")
    c5.metric("Intensity", f"{scoring.day_intensity(day):.1f}/5")
    if day.get("_edited"):
        st.info("You've edited this day. Travel times may be off; use *Regenerate around my edits* to re-route.", icon="✏️")
    fh = day["from_hotel"]
    st.caption(f"🏨 Leave accommodation → {TRANSPORT_ICONS[fh['mode']]} {fh['mode']}, {fh['duration_min']} min, {money(fh['cost'])} · {md(fh['details'])}")
    prev = fh
    for si, stop in enumerate(day["stops"]):
        render_stop(day, si, stop, prev)
        leg_picker(stop)
        prev = scoring.chosen_leg(stop)
    th = day["to_hotel"]
    st.caption(f"🏨 Back to accommodation → {TRANSPORT_ICONS[th['mode']]} {th['mode']}, {th['duration_min']} min, {money(th['cost'])}")
    (st.warning if w and w["wet"] else st.caption)(f"☔ Wet-weather backup: {md(day['wet_weather_backup'])}")
    st.caption(f"Pace: {md(day['pace_note'])}")


def generate(strategies: list[dict], extra_anchors=None, extra_notes="", replace_key: str | None = None):
    ss = st.session_state
    payload, log = current_payload(extra_anchors, extra_notes)
    ss.last_sent = {"payload": payload, "log": log, "at": datetime.now().strftime("%d %b %Y %H:%M:%S")}
    wx = forecast(ss.trip["destination"], ss.trip["start_date"], int(ss.trip["num_days"]))
    t0 = datetime.now()
    with st.status(f"Planning {len(strategies)} itinerary option(s) in parallel…", expanded=True) as status:
        st.write("🔒 De-identified trip data prepared (see *Privacy & data* tab)")
        st.write(f"🌦️ {wx['source'] if wx['days'] else wx['note']}")
        st.write("🧠 Claude is drafting: " + ", ".join(s["label"] for s in strategies))
        results = ai.generate_options(payload, wx, strategies, ss.effort)
        secs = (datetime.now() - t0).seconds
        n_ok = sum(1 for _, o, _ in results if isinstance(o, dict))
        status.update(label=f"{n_ok}/{len(results)} option(s) ready in {secs}s",
                      state="complete" if n_ok else "error", expanded=not n_ok)
    entries = []
    for strategy, out, meta in results:
        log_call(f"Itinerary: {strategy['label']}", meta)
        if isinstance(out, dict):
            entries.append({"strategy": strategy, "option": prepare_option(out), "error": None})
        else:
            entries.append({"strategy": strategy, "option": None, "error": out})
            st.error(f"{strategy['label']}: {out}")
    if not any(e["option"] for e in entries):
        return False
    if replace_key:
        new = entries[0]
        ss.options = [new if x["strategy"]["key"] == replace_key else x for x in ss.options]
        ss.avoid = []
    else:
        ss.options = entries
        ss.pop("sel_radio", None)
    ss.swaps, ss.contrast, ss.confirmed, ss.pending_replan = {}, None, None, None
    return True


def itinerary_markdown(entry: dict) -> str:
    ss = st.session_state
    o = entry["option"]
    lines = [f"# {o['title']}", f"_{ss.trip['destination']} · {entry['strategy']['label']}_", "", o["summary"], ""]
    for d in o["days"]:
        lines += [f"## Day {d['day_number']} · {fmt_date(d['date'])}: {d['theme']}", ""]
        for s in d["stops"]:
            leg = scoring.chosen_leg(s)
            lines.append(f"- **{s['start_time']}–{s['end_time']} {s['name']}** ({s['area']}), ~{money(s['est_cost_per_person'])} pp. {s['description']}")
            if s["booking_info"]:
                lines.append(f"  - Booking: {s['booking_info']}")
            if leg:
                lines.append(f"  - Then: {leg['mode']}, {leg['duration_min']} min ({leg['details']})")
        lines += ["", f"_Wet-weather backup: {d['wet_weather_backup']}_", ""]
    lines += ["---", VERIFY_NOTE]
    return "\n".join(lines)


def plan_tab():
    ss = st.session_state
    ui.page_title("Itineraries", "Generate options for the group, compare them, then refine the one you like.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Destination", ss.trip["destination"] or "—")
    c2.metric("Days", int(ss.trip["num_days"]))
    c3.metric("Travellers", len(ss.travellers))
    c4.metric("Must-visits", len(ss.anchors))
    can = bool(ss.trip["destination"] and ss.trip["transport_modes"])
    if not can:
        st.warning("Add a destination and at least one transport mode on the Trip tab.")
    if st.button(f"✨ Generate {ss.n_options} itinerary option(s)", type="primary", disabled=not can) and ai_ready():
        generate(STRATEGIES[: ss.n_options])

    ok = [e for e in ss.options if e["option"]]
    if not ok:
        st.caption("Each option is drafted by Claude with a different planning strategy, then scored by the app.")
        return

    st.info(VERIFY_NOTE, icon="ℹ️")
    summaries = [scoring.option_summary(e["option"], ss.travellers) for e in ok]
    n_days = max(1, int(ss.trip["num_days"]))
    best = max(range(len(ok)), key=lambda i: summaries[i]["nsw"])
    ui.page_title(f"Pick one of {len(ok)} itineraries", "Same trip, different ways to balance it. You can fine-tune the one you choose.")
    cols = st.columns(len(ok))
    for i, (col, e, s) in enumerate(zip(cols, ok, summaries)):
        band, ink = OPTION_BANDS[i % len(OPTION_BANDS)]
        with col, st.container(border=True):
            badge = '<span class="wf-badge">Best group fit</span>' if i == best and len(ok) > 1 else ""
            st.markdown(
                f'<div class="wf-opt-head" style="background:{band};color:{ink}">{badge}'
                f'<div class="wf-opt-letter">Option {chr(65 + i)}</div>'
                f'<div class="wf-opt-name">{md(e["strategy"]["label"])}</div></div>'
                '<div class="wf-stat-grid">'
                f'<div><div class="wf-stat-k">Cost / person</div><div class="wf-stat-v">{money(s["total_cost"])}</div></div>'
                f'<div><div class="wf-stat-k">Stops</div><div class="wf-stat-v">{s["n_stops"]}</div></div>'
                f'<div><div class="wf-stat-k">Walking / day</div><div class="wf-stat-v">{s["walking_km"] / n_days:.1f} km</div></div>'
                f'<div><div class="wf-stat-k">In transit</div><div class="wf-stat-v">{s["transit_min"] / 60:.1f} h</div></div>'
                "</div>"
                + ui.bar_row("Fair score", s["nsw"] * 100) + ui.bar_row("Avg match", s["weighted_avg"] * 100)
                + ui.bar_row("Least happy", s["min"] * 100),
                unsafe_allow_html=True)
            st.markdown(f'<span class="wf-chip">{s["hidden_gems"]} local gems</span>'
                        f'<span class="wf-chip warn">{s["high_crowd"]} busy stops</span>', unsafe_allow_html=True)
            st.button("Choose this plan", key=f"choose_{i}", type="primary" if i == best else "secondary", width="stretch",
                      on_click=lambda i=i: ss.update(sel_radio=i))

    sel = min(ss.get("sel_radio", best), len(ok) - 1)
    ss.sel_radio = sel
    st.caption("Switch between your options:")
    sel = st.radio("Review option", range(len(ok)), format_func=lambda i: ok[i]["strategy"]["label"],
                   horizontal=True, key="sel_radio", label_visibility="collapsed")
    entry, summ = ok[sel], summaries[sel]
    others = [compare_text(summ, s, ok[i]["strategy"]["label"]) for i, s in enumerate(summaries) if i != sel]
    if others:
        st.markdown("**How the other options differ from this one:**  \n" + "  \n".join(others))

    opt = entry["option"]
    st.divider()
    st.markdown(f"## {md(opt['title'])}")
    st.write(md(opt["summary"]))
    budget = ss.trip["budget"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Est. cost per person", money(summ["total_cost"]), f"{money(budget - summ['total_cost'])} under budget"
              if summ["total_cost"] <= budget else f"-{money(summ['total_cost'] - budget)} over budget")
    c2.metric("Stops", summ["n_stops"])
    c3.metric("Total transit", f"{summ['transit_min'] / 60:.1f} h")
    c4.metric("Local hidden gems", summ["hidden_gems"])
    for wmsg in opt["warnings"]:
        st.warning(md(wmsg))
    for f in scoring.pace_flags(opt, ss.travellers):
        st.warning(f, icon="🥵")

    left, right = st.columns([1, 1.3])
    with left:
        fairness_panel(opt, summ)
    with right:
        plan_map(opt)

    wx = forecast(ss.trip["destination"], ss.trip["start_date"], int(ss.trip["num_days"]))
    st.markdown("#### 🗓️ Day by day")
    for tab, day in zip(st.tabs([f"Day {d['day_number']}" for d in opt["days"]]), opt["days"]):
        with tab:
            render_day(day, wx)

    st.divider()
    st.markdown("#### 🤔 Why this instead of that?")
    for t in opt["tradeoffs"]:
        with st.container(border=True):
            st.markdown(f"Picked **{md(t['chosen'])}** over **{md(t['alternative'])}**: {md(t['deciding_factor'])}  \n"
                        f"↪️ _What would change it:_ {md(t['counterfactual'])}")
    stops = [(d, s) for d in opt["days"] for s in d["stops"]]
    c1, c2, c3 = st.columns([2, 2, 1])
    pick = c1.selectbox("Ask about a stop", range(len(stops)),
                        format_func=lambda i: f"Day {stops[i][0]['day_number']} · {stops[i][1]['name']}")
    alt = c2.text_input("…instead of", placeholder="e.g. Sentosa")
    c3.write("")
    if c3.button("Ask", width="stretch", disabled=not alt.strip()) and ai_ready():
        d, s = stops[pick]
        res = run_ai("Contrastive explanation", ai.explain_contrast, current_payload()[0], d, s, alt.strip())
        if res:
            ss.contrast = {"stop": s["name"], "alt": alt.strip(), **res.model_dump()}
    if ss.contrast:
        c = ss.contrast
        verdict = {"keep_current": ":green-badge[current choice fits better]",
                   "alternative_is_comparable": ":orange-badge[close call]",
                   "alternative_is_better": ":red-badge[alternative may fit better: consider swapping]"}[c["verdict"]]
        with st.container(border=True):
            st.markdown(f"**{md(c['stop'])}** vs **{md(c['alt'])}** {verdict}  \n**Deciding factor:** {md(c['deciding_factor'])}")
            st.dataframe(pd.DataFrame(c["comparisons"]).rename(columns={"criterion": "Criterion", "chosen": c["stop"], "alternative": c["alt"]}),
                         hide_index=True, width="stretch")
            st.markdown(f"↪️ **What would change it:** {md(c['counterfactual'])}")

    st.divider()
    st.markdown("#### 🧑‍✈️ You decide")
    locked = [(d, s) for d in opt["days"] for s in d["stops"] if s.get("_locked") and not s["is_anchor"]]
    st.caption(f"{len(locked)} stop(s) locked · {len(ss.avoid)} removed or swapped out. Regenerating keeps your locks and "
               "must-visits and avoids what you removed.")
    feedback = st.text_input("Anything to change? (optional)", placeholder="e.g. more street food, finish earlier on day 3")
    c1, c2 = st.columns(2)
    if c1.button("🔁 Regenerate this option around my edits", width="stretch") and ai_ready():
        extra = [{"id": uid(), "name": s["name"], "kind": "fixed", "date": d["date"], "time": s["start_time"],
                  "duration_min": minutes_between(s["start_time"], s["end_time"]), "note": "Locked by the group", "source_url": ""}
                 for d, s in locked]
        notes = "\n".join(filter(None, [
            f"Do NOT include: {', '.join(ss.avoid)}." if ss.avoid else "",
            f"Group feedback on the previous draft: {feedback}" if feedback else "",
        ]))
        if generate([entry["strategy"]], extra, notes, replace_key=entry["strategy"]["key"]):
            st.rerun()
    if c2.button("✅ Confirm this itinerary", type="primary", width="stretch"):
        ss.confirmed = {"entry": copy.deepcopy(entry), "at": datetime.now().strftime("%d %b %Y, %H:%M")}
    if ss.confirmed:
        conf = ss.confirmed["entry"]
        changed = json.dumps(conf["option"], sort_keys=True) != json.dumps(entry["option"], sort_keys=True)
        if changed:
            st.warning("You've changed the plan since confirming. Confirm again to save the changes.")
        else:
            st.success(f"Itinerary confirmed and saved at {ss.confirmed['at']}. Nothing is final until you confirm it.")
        c1, c2, _ = st.columns([1, 1, 2])
        c1.download_button("⬇️ Download (Markdown)", itinerary_markdown(conf), "itinerary.md", width="stretch")
        clean = json.loads(json.dumps(conf["option"]))
        c2.download_button("⬇️ Download (JSON)", json.dumps(clean, indent=2, ensure_ascii=False), "itinerary.json", width="stretch")


# ---------------------------------------------------------------- tab: live replan

def accept_replan():
    ss = st.session_state
    p = ss.pending_replan
    entry = selected_entry()
    new_day = prepare_option({"days": [p["day"]]})["days"][0]
    entry["option"]["days"][p["day_idx"]] = new_day
    ss.pending_replan = None


def compact_day(day: dict):
    for s in day["stops"]:
        st.markdown(f"`{s['start_time']}` {KIND_ICON[s['kind']]} {md(s['name'])}"
                    + (" 🔒" if s["is_anchor"] else "") + (" 🏠" if s["indoor"] else ""))


def replan_tab():
    ss = st.session_state
    entry = selected_entry()
    st.subheader("⚡ Something changed? Re-plan on the go")
    if not entry:
        st.info("Generate an itinerary on the Plan tab first.")
        return
    opt = entry["option"]
    st.caption(f"Working on: **{md(opt['title'])}**. Changes are only applied after you accept them.")
    c1, c2 = st.columns([2, 1])
    di = c1.selectbox("Which day?", range(len(opt["days"])),
                      format_func=lambda i: f"Day {opt['days'][i]['day_number']} · {fmt_date(opt['days'][i]['date'])}: {opt['days'][i]['theme']}")
    now = c2.time_input("Current time", time(14, 0), step=900)
    quick = st.pills("Quick scenarios", ["☔ Heavy rain for the rest of the day", "🚇 Train delay, we're running 45 min late",
                                         "🍜 The group is craving ramen for the next meal", "😴 The group is tired, slow down",
                                         "👥 Next stop is unexpectedly packed"], key="quick")
    event = st.text_area("Describe what happened", value=quick or "", height=70,
                         placeholder="e.g. heavy rain from 2pm, we're near Orchard Road")
    if st.button("⚡ Re-plan the rest of this day", type="primary", disabled=not event.strip()) and ai_ready():
        wx = forecast(ss.trip["destination"], ss.trip["start_date"], int(ss.trip["num_days"]))
        res = run_ai("Live re-plan", ai.replan_day, current_payload()[0], wx, opt["days"][di], event.strip(), now.strftime("%H:%M"))
        if res:
            ss.pending_replan = {"day_idx": di, "day": res.updated_day.model_dump(), "changes": res.change_summary, "event": event}

    p = ss.pending_replan
    if p:
        with st.container(border=True):
            st.markdown(f"**Proposed changes** for “{md(p['event'])}”")
            for ch in p["changes"]:
                st.markdown(f"- {md(ch)}")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Current**")
                compact_day(opt["days"][p["day_idx"]])
            with c2:
                st.markdown("**Proposed**")
                compact_day(p["day"])
            b1, b2, _ = st.columns([1, 1, 3])
            b1.button("✅ Accept changes", type="primary", on_click=accept_replan, width="stretch")
            b2.button("✕ Discard", on_click=lambda: ss.update(pending_replan=None), width="stretch")


# ---------------------------------------------------------------- tab: explore

def explore_tab():
    ss = st.session_state
    st.subheader("🔍 Discover beyond the usual list")
    tags = st.pills("Tags", ["nature", "nightlife", "street food", "cafes", "culture", "shopping", "kid-friendly",
                             "rainy day", "free", "photo spots", "local markets"], selection_mode="multi", key="tags")
    if st.button("Find places", type="primary", disabled=not (tags and ss.trip["destination"])) and ai_ready():
        res = run_ai("Explore places", ai.explore, ss.trip["destination"], tags, current_payload()[0])
        if res:
            ss.explore = [dict(p.model_dump(), color=[49, 163, 84] if p.hidden_gem else [49, 130, 189]) for p in res.places]
    if not ss.explore:
        return
    st.pydeck_chart(pdk.Deck(
        layers=[pdk.Layer("ScatterplotLayer", ss.explore, get_position="[lon, lat]", radius_min_pixels=7,
                          get_fill_color="color", pickable=True)],
        initial_view_state=pdk.ViewState(latitude=sum(p["lat"] for p in ss.explore) / len(ss.explore),
                                         longitude=sum(p["lon"] for p in ss.explore) / len(ss.explore), zoom=11),
        tooltip={"text": "{name}"}), height=320)
    st.caption("🟢 local hidden gem · 🔵 well-known · locations approximate")
    names = {a["name"].lower() for a in ss.anchors}
    for i, p in enumerate(ss.explore):
        with st.container(border=True):
            c1, c2 = st.columns([6, 1.3])
            c1.markdown(f"**{md(p['name'])}** · {md(p['area'])} {CROWD_BADGE[p['crowd_level']]}"
                        f"{' :green-badge[💎 local gem]' if p['hidden_gem'] else ''} :gray-badge[{money(p['est_cost_per_person'])}]  \n"
                        f"{md(p['description'])}  \n:small[Best time: {md(p['best_time'])} · " + ", ".join(p["tags"]) + "]")
            added = p["name"].lower() in names
            c2.button("✓ Added" if added else "📌 Must-visit", key=f"exp_{i}", disabled=added, width="stretch",
                      on_click=add_anchor, args=(p["name"], "flexible", "", "", 90, f"From Explore: {p['description']}"))


# ---------------------------------------------------------------- tab: privacy

def privacy_tab():
    ss = st.session_state
    st.subheader("🔒 What the AI sees: the trip, never the people")
    st.markdown("Everything passes through a de-identification layer before it reaches Claude. Only an allowlist of "
                "fields is sent, names become aliases, and personal identifiers are stripped. Below is the **live "
                "preview** of the next request, built from what you've entered.")
    payload, log = current_payload()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**What you entered (stays in your session)**")
        st.json({
            "travellers": [{"name": t["name"], "dietary": t["dietary"], "mobility": t["mobility"]} for t in ss.travellers],
            "trip_notes": ss.trip.get("notes", ""),
            "must_visits": [{"name": a["name"], "note": a.get("note", ""), "link": a.get("source_url", "")} for a in ss.anchors],
        }, expanded=True)
    with c2:
        st.markdown("**What Claude receives**")
        st.json(payload, expanded=True)
    st.markdown("**Applied protections**")
    for item in log:
        st.markdown(f"- ✅ {item}")
    al = aliases(ss.travellers)
    st.caption("Alias map, kept only on this device: " + ", ".join(f"{t['name']} → {al[t['id']]}" for t in ss.travellers))
    if ss.last_sent:
        with st.expander(f"Last itinerary request actually sent ({ss.last_sent['at']})"):
            st.json(ss.last_sent["payload"])

    st.divider()
    st.subheader("📚 Data sources & limitations")
    st.markdown(f"""
| Information | Source | Limitation |
|---|---|---|
| Places, opening hours, prices, crowd levels | Claude ({MODEL}) general knowledge | Not live data and may be outdated. Each stop carries a confidence level. **Verify before booking.** |
| Coordinates on the map | Claude estimate | Approximate, for orientation only |
| Weather | Open-Meteo forecast API | Only available up to 16 days ahead |
| Fairness & score breakdowns | Computed in this app from your settings | Depend on the AI's interest tags for each stop |
| Transport times & costs | Claude estimate | Check live transit apps on the day |
""")
    st.subheader("📜 PDPA alignment")
    st.markdown("""
| Obligation | How this prototype handles it |
|---|---|
| Notification | A notice is shown before the first AI call |
| Consent | Separate toggles for AI generation and personalisation, not bundled into terms |
| Purpose limitation | Trip data is used only to plan this trip. No model training, no marketing |
| Transfer limitation | The AI provider processes data abroad, so a data processing agreement is required for production |
| Retention | Nothing is stored server-side. Session data is deleted when you close the tab or press *Clear all my data* |
| Access & correction | Everything you entered and everything sent is visible on this page |
""")
    st.subheader("🧾 AI call log")
    if ss.call_log:
        st.dataframe(pd.DataFrame(ss.call_log), hide_index=True, width="stretch")
    else:
        st.caption("No AI calls yet this session.")
    st.caption("Disclaimer: AI suggestions can be wrong. Routes or venues with little reliable information are flagged "
               "with ⚠️. Use your own judgement for safety.")


# ---------------------------------------------------------------- main

def gate():
    pw = ai.get_secret("APP_PASSWORD")
    if not pw or st.session_state.get("authed"):
        return
    st.title(f"🧭 {APP_NAME}")
    entered = st.text_input("Access code", type="password")
    if entered and entered == pw:
        st.session_state.authed = True
        st.rerun()
    elif entered:
        st.error("Wrong access code.")
    st.stop()


def main():
    ui.inject_css()
    gate()
    init()
    keep_widget_state()
    sidebar()
    header()
    page = st.session_state.nav
    if page == "Plan trip":
        plan_trip_page()
    elif page == "Itineraries":
        plan_tab()
        st.divider()
        replan_tab()
    elif page == "Explore":
        explore_tab()
    else:
        privacy_tab()


main()
