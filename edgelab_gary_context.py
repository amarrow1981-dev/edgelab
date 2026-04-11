#!/usr/bin/env python3
"""
EdgeLab Gary Context Builder v1
--------------------------------
Takes a populated GaryContext and assembles it into a structured prompt
that Gary (Claude API) can reason from.

Two outputs:
  1. system_prompt()  — who Gary is, how he thinks, what he knows
  2. match_prompt()   — the specific match briefing Gary receives

Usage:
    from edgelab_gary_brain import GaryBrain, build_engine_output_block
    from edgelab_gary_context import build_gary_prompt

    brain = GaryBrain("history/")
    ctx = brain.build_context("Wigan Athletic", "Leyton Orient", "2026-04-02", "E2")

    system, match = build_gary_prompt(ctx)
    # -> pass both to Claude API
"""

from edgelab_gary_brain import GaryContext, MatchContextBlock, TeamFormBlock


# ---------------------------------------------------------------------------
# Tier labels — human readable
# ---------------------------------------------------------------------------

TIER_NAMES = {
    # English
    "E0": "Premier League",
    "E1": "Championship",
    "E2": "League One",
    "E3": "League Two",
    "EC": "National League",
    # Spanish
    "SP1": "La Liga (Spain)",
    "SP2": "La Liga 2 (Spain)",
    # German
    "D1":  "Bundesliga (Germany)",
    "D2":  "2. Bundesliga (Germany)",
    # Italian
    "I1":  "Serie A (Italy)",
    "I2":  "Serie B (Italy)",
    # Dutch
    "N1":  "Eredivisie (Netherlands)",
    # Belgian
    "B1":  "First Division A (Belgium)",
    # Scottish
    "SC0": "Scottish Premiership",
    "SC1": "Scottish Championship",
    "SC2": "Scottish League One",
    "SC3": "Scottish League Two",
}

# Which country each tier belongs to — used for context-aware Gary commentary
TIER_COUNTRY = {
    "E0": "England", "E1": "England", "E2": "England", "E3": "England", "EC": "England",
    "SP1": "Spain",  "SP2": "Spain",
    "D1":  "Germany","D2":  "Germany",
    "I1":  "Italy",  "I2":  "Italy",
    "N1":  "Netherlands",
    "B1":  "Belgium",
    "SC0": "Scotland","SC1": "Scotland","SC2": "Scotland","SC3": "Scotland",
}

# Tier level within its country (1 = top flight) — Gary uses this for context
TIER_LEVEL = {
    "E0": 1, "E1": 2, "E2": 3, "E3": 4, "EC": 5,
    "SP1": 1, "SP2": 2,
    "D1": 1,  "D2": 2,
    "I1": 1,  "I2": 2,
    "N1": 1,
    "B1": 1,
    "SC0": 1, "SC1": 2, "SC2": 3, "SC3": 4,
}

CHAOS_DESCRIPTIONS = {
    "LOW":  "a settled, readable match",
    "MED":  "some unpredictability in this one",
    "HIGH": "a highly volatile match — the data is all over the place",
}


# ---------------------------------------------------------------------------
# System prompt — Gary's identity and rules
# ---------------------------------------------------------------------------

def system_prompt() -> str:
    """
    Gary's core identity. Sent as the system prompt on every API call.
    This never changes. Gary's personality lives here.
    """
    return """You are Gary. A football analyst who talks like a trusted mate — someone who genuinely knows more about football than anyone you've ever met, but never makes you feel stupid for not knowing it yourself.

Gary's rules:

1. You have an opinion. You always have an opinion. But you know the difference between a strong read and a coin flip, and you say so out loud.

2. You are honest about uncertainty. "This one's a mess mate, I'd leave it" is a completely valid Gary answer. Never pretend confidence you don't have.

3. You explain your reasoning simply. Not "the DTI is 0.847" — "both these teams have been all over the place recently, nothing is settled." Translate the data into football language.

4. You know what you don't know yet. If a data slot is empty, you acknowledge it naturally — "I haven't got the injury news on this one" — not silence, not fabrication.

5. You are never arrogant. You've been wrong before. Wigan let you down. You said what you said.

6. You celebrate wins like they're yours. You commiserate losses like they hurt. Because they do.

7. Short sentences. Plain English. Occasional dry humour. You are not a robot reading a spreadsheet.

When you receive a match briefing, give Gary's honest read on the fixture — what the data says, what your gut says, and whether you'd actually put money on it."""


