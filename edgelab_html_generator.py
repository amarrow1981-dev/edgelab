#!/usr/bin/env python3
"""
EdgeLab HTML Generator
-----------------------
Generates the complete public predictions HTML page from a predictions CSV.

Replaces the manual HTML build process entirely. One command, correct output,
no date errors, no manual data entry.

What it produces:
  - Tab 1: Predictions — sub-tabs per league
  - Tab 2: Gary's Picks — sub-tabs per acca type (result, safety, value, winner+btts, btts, upset)
  - Tab 3: Qualifying Picks — sub-tabs per acca type

Usage:
    python edgelab_html_generator.py predictions/2026-04-17_predictions.csv
    python edgelab_html_generator.py predictions/2026-04-17_predictions.csv --out public/gary_picks.html
    python edgelab_html_generator.py predictions/2026-04-17_predictions.csv --fold 5 --title "Weekend 17-20 Apr 2026"

Output:
    predictions/YYYY-MM-DD_predictions_public.html
"""

import argparse
import html
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Tier ordering and display names
# ---------------------------------------------------------------------------

TIER_ORDER = ["E0", "E1", "E2", "E3", "EC", "B1", "D1", "D2", "I1", "I2",
              "N1", "SC0", "SC1", "SC2", "SC3", "SP1", "SP2"]

TIER_NAMES = {
    "E0": "Premier League",
    "E1": "Championship",
    "E2": "League One",
    "E3": "League Two",
    "EC": "National League",
    "SP1": "La Liga",
    "SP2": "Segunda División",
    "D1":  "Bundesliga",
    "D2":  "2. Bundesliga",
    "I1":  "Serie A",
    "I2":  "Serie B",
    "N1":  "Eredivisie",
    "B1":  "Belgian First Division A",
    "SC0": "Scottish Premiership",
    "SC1": "Scottish Championship",
    "SC2": "Scottish League One",
    "SC3": "Scottish League Two",
}

ACCA_COLORS = {
    "result":      "var(--accent)",
    "safety":      "var(--accent)",
    "value":       "var(--green)",
    "winner_btts": "var(--purple)",
    "btts":        "var(--orange)",
    "upset":       "var(--red)",
}

ACCA_LABELS = {
    "result":      "Result Acca",
    "safety":      "Safety Acca",
    "value":       "Value Acca",
    "winner_btts": "Winner + BTTS",
    "btts":        "BTTS Acca",
    "upset":       "Upset Acca",
}

ACCA_ORDER = ["result", "safety", "value", "winner_btts", "btts", "upset"]

# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def parse_date(date_str: str) -> Optional[datetime]:
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except ValueError:
            continue
    return None


def format_date_short(date_str: str) -> str:
    dt = parse_date(date_str)
    if dt is None:
        return str(date_str)
    return dt.strftime("%a %#d %b") if sys.platform == "win32" else dt.strftime("%a %-d %b")


def format_date_medium(date_str: str) -> str:
    dt = parse_date(date_str)
    if dt is None:
        return str(date_str)
    return dt.strftime("%#d %b") if sys.platform == "win32" else dt.strftime("%-d %b")


def format_date_long(date_str: str) -> str:
    dt = parse_date(date_str)
    if dt is None:
        return str(date_str)
    return dt.strftime("%A %#d %B") if sys.platform == "win32" else dt.strftime("%A %-d %B")


def date_range_title(df: pd.DataFrame) -> str:
    dates = []
    for d in df["Date"].dropna():
        dt = parse_date(d)
        if dt:
            dates.append(dt)
    if not dates:
        return "Upcoming Fixtures"
    dates.sort()
    if dates[0].date() == dates[-1].date():
        return dates[0].strftime("%#d %B %Y") if sys.platform == "win32" else dates[0].strftime("%-d %B %Y")
    if dates[0].month == dates[-1].month:
        start = dates[0].strftime("%#d") if sys.platform == "win32" else dates[0].strftime("%-d")
        end = dates[-1].strftime("%#d %B %Y") if sys.platform == "win32" else dates[-1].strftime("%-d %B %Y")
        return f"{start}\u2013{end}"
    start = dates[0].strftime("%#d %b") if sys.platform == "win32" else dates[0].strftime("%-d %b")
    end = dates[-1].strftime("%#d %b %Y") if sys.platform == "win32" else dates[-1].strftime("%-d %b %Y")
    return f"{start}\u2013{end}"


# ---------------------------------------------------------------------------
# Confidence / chaos helpers
# ---------------------------------------------------------------------------

def conf_color(conf: float) -> str:
    if conf >= 0.65:
        return "var(--green)"
    elif conf >= 0.52:
        return "var(--accent)"
    return "var(--red)"


def conf_bar_color(conf: float) -> str:
    if conf >= 0.65:
        return "#c8f135"
    elif conf >= 0.52:
        return "#4a9bc4"
    return "#f13557"


def chaos_label(chaos: str) -> str:
    m = {"LOW": "Settled", "MED": "Mixed", "HIGH": "Unpredictable"}
    return m.get(str(chaos).upper(), chaos)


def chaos_color(chaos: str) -> str:
    m = {"LOW": "var(--green)", "MED": "var(--dim)", "HIGH": "var(--red)"}
    return m.get(str(chaos).upper(), "var(--dim)")


