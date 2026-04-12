#!/usr/bin/env python3
"""
EdgeLab HTML Generator
-----------------------
Generates the complete public predictions HTML page from a predictions CSV.

Replaces the manual HTML build process entirely. One command, correct output,
no date errors, no manual data entry.

What it produces:
  - Tab 1: All Predictions — every fixture grouped by league, confidence bar,
            chaos tier, score prediction, upset flag, ~D flag
  - Tab 2: Gary's Picks — acca cards (result, safety, value, winner+btts,
            btts, upset) with Gary's comments and qualifying picks lists
  - Tab 3: Qualifying Picks — full candidate lists per acca type

Usage:
    python edgelab_html_generator.py predictions/2026-04-12_predictions.csv
    python edgelab_html_generator.py predictions/2026-04-12_predictions.csv --out public/gary_picks.html
    python edgelab_html_generator.py predictions/2026-04-12_predictions.csv --fold 5 --title "Weekend 12-14 Apr 2026"

Output:
    predictions/YYYY-MM-DD_predictions_public.html
"""

import argparse
import html
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
    "winner_btts": "Winner + Both Teams to Score",
    "btts":        "BTTS Acca",
    "upset":       "Upset Acca",
}

# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def parse_date(date_str: str) -> Optional[datetime]:
    """Parse DD/MM/YYYY or YYYY-MM-DD date string."""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except ValueError:
            continue
    return None


def format_date_short(date_str: str) -> str:
    """DD/MM/YYYY -> 'Sat 12 Apr'"""
    dt = parse_date(date_str)
    if dt is None:
        return str(date_str)
    return dt.strftime("%a %-d %b") if sys.platform != "win32" else dt.strftime("%a %#d %b")


def format_date_medium(date_str: str) -> str:
    """DD/MM/YYYY -> '12 Apr'"""
    dt = parse_date(date_str)
    if dt is None:
        return str(date_str)
    return dt.strftime("%-d %b") if sys.platform != "win32" else dt.strftime("%#d %b")


def format_date_long(date_str: str) -> str:
    """DD/MM/YYYY -> 'Saturday 12 April'"""
    dt = parse_date(date_str)
    if dt is None:
        return str(date_str)
    return dt.strftime("%A %-d %B") if sys.platform != "win32" else dt.strftime("%A %#d %B")


def date_range_title(df: pd.DataFrame) -> str:
    """Build a date range string from the predictions dataframe."""
    dates = []
    for d in df["Date"].dropna():
        dt = parse_date(d)
        if dt:
            dates.append(dt)
    if not dates:
        return "Upcoming Fixtures"
    dates.sort()
    if dates[0].date() == dates[-1].date():
        return dates[0].strftime("%-d %B %Y") if sys.platform != "win32" else dates[0].strftime("%#d %B %Y")
    if dates[0].month == dates[-1].month:
        start = dates[0].strftime("%-d") if sys.platform != "win32" else dates[0].strftime("%#d")
        end = dates[-1].strftime("%-d %B %Y") if sys.platform != "win32" else dates[-1].strftime("%#d %B %Y")
        return f"{start}\u2013{end}"
    start = dates[0].strftime("%-d %b") if sys.platform != "win32" else dates[0].strftime("%#d %b")
    end = dates[-1].strftime("%-d %b %Y") if sys.platform != "win32" else dates[-1].strftime("%#d %b %Y")
    return f"{start}\u2013{end}"


# ---------------------------------------------------------------------------
# Confidence colour helper
# ---------------------------------------------------------------------------

def conf_color(conf: float) -> str:
    if conf >= 0.65:
        return "var(--green)"
    elif conf >= 0.52:
        return "var(--accent)"
    else:
        return "var(--red)"


def conf_bar_color(conf: float) -> str:
    if conf >= 0.65:
        return "#c8f135"
    elif conf >= 0.52:
        return "#4a9bc4"
    else:
        return "#f13557"


def chaos_label(chaos: str) -> str:
    m = {"LOW": "Settled", "MED": "Mixed", "HIGH": "Unpredictable"}
    return m.get(str(chaos).upper(), chaos)


def chaos_color(chaos: str) -> str:
    m = {"LOW": "var(--green)", "MED": "var(--dim)", "HIGH": "var(--red)"}
    return m.get(str(chaos).upper(), "var(--dim)")