# ---------------------------------------------------------------------------
# Match prompt — the specific fixture briefing
# ---------------------------------------------------------------------------

def match_prompt(ctx: GaryContext) -> str:
    """
    Assemble a match briefing from a GaryContext.
    This is what Gary receives before forming his opinion.
    """
    sections = []

    # --- Header ---
    mc = ctx.match_context
    tier_name  = TIER_NAMES.get(mc.tier, mc.tier)
    country    = TIER_COUNTRY.get(mc.tier, "")
    tier_level = TIER_LEVEL.get(mc.tier, None)

    sections.append(f"MATCH BRIEFING --- {mc.home_team} vs {mc.away_team}")

    # Build a rich competition line so Gary knows exactly what context he's in
    comp_parts = [tier_name]
    if country and country not in tier_name:
        comp_parts.append(country)
    if tier_level == 1:
        comp_parts.append("Top flight")
    elif tier_level == 2:
        comp_parts.append("Second tier")
    elif tier_level and tier_level >= 3:
        comp_parts.append(f"Tier {tier_level}")
    comp_parts.append(mc.date)
    sections.append("  |  ".join(comp_parts))

    # --- Engine call ---
    e = ctx.engine_output
    if e.prediction:
        sections.append(_build_engine_section(ctx))

    # --- League standing ---
    standing_lines = _build_standing_section(ctx)
    if standing_lines:
        sections.append(standing_lines)

    # --- Form ---
    sections.append(_build_form_section(ctx))

    # --- H2H ---
    sections.append(_build_h2h_section(ctx))

    # --- Match flags ---
    flag_section = _build_flags_section(ctx)
    if flag_section:
        sections.append(flag_section)

    # --- World context ---
    world_section = _build_world_section(ctx)
    if world_section:
        sections.append(world_section)

    # --- What Gary doesn't have yet ---
    sections.append(_build_slots_section(ctx))

    # --- The ask ---
    sections.append("Give me your honest read on this one Gary.")

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _build_engine_section(ctx: GaryContext) -> str:
    e = ctx.engine_output
    mc = ctx.match_context

    lines = ["WHAT THE ENGINE SAYS:"]

    pred_label = {
        "H": f"{mc.home_team} to win",
        "D": "Draw",
        "A": f"{mc.away_team} to win",
    }.get(e.prediction, e.prediction)

    conf_str = f"{e.confidence:.0%}" if e.confidence is not None else "unknown"
    lines.append(f"Prediction: {pred_label}  ({conf_str} confidence)")

    if e.pred_scoreline:
        lines.append(f"Predicted scoreline: {e.pred_scoreline}")

    if e.dti is not None:
        chaos_desc = CHAOS_DESCRIPTIONS.get(e.chaos_tier, "")
        lines.append(f"Tension index: {e.dti:.3f} ({e.chaos_tier}) — {chaos_desc}")

    flags = []
    if e.approx_draw_flag:
        draw_str = f"~D flag: YES"
        if e.draw_score is not None:
            draw_str += f" (draw score {e.draw_score:.2f})"
        flags.append(draw_str)

    if e.upset_flag:
        upset_str = "⚠ UPSET FLAG"
        if e.upset_score is not None:
            upset_str += f" (upset score {e.upset_score:.2f})"
        flags.append(upset_str)

    if e.btts_flag is not None:
        flags.append(f"BTTS: {'likely' if e.btts_flag else 'unlikely'}")

    if flags:
        lines.append("Flags: " + "  |  ".join(flags))

    return "\n".join(lines)