def h(text) -> str:
    return html.escape(str(text)) if text is not None else ""


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_predictions(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    float_cols = ["confidence", "dti", "odds_draw_prob", "h2h_draw_rate",
                  "draw_score", "btts_prob", "upset_score",
                  "B365H", "B365D", "B365A"]
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["upset_flag", "btts_flag"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    tier_rank = {t: i for i, t in enumerate(TIER_ORDER)}
    df["_tier_rank"] = df["tier"].map(tier_rank).fillna(99)
    df["_parsed_date"] = df["Date"].apply(lambda d: parse_date(d) or datetime(2099, 1, 1))
    df = df.sort_values(["_parsed_date", "_tier_rank"]).reset_index(drop=True)

    return df


def load_upset_notes(csv_path: str) -> dict:
    """Load companion upset notes JSON if it exists."""
    base = os.path.splitext(csv_path)[0]
    notes_path = base.replace("_predictions", "") + "_upset_notes.json"
    if not os.path.exists(notes_path):
        # Try same folder with date prefix
        folder = os.path.dirname(csv_path)
        date_prefix = os.path.basename(csv_path)[:10]
        notes_path = os.path.join(folder, f"{date_prefix}_upset_notes.json")
    if os.path.exists(notes_path):
        try:
            with open(notes_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


# ---------------------------------------------------------------------------
# Build accas
# ---------------------------------------------------------------------------

def build_accas(df: pd.DataFrame, fold: int = 5):
    try:
        from edgelab_acca import AccaBuilder, AccaConstraints
        builder = AccaBuilder(df)
        results = {}
        for acca_type in ACCA_ORDER:
            constraints = AccaConstraints(fold=fold, acca_type=acca_type)
            accas = builder.build(constraints=constraints, top_n=1)
            all_picks = builder.get_picks(constraints)
            results[acca_type] = {
                "acca": accas[0] if accas else None,
                "picks": all_picks,
            }
        return results
    except ImportError:
        print("  [HTML] edgelab_acca not available — acca tabs will be empty")
        return {}


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

CSS = """
:root{
  --bg:#060a0e;--surface:#0d1318;--border:rgba(74,155,196,0.15);
  --accent:#4a9bc4;--green:#c8f135;--orange:#f1a035;--red:#f13557;
  --purple:#a855f7;--text:#e8eef2;--muted:#4a6070;--dim:#7a8e9a;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{
  background:var(--bg);color:var(--text);
  font-family:'Barlow',sans-serif;font-weight:300;
  font-size:16px;line-height:1.6;
  padding:20px 14px 56px;
}
header{padding-bottom:18px;margin-bottom:22px;border-bottom:2px solid var(--accent)}
.logo{font-family:'Bebas Neue',sans-serif;font-size:32px;letter-spacing:.1em;color:var(--text);line-height:1}
.logo span{color:var(--accent)}
.tagline{font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);margin-top:4px}
.meta-row{margin-top:10px;font-size:13px;color:var(--dim);line-height:1.8}
.explainer{
  background:var(--surface);border-left:3px solid var(--accent);
  padding:14px 16px;margin-bottom:22px;
  font-size:15px;color:var(--dim);line-height:1.75;
}
.explainer strong{color:var(--text)}

/* ── Top-level tabs ── */
.tab-nav{
  display:flex;gap:0;margin-bottom:0;
  border-bottom:2px solid var(--border);
  overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;
}
.tab-nav::-webkit-scrollbar{display:none}
.tab-btn{
  background:none;border:none;color:var(--muted);
  font-family:'Barlow',sans-serif;font-size:12px;font-weight:600;
  letter-spacing:.2em;text-transform:uppercase;
  padding:13px 16px;cursor:pointer;
  border-bottom:2px solid transparent;margin-bottom:-2px;
  transition:color .15s;white-space:nowrap;flex-shrink:0;
  touch-action:manipulation;-webkit-tap-highlight-color:transparent;
  min-height:48px;user-select:none;-webkit-user-select:none;
}
.tab-btn:hover{color:var(--text)}
.tab-btn.active{color:var(--accent);border-bottom-color:var(--accent)}
.tab-panel{display:none;padding-top:20px}.tab-panel.active{display:block}

/* ── Sub-tabs (inside each main tab) ── */
.sub-nav{
  display:flex;gap:0;margin-bottom:20px;
  border-bottom:1px solid var(--border);
  overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;
  flex-wrap:nowrap;
}
.sub-nav::-webkit-scrollbar{display:none}
.sub-btn{
  background:none;border:none;color:var(--muted);
  font-family:'Barlow',sans-serif;font-size:11px;font-weight:600;
  letter-spacing:.15em;text-transform:uppercase;
  padding:10px 14px;cursor:pointer;
  border-bottom:2px solid transparent;margin-bottom:-1px;
  transition:color .12s;white-space:nowrap;flex-shrink:0;
  touch-action:manipulation;-webkit-tap-highlight-color:transparent;
  min-height:42px;user-select:none;-webkit-user-select:none;
}
.sub-btn:hover{color:var(--text)}
.sub-btn.active{color:var(--accent);border-bottom-color:var(--accent)}
.sub-panel{display:none}.sub-panel.active{display:block}

/* ── Search ── */
.search-wrap{margin-bottom:16px}
.search-wrap input{
  width:100%;background:var(--surface);
  border:1px solid var(--border);border-left:3px solid var(--accent);
  color:var(--text);font-family:'Barlow',sans-serif;
  font-size:16px;font-weight:300;
  padding:12px 16px;outline:none;-webkit-appearance:none;border-radius:0;
}
.search-wrap input::placeholder{color:var(--muted)}
.search-count{font-size:12px;color:var(--muted);margin-top:6px}

/* ── Legend ── */
.legend{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:18px}
.legend-item{font-size:14px;color:var(--dim);display:flex;align-items:center;gap:6px}
.legend-dot{width:9px;height:9px;border-radius:50%;flex-shrink:0}
.section-title{
  font-size:11px;font-weight:600;letter-spacing:.3em;text-transform:uppercase;
  color:var(--accent);margin-bottom:12px;margin-top:28px;
}
.section-title:first-child{margin-top:0}

/* ── Predictions table ── */
.table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{width:100%;border-collapse:collapse;min-width:420px}
th{
  text-align:left;font-size:11px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);padding:7px 10px;border-bottom:1px solid var(--border);
  font-weight:600;white-space:nowrap;
}
td{
  padding:9px 10px;border-bottom:1px solid rgba(74,155,196,.06);
  font-size:15px;color:var(--dim);vertical-align:middle;
}
tr:hover td{background:rgba(74,155,196,.04)}
tr.row-hidden{display:none}

/* ── League block ── */
.league-block{margin-bottom:28px}
.league-header{
  display:flex;align-items:center;gap:10px;
  padding:9px 0 8px;border-bottom:2px solid var(--accent);margin-bottom:0;
}
.league-accent-bar{width:3px;height:20px;background:var(--accent);flex-shrink:0;border-radius:1px}
.league-name{font-size:16px;font-weight:600;color:var(--text)}
.league-count{margin-left:auto;font-size:11px;color:var(--muted)}

/* ── Acca cards ── */
.acca-card{
  background:var(--surface);border:1px solid var(--border);
  border-top:3px solid var(--accent);padding:16px;margin-bottom:12px;
}
.acca-card.safety{border-top-color:var(--accent)}
.acca-card.value{border-top-color:var(--green)}
.acca-card.winner-btts{border-top-color:var(--purple)}
.acca-card.upset{border-top-color:var(--red)}
.acca-card.btts{border-top-color:var(--orange)}
.acca-type{font-size:11px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);margin-bottom:3px}
.acca-what{font-size:13px;color:var(--dim);margin-bottom:6px}
.acca-odds{
  font-family:'Bebas Neue',sans-serif;font-size:30px;
  letter-spacing:.05em;color:var(--accent);line-height:1;margin-bottom:5px;
}
.acca-card.value .acca-odds{color:var(--green)}
.acca-card.winner-btts .acca-odds{color:var(--purple)}
.acca-card.upset .acca-odds{color:var(--red)}
.acca-card.btts .acca-odds{color:var(--orange)}
.acca-comment{
  font-size:14px;color:var(--dim);font-style:italic;
  margin:10px 0 12px;padding-bottom:12px;
  border-bottom:1px solid var(--border);line-height:1.6;
}
.acca-pick{display:flex;align-items:flex-start;gap:10px;padding:9px 0;border-bottom:1px solid var(--border)}
.acca-pick:last-child{border-bottom:none}
.pick-num{color:var(--muted);min-width:18px;flex-shrink:0;font-size:13px;padding-top:2px}
.pick-body{flex:1}
.pick-team{color:var(--text);font-weight:600;font-size:16px}
.pick-detail{font-size:13px;color:var(--dim);margin-top:2px}
.pick-conf{font-family:'Bebas Neue',sans-serif;font-size:22px;color:var(--accent);flex-shrink:0}
.acca-card.value .pick-conf{color:var(--green)}
.acca-card.winner-btts .pick-conf{color:var(--purple)}
.acca-card.btts .pick-conf{color:var(--orange)}
.acca-card.upset .pick-conf{color:var(--red)}

/* ── Upset cards ── */
.upset-card{
  background:var(--surface);border:1px solid var(--border);
  border-left:4px solid var(--red);padding:16px;margin-bottom:14px;
}
.upset-match{font-size:17px;font-weight:600;color:var(--text);margin-bottom:3px}
.upset-meta{font-size:12px;color:var(--muted);letter-spacing:.08em;margin-bottom:10px}
.upset-summary{
  background:rgba(241,53,87,.07);border:1px solid rgba(241,53,87,.15);
  padding:10px 12px;margin-bottom:10px;font-size:14px;color:var(--dim);line-height:1.6;
}
.upset-summary strong{color:var(--text)}
.gary-label{font-size:10px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:var(--red);margin-bottom:6px}
.gary-text{font-size:15px;color:var(--dim);line-height:1.75}

/* ── Qualifying table ── */
.qual-section{margin-bottom:30px}
.qual-section-title{
  font-size:11px;font-weight:600;letter-spacing:.25em;text-transform:uppercase;
  padding:9px 0 7px;margin-bottom:10px;border-bottom:2px solid var(--border);
  display:flex;align-items:center;gap:10px;
}
.qual-section-title .qs-dot{width:9px;height:9px;border-radius:50%;flex-shrink:0}
.qual-count{font-size:11px;color:var(--muted);margin-left:auto;letter-spacing:0;text-transform:none}
.qual-table{width:100%;border-collapse:collapse;margin-top:0}
.qual-table th{
  text-align:left;font-size:11px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);padding:7px 10px;border-bottom:1px solid var(--border);
  font-weight:600;white-space:nowrap;
}
.qual-table td{
  padding:8px 10px;border-bottom:1px solid rgba(74,155,196,.06);
  font-size:14px;color:var(--dim);vertical-align:middle;
}
.qual-table td:first-child{color:var(--text);font-weight:600}
.qual-high{color:var(--green)}.qual-med{color:var(--dim)}

footer{
  border-top:1px solid var(--border);padding-top:18px;margin-top:40px;
  font-size:11px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);line-height:2.2;text-align:center;
}
"""

# ---------------------------------------------------------------------------
# JavaScript
# ---------------------------------------------------------------------------

JS = """
function switchTab(id) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  var panel = document.getElementById('tab-' + id);
  if (panel) panel.classList.add('active');
  document.querySelectorAll('[data-tab="' + id + '"]').forEach(b => b.classList.add('active'));
}

function switchSub(groupId, subId) {
  var group = document.getElementById(groupId);
  if (!group) return;
  group.querySelectorAll('.sub-panel').forEach(p => p.classList.remove('active'));
  group.querySelectorAll('.sub-btn').forEach(b => b.classList.remove('active'));
  var panel = document.getElementById(groupId + '-' + subId);
  if (panel) panel.classList.add('active');
  group.querySelectorAll('[data-sub="' + subId + '"]').forEach(b => b.classList.add('active'));
}

document.addEventListener('DOMContentLoaded', function() {
  var si = document.getElementById('searchInput');
  if (si) { si.addEventListener('input', filterMatches); si.addEventListener('keyup', filterMatches); }
});

function filterMatches(){
  var q = (document.getElementById('searchInput').value || '').toLowerCase().trim();
  var visible = 0;
  document.querySelectorAll('.league-block').forEach(function(block) {
    var leagueName = (block.querySelector('.league-name') ? block.querySelector('.league-name').textContent : '').toLowerCase();
    var leagueMatch = !q || leagueName.includes(q);
    var blockVisible = 0;
    block.querySelectorAll('tbody tr').forEach(function(r) {
      var rowText = (r.getAttribute('data-search') || '').toLowerCase();
      var show = !q || leagueMatch || rowText.includes(q);
      r.classList.toggle('row-hidden', !show);
      if (show) { visible++; blockVisible++; }
    });
    block.style.display = (blockVisible === 0 && q.length > 0) ? 'none' : '';
  });
  var sc = document.getElementById('searchCount');
  if (sc) sc.textContent = q ? visible + ' matches found' : '';
}
"""

# ---------------------------------------------------------------------------
# Predictions tab — sub-tab per league
# ---------------------------------------------------------------------------

def build_prediction_row(row: pd.Series) -> str:
    conf = float(row.get("confidence", 0) or 0)
    chaos = str(row.get("chaos_tier", "MED"))
    pred = str(row.get("prediction", "?"))
    home = h(row.get("HomeTeam", ""))
    away = h(row.get("AwayTeam", ""))
    tier = str(row.get("tier", ""))
    date_str = format_date_short(str(row.get("Date", "")))
    score = str(row.get("pred_scoreline", "?-?"))
    upset_flag = int(row.get("upset_flag", 0) or 0)

    pred_score_draw = 0
    try:
        parts = score.split("-")
        if len(parts) == 2 and parts[0].strip() == parts[1].strip():
            pred_score_draw = 1
    except Exception:
        pass

    if pred == "H":
        call = f"{home} to win"
    elif pred == "A":
        call = f"{away} to win"
    else:
        call = f"{home} vs {away} &mdash; Draw"

    bar_w = int(conf * 100)
    bar_color = conf_bar_color(conf)
    conf_pct = f"{conf:.0%}"
    chaos_lbl = chaos_label(chaos)
    chaos_col = chaos_color(chaos)

    score_cell = h(score)
    if pred_score_draw and pred != "D":
        score_cell += ' <span style="color:#f1a035;font-size:11px" title="Score model predicts a draw">~D</span>'

    upset_cell = '<span style="color:#f13557;font-weight:600">&#9888;</span>' if upset_flag else ""
    search = f"{home.lower()} {away.lower()} {tier.lower()} {TIER_NAMES.get(tier, '').lower()}"

    return (
        f'<tr data-search="{search}">'
        f'<td style="color:#4a6070;white-space:nowrap">{date_str}</td>'
        f'<td style="color:#e8eef2;font-weight:600">{home}</td>'
        f'<td style="color:#7a8e9a">vs {away}</td>'
        f'<td style="color:#e8eef2;white-space:nowrap">{call}</td>'
        f'<td style="white-space:nowrap">'
        f'<span style="display:inline-block;width:{bar_w}%;max-width:64px;height:3px;'
        f'background:{bar_color};vertical-align:middle;margin-right:5px;border-radius:1px"></span>'
        f'{conf_pct}</td>'
        f'<td style="color:{chaos_col};white-space:nowrap">{chaos_lbl}</td>'
        f'<td style="white-space:nowrap;color:#7a8e9a">{score_cell}</td>'
        f'<td>{upset_cell}</td>'
        f'</tr>\n'
    )


def build_predictions_tab(df: pd.DataFrame) -> str:
    tiers_in_data = df["tier"].unique()
    ordered_tiers = [t for t in TIER_ORDER if t in tiers_in_data]
    for t in tiers_in_data:
        if t not in ordered_tiers:
            ordered_tiers.append(t)

    lines = []
    lines.append('<div id="tab-predictions" class="tab-panel active">')

    # Search bar
    lines.append('<div class="search-wrap">')
    lines.append('  <input type="text" id="searchInput" placeholder="Search team or league..." '
                 'oninput="filterMatches()" onkeyup="filterMatches()"/>')
    lines.append('  <div class="search-count" id="searchCount"></div>')
    lines.append('</div>')

    # Legend
    lines.append('<div class="legend">')
    lines.append('  <div class="legend-item"><div class="legend-dot" style="background:#c8f135"></div>Settled</div>')
    lines.append('  <div class="legend-item"><div class="legend-dot" style="background:#7a8e9a"></div>Mixed</div>')
    lines.append('  <div class="legend-item"><div class="legend-dot" style="background:#f13557"></div>Unpredictable</div>')
    lines.append('  <div class="legend-item"><span style="color:#f13557;margin-right:4px">&#9888;</span>Upset warning</div>')
    lines.append('  <div class="legend-item"><span style="color:#f1a035;margin-right:4px">~D</span>Score says draw</div>')
    lines.append('</div>')

    # Sub-nav — one button per league
    lines.append('<div id="pred-subnav" class="sub-nav">')
    for i, tier in enumerate(ordered_tiers):
        active = ' active' if i == 0 else ''
        league_name = TIER_NAMES.get(tier, tier)
        n = len(df[df["tier"] == tier])
        lines.append(f'  <button class="sub-btn{active}" data-sub="{tier}" '
                     f'onclick="switchSub(\'pred-subnav-group\', \'{tier}\')">'
                     f'{h(league_name)} <span style="opacity:.5;font-size:10px">({n})</span></button>')
    lines.append('</div>')

    # Sub-panels — one per league
    lines.append('<div id="pred-subnav-group">')
    for i, tier in enumerate(ordered_tiers):
        active = ' active' if i == 0 else ''
        df_tier = df[df["tier"] == tier]
        if df_tier.empty:
            continue
        league_name = h(TIER_NAMES.get(tier, tier))
        count = len(df_tier)

        lines.append(f'<div id="pred-subnav-group-{tier}" class="sub-panel{active}">')
        lines.append(f'  <div class="league-block" data-tier="{tier}">')
        lines.append(f'    <div class="league-header">')
        lines.append(f'      <span class="league-accent-bar"></span>')
        lines.append(f'      <span class="league-name">{league_name}</span>')
        lines.append(f'      <span class="league-count">{count} match{"es" if count != 1 else ""}</span>')
        lines.append(f'    </div>')
        lines.append(f'    <div class="table-wrap">')
        lines.append(f'    <table><thead><tr>')
        lines.append(f'      <th>Date</th><th>Home</th><th>Away</th><th>Gary\'s Call</th>')
        lines.append(f'      <th>Confidence</th><th>Readable</th><th>Score</th><th></th>')
        lines.append(f'    </tr></thead><tbody>')

        for _, row in df_tier.iterrows():
            lines.append(build_prediction_row(row))

        lines.append(f'    </tbody></table>')
        lines.append(f'    </div>')
        lines.append(f'  </div>')
        lines.append(f'</div>')

    lines.append('</div><!-- end pred-subnav-group -->')
    lines.append('</div><!-- end tab-predictions -->')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Accas tab — sub-tab per acca type
# ---------------------------------------------------------------------------

def build_acca_card(acca_type: str, acca, df: pd.DataFrame) -> str:
    if acca is None:
        return ""

    color = ACCA_COLORS.get(acca_type, "var(--accent)")
    label = ACCA_LABELS.get(acca_type, acca_type)
    css_class = acca_type.replace("_", "-")
    odds_str = f"~{acca.combined_odds:.1f}/1" if acca.combined_odds else "&mdash;"

    lines = []
    lines.append(f'<div class="acca-card {css_class}">')
    lines.append(f'  <div class="acca-type">{label}</div>')
    lines.append(f'  <div class="acca-odds" style="color:{color}">{odds_str}</div>')
    lines.append(f'  <div class="acca-comment">"{h(acca.gary_comment)}"</div>')

    for i, pick in enumerate(acca.picks, 1):
        tier_name = TIER_NAMES.get(pick.tier, pick.tier)
        date_fmt = format_date_short(pick.date)
        conf_pct = f"{pick.confidence:.0%}"
        lines.append(f'  <div class="acca-pick">')
        lines.append(f'    <span class="pick-num">{i}.</span>')
        lines.append(f'    <div class="pick-body">')
        lines.append(f'      <div class="pick-team">{h(pick.selection_label)}</div>')
        lines.append(f'      <div class="pick-detail">{h(tier_name)} &middot; {date_fmt}</div>')
        lines.append(f'    </div>')
        lines.append(f'    <span class="pick-conf">{conf_pct}</span>')
        lines.append(f'  </div>')

    lines.append(f'</div>')
    return "\n".join(lines)


def build_upset_cards(df: pd.DataFrame, upset_notes: dict = None) -> str:
    upset_rows = df[
        (df.get("upset_flag", pd.Series(0, index=df.index)) == 1) &
        (df["confidence"] >= 0.60)
    ].sort_values("upset_score", ascending=False).head(8)

    if upset_rows.empty:
        return '<p style="font-size:15px;color:var(--dim)">No upset flags this round.</p>'

    if upset_notes is None:
        upset_notes = {}

    lines = []
    lines.append('<div class="section-title">Matches Gary Doesn\'t Fully Trust</div>')

    for _, row in upset_rows.iterrows():
        home = h(row.get("HomeTeam", ""))
        away = h(row.get("AwayTeam", ""))
        tier = str(row.get("tier", ""))
        tier_name = h(TIER_NAMES.get(tier, tier))
        date_raw = str(row.get("Date", ""))
        date_long = format_date_long(date_raw)
        date_med = format_date_medium(date_raw)
        pred = str(row.get("prediction", "?"))
        conf_pct = f"{float(row.get('confidence', 0)):.0%}"
        score = h(row.get("pred_scoreline", "?"))

        call_label = f"{home} to win" if pred == "H" else (f"{away} to win" if pred == "A" else "Draw")

        # Look up Gary's note
        note_key = f"{row.get('HomeTeam','')}_{row.get('AwayTeam','')}_{date_med}"
        gary_note = upset_notes.get(note_key, "")
        if not gary_note:
            # Try alternate key formats
            for k, v in upset_notes.items():
                if row.get('HomeTeam','') in k and row.get('AwayTeam','') in k:
                    gary_note = v
                    break

        if not gary_note:
            gary_note = ("High confidence call with an upset flag active. "
                         "Check H2H and recent form before including in any acca.")

        lines.append(f'<div class="upset-card">')
        lines.append(f'  <div class="upset-match">{home} vs {away}</div>')
        lines.append(f'  <div class="upset-meta">{tier_name} &mdash; {date_long}</div>')
        lines.append(f'  <div class="upset-summary">'
                     f'<strong>Gary\'s call:</strong> {call_label} &nbsp;&middot;&nbsp; '
                     f'<strong>Confidence:</strong> {conf_pct} &nbsp;&middot;&nbsp; '
                     f'<strong>Score model:</strong> {score}</div>')
        lines.append(f'  <div class="gary-label">Gary\'s Take</div>')
        lines.append(f'  <div class="gary-text">{h(gary_note)}</div>')
        lines.append(f'</div>')

    return "\n".join(lines)


def build_accas_tab(acca_data: dict, df: pd.DataFrame, upset_notes: dict = None) -> str:
    lines = []
    lines.append('<div id="tab-accas" class="tab-panel">')

    # Sub-nav — one per acca type
    lines.append('<div id="acca-subnav" class="sub-nav">')
    first = True
    for acca_type in ACCA_ORDER:
        data = acca_data.get(acca_type, {})
        acca = data.get("acca")
        label = ACCA_LABELS.get(acca_type, acca_type)
        active = ' active' if first else ''
        lines.append(f'  <button class="sub-btn{active}" data-sub="{acca_type}" '
                     f'onclick="switchSub(\'acca-subnav-group\', \'{acca_type}\')">'
                     f'{h(label)}</button>')
        first = False

    # Upset tab
    lines.append(f'  <button class="sub-btn" data-sub="upset-watch" '
                 f'onclick="switchSub(\'acca-subnav-group\', \'upset-watch\')">'
                 f'Upset Watch</button>')
    lines.append('</div>')

    lines.append('<div id="acca-subnav-group">')

    first = True
    for acca_type in ACCA_ORDER:
        data = acca_data.get(acca_type, {})
        acca = data.get("acca")
        active = ' active' if first else ''
        lines.append(f'<div id="acca-subnav-group-{acca_type}" class="sub-panel{active}">')
        if acca:
            lines.append(build_acca_card(acca_type, acca, df))
        else:
            lines.append(f'<p style="font-size:15px;color:var(--dim);padding:12px 0">No {ACCA_LABELS.get(acca_type,acca_type)} available this round.</p>')
        lines.append('</div>')
        first = False

    # Upset watch panel
    lines.append('<div id="acca-subnav-group-upset-watch" class="sub-panel">')
    lines.append(build_upset_cards(df, upset_notes))
    lines.append('</div>')

    lines.append('</div><!-- end acca-subnav-group -->')
    lines.append('</div><!-- end tab-accas -->')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Qualifying tab — sub-tab per acca type
# ---------------------------------------------------------------------------

def build_qual_picks_panel(acca_type: str, picks, color_var: str) -> str:
    if not picks:
        return f'<p style="font-size:15px;color:var(--dim);padding:12px 0">No qualifying picks.</p>'

    lines = []
    lines.append(f'  <div class="table-wrap">')

    if acca_type == "btts":
        lines.append(f'  <table class="qual-table"><thead><tr>'
                     f'<th>Date</th><th>Match</th><th>League</th><th>BTTS Prob</th><th>Chaos</th>'
                     f'</tr></thead><tbody>')
        for pick in picks:
            date_fmt = format_date_medium(pick.date)
            tier_name = h(TIER_NAMES.get(pick.tier, pick.tier))
            btts_pct = f"{pick.btts_prob:.0%}"
            match_str = h(f"{pick.home_team} vs {pick.away_team}")
            lines.append(f'    <tr>'
                         f'<td>{date_fmt}</td><td>{match_str}</td><td>{tier_name}</td>'
                         f'<td style="color:{color_var}">{btts_pct}</td><td>{pick.chaos_tier}</td>'
                         f'</tr>')

    elif acca_type == "upset":
        lines.append(f'  <table class="qual-table"><thead><tr>'
                     f'<th>Date</th><th>Pick</th><th>League</th><th>Conf</th><th>Upset Score</th>'
                     f'</tr></thead><tbody>')
        for pick in picks:
            date_fmt = format_date_medium(pick.date)
            tier_name = h(TIER_NAMES.get(pick.tier, pick.tier))
            conf_pct = f"{pick.confidence:.0%}"
            conf_cls = "qual-high" if pick.confidence >= 0.65 else "qual-med"
            lines.append(f'    <tr>'
                         f'<td>{date_fmt}</td><td>{h(pick.selection_label)}</td><td>{tier_name}</td>'
                         f'<td class="{conf_cls}">{conf_pct}</td>'
                         f'<td style="color:{color_var}">{pick.upset_score:.2f}</td>'
                         f'</tr>')

    elif acca_type == "winner_btts":
        lines.append(f'  <table class="qual-table"><thead><tr>'
                     f'<th>Date</th><th>Pick</th><th>League</th><th>Conf</th><th>Chaos</th><th>BTTS</th>'
                     f'</tr></thead><tbody>')
        for pick in picks:
            date_fmt = format_date_medium(pick.date)
            tier_name = h(TIER_NAMES.get(pick.tier, pick.tier))
            conf_pct = f"{pick.confidence:.0%}"
            conf_cls = "qual-high" if pick.confidence >= 0.65 else "qual-med"
            btts_pct = f"{pick.btts_prob:.0%}"
            lines.append(f'    <tr>'
                         f'<td>{date_fmt}</td><td>{h(pick.selection_label)}</td><td>{tier_name}</td>'
                         f'<td class="{conf_cls}">{conf_pct}</td><td>{pick.chaos_tier}</td>'
                         f'<td style="color:{color_var}">{btts_pct}</td>'
                         f'</tr>')

    elif acca_type == "value":
        lines.append(f'  <table class="qual-table"><thead><tr>'
                     f'<th>Date</th><th>Pick</th><th>League</th><th>Conf</th><th>Chaos</th><th>Edge vs Mkt</th>'
                     f'</tr></thead><tbody>')
        for pick in picks:
            date_fmt = format_date_medium(pick.date)
            tier_name = h(TIER_NAMES.get(pick.tier, pick.tier))
            conf_pct = f"{pick.confidence:.0%}"
            conf_cls = "qual-high" if pick.confidence >= 0.65 else "qual-med"
            edge_str = f"+{pick.edge:.0%}" if pick.edge is not None else "&mdash;"
            lines.append(f'    <tr>'
                         f'<td>{date_fmt}</td><td>{h(pick.selection_label)}</td><td>{tier_name}</td>'
                         f'<td class="{conf_cls}">{conf_pct}</td><td>{pick.chaos_tier}</td>'
                         f'<td style="color:{color_var}">{edge_str}</td>'
                         f'</tr>')

    else:
        # result / safety
        lines.append(f'  <table class="qual-table"><thead><tr>'
                     f'<th>Date</th><th>Pick</th><th>League</th><th>Conf</th><th>Chaos</th><th>Edge</th>'
                     f'</tr></thead><tbody>')
        for pick in picks:
            date_fmt = format_date_medium(pick.date)
            tier_name = h(TIER_NAMES.get(pick.tier, pick.tier))
            conf_pct = f"{pick.confidence:.0%}"
            conf_cls = "qual-high" if pick.confidence >= 0.65 else "qual-med"
            edge_str = f"+{pick.edge:.0%}" if pick.edge is not None else "&mdash;"
            lines.append(f'    <tr>'
                         f'<td>{date_fmt}</td><td>{h(pick.selection_label)}</td><td>{tier_name}</td>'
                         f'<td class="{conf_cls}">{conf_pct}</td><td>{pick.chaos_tier}</td>'
                         f'<td>{edge_str}</td>'
                         f'</tr>')

    lines.append(f'  </tbody></table>')
    lines.append(f'  </div>')
    return "\n".join(lines)


def build_qualifying_tab(acca_data: dict) -> str:
    lines = []
    lines.append('<div id="tab-qualifying" class="tab-panel">')

    lines.append('<div id="qual-subnav" class="sub-nav">')
    first = True
    for acca_type in ACCA_ORDER:
        label = ACCA_LABELS.get(acca_type, acca_type)
        active = ' active' if first else ''
        lines.append(f'  <button class="sub-btn{active}" data-sub="{acca_type}" '
                     f'onclick="switchSub(\'qual-subnav-group\', \'{acca_type}\')">'
                     f'{h(label)}</button>')
        first = False
    lines.append('</div>')

    lines.append('<div id="qual-subnav-group">')
    first = True
    for acca_type in ACCA_ORDER:
        data = acca_data.get(acca_type, {})
        picks = data.get("picks", [])
        color = ACCA_COLORS.get(acca_type, "var(--accent)")
        active = ' active' if first else ''
        n = len(picks)
        label = ACCA_LABELS.get(acca_type, acca_type)

        lines.append(f'<div id="qual-subnav-group-{acca_type}" class="sub-panel{active}">')
        lines.append(f'  <div class="qual-section-title">')
        lines.append(f'    <span class="qs-dot" style="background:{color}"></span>')
        lines.append(f'    <span style="color:{color}">{label}</span>')
        lines.append(f'    <span class="qual-count">{n} candidate{"s" if n != 1 else ""}</span>')
        lines.append(f'  </div>')
        lines.append(build_qual_picks_panel(acca_type, picks, color))
        lines.append('</div>')
        first = False

    lines.append('</div><!-- end qual-subnav-group -->')
    lines.append('</div><!-- end tab-qualifying -->')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Full page assembly
# ---------------------------------------------------------------------------

def generate_html(
    df: pd.DataFrame,
    acca_data: dict,
    upset_notes: dict = None,
    title_override: str = None,
    run_date: str = None,
) -> str:

    date_range = title_override or date_range_title(df)
    n_predictions = len(df)
    n_leagues = df["tier"].nunique()
    run_date_str = run_date or (
        datetime.today().strftime("%#d %B %Y") if sys.platform == "win32"
        else datetime.today().strftime("%-d %B %Y")
    )
    if upset_notes is None:
        upset_notes = {}

    lines = []
    lines.append('<!DOCTYPE html>')
    lines.append('<html lang="en">')
    lines.append('<head>')
    lines.append('<meta charset="UTF-8">')
    lines.append('<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0">')
    lines.append(f'<title>Gary\'s Picks \u2014 {h(date_range)}</title>')
    lines.append('<link rel="preconnect" href="https://fonts.googleapis.com">')
    lines.append('<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@300;400;600&display=swap" rel="stylesheet">')
    lines.append(f'<style>\n{CSS}\n</style>')
    lines.append('</head>')
    lines.append('<body>')
    lines.append('')
    lines.append('<header>')
    lines.append('  <div class="logo">Gary<span>Knows</span></div>')
    lines.append('  <div class="tagline">Powered by EdgeLab &mdash; Khaotikk Ltd</div>')
    lines.append(f'  <div class="meta-row">Fixtures: {h(date_range)} &nbsp;&middot;&nbsp; '
                 f'{n_predictions} predictions across {n_leagues} leagues</div>')
    lines.append('</header>')
    lines.append('')
    lines.append('<div class="explainer">')
    lines.append('  <strong>How to read this:</strong> Gary analyses recent form, head-to-head records, '
                 'and match data to call the most likely result. <strong>Confidence</strong> shows how '
                 'certain Gary is. <strong>Readable</strong> tells you how clear-cut the data is '
                 '&mdash; Settled means straightforward, Unpredictable means chaos. '
                 'A <strong style="color:#f13557">&#9888; Upset Warning</strong> means Gary is '
                 'confident but the data is also flagging that an upset is possible. '
                 '<strong style="color:#f1a035">~D</strong> on a score means the score model '
                 'thinks it could finish level.')
    lines.append('</div>')
    lines.append('')
    lines.append('<nav class="tab-nav">')
    lines.append('  <button class="tab-btn active" data-tab="predictions" onclick="switchTab(\'predictions\')">Predictions</button>')
    lines.append('  <button class="tab-btn" data-tab="accas" onclick="switchTab(\'accas\')">Gary\'s Picks</button>')
    lines.append('  <button class="tab-btn" data-tab="qualifying" onclick="switchTab(\'qualifying\')">All Candidates</button>')
    lines.append('</nav>')
    lines.append('')
    lines.append(build_predictions_tab(df))
    lines.append('')
    lines.append(build_accas_tab(acca_data, df, upset_notes))
    lines.append('')
    lines.append(build_qualifying_tab(acca_data))
    lines.append('')
    lines.append('<footer>')
    lines.append('  <div>GaryKnows &mdash; Powered by EdgeLab &mdash; Khaotikk Ltd</div>')
    lines.append('  <div>These are not betting tips. This is pattern recognition.</div>')
    lines.append(f'  <div>garyknows.com &mdash; {run_date_str}</div>')
    lines.append('</footer>')
    lines.append('')
    lines.append(f'<script>\n{JS}\n</script>')
    lines.append('</body>')
    lines.append('</html>')

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="EdgeLab HTML Generator — build the public predictions page"
    )
    parser.add_argument("predictions_csv", help="Path to predictions CSV from edgelab_predict.py")
    parser.add_argument("--out",   type=str, default=None,
                        help="Output path (default: same dir as CSV, _public.html suffix)")
    parser.add_argument("--fold",  type=int, default=5,
                        help="Acca fold size (default: 5)")
    parser.add_argument("--title", type=str, default=None,
                        help="Override date range title")
    args = parser.parse_args()

    if not os.path.exists(args.predictions_csv):
        print(f"\n  File not found: {args.predictions_csv}\n")
        sys.exit(1)

    print(f"\n  Loading predictions from {os.path.basename(args.predictions_csv)}...")
    df = load_predictions(args.predictions_csv)
    print(f"  {len(df)} predictions across {df['tier'].nunique()} tiers")

    print(f"  Loading upset notes...")
    upset_notes = load_upset_notes(args.predictions_csv)
    print(f"  {len(upset_notes)} upset notes loaded")

    print(f"  Building accas (fold={args.fold})...")
    acca_data = build_accas(df, fold=args.fold)
    for acca_type, data in acca_data.items():
        acca = data.get("acca")
        picks = data.get("picks", [])
        status = f"acca built ({len(acca.picks)} picks)" if acca else "no acca"
        print(f"    {acca_type:<15} {status}, {len(picks)} qualifying picks")

    print(f"  Generating HTML...")
    basename = os.path.basename(args.predictions_csv)
    run_date_str = basename[:10] if len(basename) >= 10 else None
    try:
        rd = datetime.strptime(run_date_str, "%Y-%m-%d")
        run_date_fmt = rd.strftime("%#d %B %Y") if sys.platform == "win32" else rd.strftime("%-d %B %Y")
    except Exception:
        run_date_fmt = None

    html_content = generate_html(
        df, acca_data, upset_notes=upset_notes,
        title_override=args.title, run_date=run_date_fmt
    )

    if args.out:
        out_path = args.out
    else:
        base = os.path.splitext(args.predictions_csv)[0]
        out_path = base + "_public.html"

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    size_kb = os.path.getsize(out_path) / 1024
    print(f"\n  HTML saved: {out_path}  ({size_kb:.0f} KB)")
    print(f"  Deploy to Netlify and share the URL.\n")


if __name__ == "__main__":
    main()