def h(text) -> str:
    """HTML-escape a value."""
    return html.escape(str(text)) if text is not None else ""


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_predictions(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    # Normalise columns
    float_cols = ["confidence", "dti", "odds_draw_prob", "h2h_draw_rate",
                  "draw_score", "btts_prob", "upset_score",
                  "B365H", "B365D", "B365A"]
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["upset_flag", "btts_flag"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Sort by date then tier order
    tier_rank = {t: i for i, t in enumerate(TIER_ORDER)}
    df["_tier_rank"] = df["tier"].map(tier_rank).fillna(99)
    df["_parsed_date"] = df["Date"].apply(lambda d: parse_date(d) or datetime(2099, 1, 1))
    df = df.sort_values(["_parsed_date", "_tier_rank"]).reset_index(drop=True)

    return df


# ---------------------------------------------------------------------------
# Build accas using existing AccaBuilder
# ---------------------------------------------------------------------------

def build_accas(df: pd.DataFrame, fold: int = 5):
    """Run AccaBuilder and return dict of acca type -> Acca object."""
    try:
        from edgelab_acca import AccaBuilder, AccaConstraints
        builder = AccaBuilder(df)
        results = {}
        for acca_type in ["result", "safety", "value", "winner_btts", "btts", "upset"]:
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
# HTML sections
# ---------------------------------------------------------------------------

CSS = """
:root{--bg:#060a0e;--surface:#0d1318;--border:rgba(74,155,196,0.15);--accent:#4a9bc4;--green:#c8f135;--orange:#f1a035;--red:#f13557;--purple:#a855f7;--text:#e8eef2;--muted:#4a6070;--dim:#7a8e9a}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:'Barlow',sans-serif;font-weight:300;font-size:14px;line-height:1.5;padding:18px 12px 48px}
header{padding-bottom:16px;margin-bottom:20px;border-bottom:2px solid var(--accent)}
.logo{font-family:'Bebas Neue',sans-serif;font-size:28px;letter-spacing:.1em;color:var(--text);line-height:1}
.logo span{color:var(--accent)}
.tagline{font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);margin-top:3px}
.meta-row{margin-top:8px;font-size:12px;color:var(--dim);line-height:1.8}
.explainer{background:var(--surface);border-left:3px solid var(--accent);padding:12px 14px;margin-bottom:20px;font-size:13px;color:var(--dim);line-height:1.7}
.explainer strong{color:var(--text)}
.section-title{font-size:10px;font-weight:600;letter-spacing:.3em;text-transform:uppercase;color:var(--accent);margin-bottom:10px;margin-top:24px}
.acca-card{background:var(--surface);border:1px solid var(--border);border-top:3px solid var(--accent);padding:14px;margin-bottom:10px}
.acca-card.safety{border-top-color:var(--accent)}.acca-card.value{border-top-color:var(--green)}.acca-card.winner-btts{border-top-color:var(--purple)}.acca-card.upset{border-top-color:var(--red)}.acca-card.btts{border-top-color:var(--orange)}
.acca-type{font-size:10px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);margin-bottom:2px}
.acca-what{font-size:12px;color:var(--dim);margin-bottom:5px}
.acca-odds{font-family:'Bebas Neue',sans-serif;font-size:26px;letter-spacing:.05em;color:var(--accent);line-height:1;margin-bottom:4px}
.acca-card.value .acca-odds{color:var(--green)}.acca-card.winner-btts .acca-odds{color:var(--purple)}.acca-card.upset .acca-odds{color:var(--red)}.acca-card.btts .acca-odds{color:var(--orange)}
.acca-comment{font-size:12px;color:var(--dim);font-style:italic;margin:8px 0 10px;padding-bottom:10px;border-bottom:1px solid var(--border);line-height:1.5}
.acca-pick{display:flex;align-items:flex-start;gap:8px;padding:7px 0;border-bottom:1px solid var(--border)}
.acca-pick:last-child{border-bottom:none}
.pick-num{color:var(--muted);min-width:16px;flex-shrink:0;font-size:11px;padding-top:2px}
.pick-body{flex:1}
.pick-team{color:var(--text);font-weight:600;font-size:14px}
.pick-detail{font-size:11px;color:var(--dim);margin-top:1px}
.pick-conf{font-family:'Bebas Neue',sans-serif;font-size:18px;color:var(--accent);flex-shrink:0}
.acca-card.value .pick-conf{color:var(--green)}.acca-card.winner-btts .pick-conf{color:var(--purple)}.acca-card.btts .pick-conf{color:var(--orange)}.acca-card.upset .pick-conf{color:var(--red)}
.upset-card{background:var(--surface);border:1px solid var(--border);border-left:4px solid var(--red);padding:14px;margin-bottom:12px}
.upset-match{font-size:15px;font-weight:600;color:var(--text);margin-bottom:2px}
.upset-meta{font-size:11px;color:var(--muted);letter-spacing:.08em;margin-bottom:8px}
.upset-summary{background:rgba(241,53,87,.07);border:1px solid rgba(241,53,87,.15);padding:8px 10px;margin-bottom:8px;font-size:12px;color:var(--dim);line-height:1.6}
.upset-summary strong{color:var(--text)}
.gary-label{font-size:9px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:var(--red);margin-bottom:5px}
.gary-text{font-size:13px;color:var(--dim);line-height:1.7}
.tab-nav{display:flex;gap:0;margin-bottom:24px;border-bottom:2px solid var(--border);overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none}
.tab-nav::-webkit-scrollbar{display:none}
.tab-btn{background:none;border:none;color:var(--muted);font-family:'Barlow',sans-serif;font-size:11px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;padding:12px 14px;cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-2px;transition:color .15s;white-space:nowrap;flex-shrink:0;touch-action:manipulation;-webkit-tap-highlight-color:transparent;min-height:44px;user-select:none;-webkit-user-select:none}
.tab-btn:hover{color:var(--text)}
.tab-btn.active{color:var(--accent);border-bottom-color:var(--accent)}
.tab-panel{display:none}.tab-panel.active{display:block}
.search-wrap{margin-bottom:14px;margin-top:0}
.search-wrap input{width:100%;background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--accent);color:var(--text);font-family:'Barlow',sans-serif;font-size:15px;font-weight:300;padding:11px 14px;outline:none;-webkit-appearance:none;border-radius:0}
.search-wrap input::placeholder{color:var(--muted)}
.search-count{font-size:11px;color:var(--muted);margin-top:5px}
.qual-section{margin-bottom:28px}
.qual-section-title{font-size:10px;font-weight:600;letter-spacing:.25em;text-transform:uppercase;padding:8px 0 6px;margin-bottom:8px;border-bottom:2px solid var(--border);display:flex;align-items:center;gap:8px}
.qual-section-title .qs-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.qual-count{font-size:10px;color:var(--muted);margin-left:auto;letter-spacing:0;text-transform:none}
.qual-table{width:100%;border-collapse:collapse;margin-top:0}
.qual-table th{text-align:left;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);padding:6px 8px;border-bottom:1px solid var(--border);font-weight:600;white-space:nowrap}
.qual-table td{padding:7px 8px;border-bottom:1px solid rgba(74,155,196,.06);font-size:12px;color:var(--dim);vertical-align:middle}
.qual-table td:first-child{color:var(--text);font-weight:600}
.qual-high{color:var(--green)}.qual-med{color:var(--dim)}
.legend{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:16px}
.legend-item{font-size:12px;color:var(--dim);display:flex;align-items:center;gap:5px}
.legend-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.league-block{margin-bottom:24px}.league-block.hidden{display:none}
.league-header{display:flex;align-items:center;gap:10px;padding:8px 0 7px;border-bottom:2px solid var(--accent);margin-bottom:0}
.league-accent-bar{width:3px;height:18px;background:var(--accent);flex-shrink:0;border-radius:1px}
.league-name{font-size:14px;font-weight:600;color:var(--text)}
.league-count{margin-left:auto;font-size:10px;color:var(--muted)}
.table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{width:100%;border-collapse:collapse;min-width:400px}
th{text-align:left;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);padding:6px 8px;border-bottom:1px solid var(--border);font-weight:600;white-space:nowrap}
td{padding:7px 8px;border-bottom:1px solid rgba(74,155,196,.06);font-size:13px;color:var(--dim);vertical-align:middle}
tr:hover td{background:rgba(74,155,196,.04)}
tr.row-hidden{display:none}
footer{border-top:1px solid var(--border);padding-top:16px;margin-top:36px;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);line-height:2;text-align:center}
"""

JS = """
function switchTab(id) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  var panel = document.getElementById('tab-' + id);
  if (panel) panel.classList.add('active');
  document.querySelectorAll('[data-tab="' + id + '"]').forEach(b => b.classList.add('active'));
  if (id !== 'predictions') {
    var sc = document.getElementById('searchCount');
    if (sc) sc.textContent = '';
  }
}

document.addEventListener('DOMContentLoaded', function() {
  var searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('input', filterMatches);
    searchInput.addEventListener('keyup', filterMatches);
  }
});

function filterMatches(){
  const q = document.getElementById('searchInput').value.toLowerCase().trim();
  let visible = 0;

  document.querySelectorAll('#tab-predictions .league-block').forEach(function(block) {
    const leagueName = (block.querySelector('.league-name') ? block.querySelector('.league-name').textContent : '').toLowerCase();
    const leagueCode = (block.querySelector('.league-code') ? block.querySelector('.league-code').textContent : '').toLowerCase();
    const leagueMatch = !q || leagueName.includes(q) || leagueCode.includes(q);

    let blockVisible = 0;
    block.querySelectorAll('tbody tr').forEach(function(r) {
      const rowText = (r.getAttribute('data-search') || '').toLowerCase();
      const show = !q || leagueMatch || rowText.includes(q);
      r.classList.toggle('row-hidden', !show);
      if (show) { visible++; blockVisible++; }
    });

    block.classList.toggle('hidden', blockVisible === 0 && q.length > 0);
  });

  document.getElementById('searchCount').textContent = q ? visible + ' matches found' : '';
}
"""


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
    # Check if score prediction is a draw (equal goals in pred_scoreline)
    try:
        parts = score.split("-")
        if len(parts) == 2 and parts[0].strip() == parts[1].strip():
            pred_score_draw = 1
    except Exception:
        pass

    # Call label
    if pred == "H":
        call = f"{home} to win"
    elif pred == "A":
        call = f"{away} to win"
    else:
        call = f"{home} vs {away} &mdash; Draw"

    # Confidence bar
    bar_w = int(conf * 100)
    bar_color = conf_bar_color(conf)
    conf_pct = f"{conf:.0%}"
    chaos_lbl = chaos_label(chaos)
    chaos_col = chaos_color(chaos)

    # Score cell — add ~D flag if score is a draw and pred isn't D
    score_cell = h(score)
    if pred_score_draw and pred != "D":
        score_cell += ' <span style="color:#f1a035;font-size:10px" title="Score model predicts a draw">~D</span>'

    # Upset flag cell
    upset_cell = '<span style="color:#f13557;font-weight:600">&#9888;</span>' if upset_flag else ""

    # Search data
    search = f"{home.lower()} {away.lower()} {tier.lower()} {TIER_NAMES.get(tier, '').lower()}"

    return (
        f'<tr data-search="{search}">'
        f'<td style="color:#4a6070;white-space:nowrap">{date_str}</td>'
        f'<td style="color:#e8eef2;font-weight:600">{home}</td>'
        f'<td style="color:#7a8e9a">vs {away}</td>'
        f'<td style="color:#e8eef2;white-space:nowrap">{call}</td>'
        f'<td style="white-space:nowrap">'
        f'<span style="display:inline-block;width:{bar_w}%;max-width:60px;height:3px;'
        f'background:{bar_color};vertical-align:middle;margin-right:4px;border-radius:1px"></span>'
        f'{conf_pct}</td>'
        f'<td style="color:{chaos_col};white-space:nowrap">{chaos_lbl}</td>'
        f'<td style="white-space:nowrap;color:#7a8e9a">{score_cell}</td>'
        f'<td>{upset_cell}</td>'
        f'</tr>\n'
    )


def build_predictions_tab(df: pd.DataFrame) -> str:
    lines = []
    lines.append('<div id="tab-predictions" class="tab-panel active">')
    lines.append('<div class="search-wrap">')
    lines.append('  <input type="text" id="searchInput" placeholder="Search by team or league..." '
                 'oninput="filterMatches()" onkeyup="filterMatches()" onchange="filterMatches()"/>')
    lines.append('  <div class="search-count" id="searchCount"></div>')
    lines.append('</div>')
    lines.append('<div class="section-title">All Predictions</div>')
    lines.append('<div class="legend">')
    lines.append('  <div class="legend-item"><div class="legend-dot" style="background:#c8f135"></div> Settled &mdash; data is clear</div>')
    lines.append('  <div class="legend-item"><div class="legend-dot" style="background:#7a8e9a"></div> Mixed &mdash; some uncertainty</div>')
    lines.append('  <div class="legend-item"><div class="legend-dot" style="background:#f13557"></div> Unpredictable &mdash; hard to read</div>')
    lines.append('  <div class="legend-item"><span style="color:#f13557;margin-right:3px">&#9888;</span> Upset warning</div>')
    lines.append('  <div class="legend-item"><span style="color:#f1a035;margin-right:3px">~D</span> Score model says draw</div>')
    lines.append('</div>')
    lines.append('')

    # Group by tier in defined order
    tiers_in_data = df["tier"].unique()
    ordered_tiers = [t for t in TIER_ORDER if t in tiers_in_data]
    # Add any tiers not in TIER_ORDER at the end
    for t in tiers_in_data:
        if t not in ordered_tiers:
            ordered_tiers.append(t)

    for tier in ordered_tiers:
        df_tier = df[df["tier"] == tier]
        if df_tier.empty:
            continue
        league_name = h(TIER_NAMES.get(tier, tier))
        count = len(df_tier)

        lines.append(f'<div class="league-block" data-tier="{tier}">')
        lines.append(f'  <div class="league-header">')
        lines.append(f'    <span class="league-accent-bar"></span>')
        lines.append(f'    <span class="league-name">{league_name}</span>')
        lines.append(f'    <span class="league-count">{count} match{"es" if count != 1 else ""}</span>')
        lines.append(f'  </div>')
        lines.append(f'  <div class="table-wrap">')
        lines.append(f'  <table><thead><tr>')
        lines.append(f'    <th>Date</th><th>Home Team</th><th>Away Team</th><th>Gary\'s Call</th>')
        lines.append(f'    <th>Confidence</th><th>How Readable</th><th>Score</th><th></th>')
        lines.append(f'  </tr></thead><tbody>')

        for _, row in df_tier.iterrows():
            lines.append(build_prediction_row(row))

        lines.append(f'  </tbody></table>')
        lines.append(f'  </div>')
        lines.append(f'</div>')

    lines.append('</div><!-- end tab-predictions -->')
    return "\n".join(lines)


def build_acca_card(acca_type: str, acca, df: pd.DataFrame) -> str:
    if acca is None:
        return ""

    color = ACCA_COLORS.get(acca_type, "var(--accent)")
    label = ACCA_LABELS.get(acca_type, acca_type)
    css_class = acca_type.replace("_", "-")

    odds_str = f"~{acca.combined_odds:.1f}/1" if acca.combined_odds else "&mdash; (no odds)"

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


def build_upset_cards(df: pd.DataFrame) -> str:
    """Build Gary's upset warning cards for high-confidence upset-flagged matches."""
    upset_rows = df[
        (df.get("upset_flag", pd.Series(0, index=df.index)) == 1) &
        (df["confidence"] >= 0.60)
    ].sort_values("upset_score", ascending=False).head(5)

    if upset_rows.empty:
        return ""

    lines = []
    lines.append('<div class="section-title">Gary\'s Take &mdash; Matches He Doesn\'t Trust</div>')
    lines.append('<p style="font-size:13px;color:var(--dim);margin-bottom:14px;line-height:1.6;">'
                 'Gary made a confident call on these but the data is also flagging caution.</p>')

    for _, row in upset_rows.iterrows():
        home = h(row.get("HomeTeam", ""))
        away = h(row.get("AwayTeam", ""))
        tier = str(row.get("tier", ""))
        tier_name = h(TIER_NAMES.get(tier, tier))
        date_long = format_date_long(str(row.get("Date", "")))
        pred = str(row.get("prediction", "?"))
        conf_pct = f"{float(row.get('confidence', 0)):.0%}"
        score = h(row.get("pred_scoreline", "?"))

        if pred == "H":
            call_label = f"{home} to win"
        elif pred == "A":
            call_label = f"{away} to win"
        else:
            call_label = "Draw"

        lines.append(f'<div class="upset-card">')
        lines.append(f'  <div class="upset-match">{home} vs {away}</div>')
        lines.append(f'  <div class="upset-meta">{tier_name} &mdash; {date_long}</div>')
        lines.append(f'  <div class="upset-summary">'
                     f'<strong>Gary\'s call:</strong> {call_label} &nbsp;&middot;&nbsp; '
                     f'<strong>Confidence:</strong> {conf_pct} &nbsp;&middot;&nbsp; '
                     f'<strong>Score model:</strong> {score}</div>')
        lines.append(f'  <div class="gary-label">Upset Warning</div>')
        lines.append(f'  <div class="gary-text">High confidence call with an upset flag active. '
                     f'Check H2H and form before including in any acca.</div>')
        lines.append(f'</div>')

    return "\n".join(lines)


def build_accas_tab(acca_data: dict, df: pd.DataFrame) -> str:
    lines = []
    lines.append('<div id="tab-accas" class="tab-panel">')
    lines.append('<div class="section-title">Gary\'s Accumulator Picks</div>')
    lines.append('<div class="acca-grid">')
    lines.append('')

    for acca_type in ["result", "safety", "value", "winner_btts", "btts", "upset"]:
        data = acca_data.get(acca_type, {})
        acca = data.get("acca")
        if acca:
            lines.append(build_acca_card(acca_type, acca, df))
            lines.append('')

    lines.append('</div>')
    lines.append('')

    # Upset warning cards
    lines.append(build_upset_cards(df))

    lines.append('')
    lines.append('</div><!-- end tab-accas -->')
    return "\n".join(lines)


def build_qual_section_result(acca_type: str, picks, color_var: str, label: str) -> str:
    if not picks:
        return ""

    n = len(picks)
    lines = []
    lines.append(f'<div class="qual-section">')
    lines.append(f'  <div class="qual-section-title">')
    lines.append(f'    <span class="qs-dot" style="background:{color_var}"></span>')
    lines.append(f'    <span style="color:{color_var}">{label}</span>')
    lines.append(f'    <span class="qual-count">{n} candidate{"s" if n != 1 else ""}</span>')
    lines.append(f'  </div>')
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
                         f'<td>{date_fmt}</td>'
                         f'<td>{match_str}</td>'
                         f'<td>{tier_name}</td>'
                         f'<td style="color:{color_var}">{btts_pct}</td>'
                         f'<td>{pick.chaos_tier}</td>'
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
            upset_str = f"{pick.upset_score:.2f}"
            lines.append(f'    <tr>'
                         f'<td>{date_fmt}</td>'
                         f'<td>{h(pick.selection_label)}</td>'
                         f'<td>{tier_name}</td>'
                         f'<td class="{conf_cls}">{conf_pct}</td>'
                         f'<td style="color:{color_var}">{upset_str}</td>'
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
                         f'<td>{date_fmt}</td>'
                         f'<td>{h(pick.selection_label)}</td>'
                         f'<td>{tier_name}</td>'
                         f'<td class="{conf_cls}">{conf_pct}</td>'
                         f'<td>{pick.chaos_tier}</td>'
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
            edge_color = f'style="color:{color_var}"' if pick.edge is not None else ""
            lines.append(f'    <tr>'
                         f'<td>{date_fmt}</td>'
                         f'<td>{h(pick.selection_label)}</td>'
                         f'<td>{tier_name}</td>'
                         f'<td class="{conf_cls}">{conf_pct}</td>'
                         f'<td>{pick.chaos_tier}</td>'
                         f'<td {edge_color}>{edge_str}</td>'
                         f'</tr>')

    else:
        # result / safety — confidence + chaos + edge
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
                         f'<td>{date_fmt}</td>'
                         f'<td>{h(pick.selection_label)}</td>'
                         f'<td>{tier_name}</td>'
                         f'<td class="{conf_cls}">{conf_pct}</td>'
                         f'<td>{pick.chaos_tier}</td>'
                         f'<td>{edge_str}</td>'
                         f'</tr>')

    lines.append(f'  </tbody></table>')
    lines.append(f'  </div>')
    lines.append(f'</div>')
    return "\n".join(lines)


def build_qualifying_tab(acca_data: dict) -> str:
    sections = [
        ("result",      "var(--accent)",  "Result Acca"),
        ("safety",      "var(--accent)",  "Safety Acca"),
        ("value",       "var(--green)",   "Value Acca"),
        ("winner_btts", "var(--purple)",  "Winner + BTTS"),
        ("btts",        "var(--orange)",  "BTTS Acca"),
        ("upset",       "var(--red)",     "Upset Acca"),
    ]

    lines = []
    lines.append('<div id="tab-qualifying" class="tab-panel">')

    for acca_type, color, label in sections:
        data = acca_data.get(acca_type, {})
        picks = data.get("picks", [])
        section = build_qual_section_result(acca_type, picks, color, label)
        if section:
            lines.append(section)

    lines.append('</div><!-- end tab-qualifying -->')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Full page assembly
# ---------------------------------------------------------------------------

def generate_html(
    df: pd.DataFrame,
    acca_data: dict,
    title_override: str = None,
    run_date: str = None,
) -> str:

    date_range = title_override or date_range_title(df)
    n_predictions = len(df)
    n_leagues = df["tier"].nunique()
    run_date_str = run_date or datetime.today().strftime("%-d %B %Y") if sys.platform != "win32" else datetime.today().strftime("%#d %B %Y")

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
                 'certain Gary is. <strong>How Readable</strong> tells you how clear-cut the data is '
                 '&mdash; Settled means straightforward, Unpredictable means the data is all over the '
                 'place. A <strong style="color:#f13557">&#9888; Upset Warning</strong> means Gary is '
                 'confident but the data is also flagging that an upset is possible. The '
                 '<strong style="color:#f1a035">~D</strong> flag on a score means the score model '
                 'thinks it could be a draw even where Gary calls a winner &mdash; watch those ones.')
    lines.append('</div>')
    lines.append('')
    lines.append('<nav class="tab-nav">')
    lines.append('  <button class="tab-btn active" data-tab="predictions" onclick="switchTab(\'predictions\')">All Predictions</button>')
    lines.append('  <button class="tab-btn" data-tab="accas" onclick="switchTab(\'accas\')">Gary\'s Picks</button>')
    lines.append('  <button class="tab-btn" data-tab="qualifying" onclick="switchTab(\'qualifying\')">Qualifying Picks</button>')
    lines.append('</nav>')
    lines.append('')

    # Tabs — accas first in DOM (hidden), predictions second (active)
    lines.append(build_accas_tab(acca_data, df))
    lines.append('')
    lines.append(build_predictions_tab(df))
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
                        help="Override date range title e.g. 'Weekend 12-14 Apr 2026'")
    args = parser.parse_args()

    if not os.path.exists(args.predictions_csv):
        print(f"\n  File not found: {args.predictions_csv}\n")
        sys.exit(1)

    print(f"\n  Loading predictions from {os.path.basename(args.predictions_csv)}...")
    df = load_predictions(args.predictions_csv)
    print(f"  {len(df)} predictions across {df['tier'].nunique()} tiers")

    print(f"  Building accas (fold={args.fold})...")
    acca_data = build_accas(df, fold=args.fold)
    for acca_type, data in acca_data.items():
        acca = data.get("acca")
        picks = data.get("picks", [])
        status = f"acca built ({len(acca.picks)} picks)" if acca else "no acca"
        print(f"    {acca_type:<15} {status}, {len(picks)} qualifying picks")

    print(f"  Generating HTML...")
    # Run date from CSV filename if possible
    basename = os.path.basename(args.predictions_csv)
    run_date_str = basename[:10] if len(basename) >= 10 else None
    try:
        rd = datetime.strptime(run_date_str, "%Y-%m-%d")
        run_date_fmt = rd.strftime("%-d %B %Y") if sys.platform != "win32" else rd.strftime("%#d %B %Y")
    except Exception:
        run_date_fmt = None

    html_content = generate_html(df, acca_data, title_override=args.title, run_date=run_date_fmt)

    # Output path
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