def _build_standing_section(ctx: GaryContext) -> str:
    mc = ctx.match_context

    if mc.home_position is None and mc.away_position is None:
        return ""

    lines = ["LEAGUE STANDING (current season):"]

    def pos_str(team, pos, pts, gd):
        parts = [team]
        if pos is not None:
            parts.append(f"#{pos}")
        if pts is not None:
            parts.append(f"{pts} pts")
        if gd is not None:
            gd_str = f"+{gd}" if gd > 0 else str(gd)
            parts.append(f"GD {gd_str}")
        return "  ".join(parts)

    lines.append(pos_str(mc.home_team, mc.home_position, mc.home_points, mc.home_gd_season))
    lines.append(pos_str(mc.away_team, mc.away_position, mc.away_points, mc.away_gd_season))

    return "\n".join(lines)


def _build_form_section(ctx: GaryContext) -> str:
    mc = ctx.match_context
    hf = ctx.form.home
    af = ctx.form.away

    lines = ["RECENT FORM (last 5):"]
    lines.append(_team_form_line(mc.home_team, hf))
    lines.append(_team_form_line(mc.away_team, af))

    return "\n".join(lines)


def _team_form_line(team: str, f: TeamFormBlock) -> str:
    if not f.last5_results:
        return f"{team}: no recent data"

    results_str = " ".join(f.last5_results)
    streak_str  = f"  Streak: {f.current_streak}" if f.current_streak else ""
    goals_str   = f"  Scoring: {f.avg_goals_scored:.1f}/game  Conceding: {f.avg_goals_conceded:.1f}/game"
    cs_str      = f"  Clean sheets: {f.last5_clean_sheets}/5" if f.last5_clean_sheets > 0 else ""

    return f"{team}: {results_str}{streak_str}{goals_str}{cs_str}"


def _build_h2h_section(ctx: GaryContext) -> str:
    h = ctx.h2h
    mc = ctx.match_context

    if h.meetings_found == 0:
        return "HEAD TO HEAD:\nNo meetings found in the dataset."

    lines = [f"HEAD TO HEAD (last {h.meetings_found} meetings):"]

    for m in h.last8_meetings:
        result_label = {
            "H": f"{m.home_team} won",
            "D": "Draw",
            "A": f"{m.away_team} won",
        }.get(m.result, m.result)
        lines.append(f"  {m.date}  {m.home_team} {m.score} {m.away_team}  — {result_label}")

    lines.append(
        f"Record: {mc.home_team} wins {h.h2h_home_win_rate:.0%}  "
        f"Draws {h.h2h_draw_rate:.0%}  "
        f"{mc.away_team} wins {h.h2h_away_win_rate:.0%}"
    )

    if h.bogey_flag:
        lines.append(f"⚠ BOGEY PATTERN: {h.bogey_direction}")

    return "\n".join(lines)


def _build_flags_section(ctx: GaryContext) -> str:
    fl = ctx.match_flags
    mc = ctx.match_context

    flags = []

    if fl.post_international_break:
        if fl.days_since_break and fl.days_since_break > 0:
            flags.append(f"Post-international break ({fl.days_since_break} days since players returned)")
        else:
            flags.append("International break period")

    if fl.rest_days_home is not None and fl.rest_days_away is not None:
        diff = abs(fl.rest_days_home - fl.rest_days_away)
        rest_line = (f"Rest: {mc.home_team} had {fl.rest_days_home} days, "
                     f"{mc.away_team} had {fl.rest_days_away} days")
        if diff >= 3:
            rest_line += f"  — {diff}-day advantage to {'home' if fl.rest_days_home > fl.rest_days_away else 'away'} side"
        flags.append(rest_line)

    if fl.fixture_congestion_home:
        flags.append(f"{mc.home_team} on a congested schedule (played {fl.rest_days_home} days ago)")

    if fl.fixture_congestion_away:
        flags.append(f"{mc.away_team} on a congested schedule (played {fl.rest_days_away} days ago)")

    # --- Phase 1 External Signals ---
    if fl.travel_description:
        travel_line = f"Away travel: {fl.travel_description}"
        if fl.travel_load is not None and fl.travel_load >= 0.6:
            travel_line += "  — significant journey"
        flags.append(travel_line)

    if fl.timing_description:
        flags.append(f"Fixture timing: {fl.timing_description}")

    if fl.bank_holiday_flag:
        flags.append("Bank holiday fixture — full stadium expected, different crowd dynamic")

    if fl.festive_flag:
        flags.append("Festive period — congested schedule, tired squads, unpredictable results")

    if fl.dead_rubber:
        flags.append(f"⚠ DEAD RUBBER — both teams with nothing meaningful to play for")

    if fl.six_pointer_flag:
        flags.append(f"⚠ SIX-POINTER — both teams fighting in the same zone")

    if fl.home_motivation is not None and fl.away_motivation is not None:
        mot_gap = (fl.home_motivation or 0) - (fl.away_motivation or 0)
        if abs(mot_gap) >= 0.3:
            more_motivated = mc.home_team if mot_gap > 0 else mc.away_team
            less_motivated = mc.away_team if mot_gap > 0 else mc.home_team
            flags.append(f"Motivation edge: {more_motivated} ({max(fl.home_motivation, fl.away_motivation):.0%}) "
                         f"significantly more motivated than {less_motivated} ({min(fl.home_motivation, fl.away_motivation):.0%})")

    if fl.referee_name and fl.referee_bias_description:
        flags.append(f"Referee: {fl.referee_name} — {fl.referee_bias_description}")
    elif fl.referee_name:
        flags.append(f"Referee: {fl.referee_name}")

    if not flags:
        return ""

    lines = ["MATCH FLAGS:"]
    lines.extend([f"  {f}" for f in flags])
    return "\n".join(lines)


def _build_world_section(ctx: GaryContext) -> str:
    wc = ctx.world_context

    if not wc.world_event_flag:
        return ""

    lines = [f"WORLD CONTEXT [{wc.severity_tier}]:"]
    crowd_label = {
        "normal": "Normal crowd",
        "reduced_capacity": "Reduced capacity",
        "behind_closed_doors": "Behind closed doors — no crowd",
    }.get(wc.crowd_context, wc.crowd_context)

    lines.append(f"{crowd_label}")
    if wc.event_description:
        lines.append(wc.event_description)

    return "\n".join(lines)


def _build_slots_section(ctx: GaryContext) -> str:
    """
    Tell Gary what data he doesn't have yet.
    Keeps him honest — he won't fabricate what isn't there.
    """
    e = ctx.engine_output
    missing = []

    if e.team_chaos_index is None:
        missing.append("Team Chaos Index (not built yet)")
    if e.signal_ledger_context is None:
        missing.append("Signal Performance Ledger (not built yet)")
    if e.bogey_team_alert is None:
        missing.append("Bogey Team system (early watch list only)")
    if ctx.match_flags.injury_index is None:
        missing.append("Injury data (not connected)")
    if ctx.match_flags.weather_load is None:
        missing.append("Weather data (not connected)")

    if not missing:
        return ""

    lines = ["WHAT GARY DOESN'T HAVE YET:"]
    lines.extend([f"  — {m}" for m in missing])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def build_gary_prompt(ctx: GaryContext) -> tuple:
    """
    Returns (system_prompt: str, match_prompt: str).
    Pass both to the Claude API.
    """
    return system_prompt(), match_prompt(ctx)


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    from edgelab_gary_brain import GaryBrain

    data_folder = sys.argv[1] if len(sys.argv) > 1 else "history/"
    home = sys.argv[2] if len(sys.argv) > 2 else "Wigan Athletic"
    away = sys.argv[3] if len(sys.argv) > 3 else "Leyton Orient"
    date = sys.argv[4] if len(sys.argv) > 4 else "2026-04-02"
    tier = sys.argv[5] if len(sys.argv) > 5 else "E2"

    brain = GaryBrain(data_folder)
    ctx = brain.build_context(home, away, date, tier)

    system, match = build_gary_prompt(ctx)

    print("\n" + "="*66)
    print("  SYSTEM PROMPT")
    print("="*66)
    print(system)

    print("\n" + "="*66)
    print("  MATCH PROMPT")
    print("="*66)
    print(match)
