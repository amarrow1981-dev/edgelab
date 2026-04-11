#!/usr/bin/env python3
"""
EdgeLab Gary v1
---------------
The Claude API wrapper. Gary's mouth.

Takes a GaryContext, builds the prompt, hits the Claude API, returns Gary's response.

Usage:
    # Single match — ask Gary for his read
    from edgelab_gary import Gary
    from edgelab_gary_brain import GaryBrain, build_engine_output_block
    from edgelab_gary_context import build_gary_prompt

    gary = Gary(api_key="YOUR_KEY")
    brain = GaryBrain("history/")

    ctx = brain.build_context(
        home_team="Wigan Athletic",
        away_team="Leyton Orient",
        match_date="2026-04-02",
        tier="E2",
    )

    response = gary.ask(ctx)
    print(response)

    # Conversation mode — follow-up questions
    response2 = gary.follow_up("What about the H2H though?")
    print(response2)

    # Full predictions table — Gary talks through a whole matchday
    gary.matchday_briefing(ctx_list)

CLI:
    python edgelab_gary.py --data history/ --home "Wigan Athletic" --away "Leyton Orient" --date 2026-04-02 --tier E2
    python edgelab_gary.py --data history/ --home "Wigan Athletic" --away "Leyton Orient" --date 2026-04-02 --tier E2 --chat
"""

import os
import sys
import json
import argparse
import logging
from typing import Optional, List

sys.path.insert(0, os.path.dirname(__file__))

from edgelab_gary_brain import GaryBrain, GaryContext, build_engine_output_block
from edgelab_gary_context import build_gary_prompt, system_prompt, match_prompt

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLAUDE_MODEL    = "claude-sonnet-4-20250514"
MAX_TOKENS      = 1024
API_ENDPOINT    = "https://api.anthropic.com/v1/messages"


# ---------------------------------------------------------------------------
# Gary — the API wrapper
# ---------------------------------------------------------------------------

class Gary:
    """
    Gary's voice. Wraps the Claude API.

    Maintains conversation history so follow-up questions work naturally.
    Each call to ask() starts a fresh conversation.
    follow_up() continues the current one.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._system = system_prompt()
        self._history: List[dict] = []   # conversation history for this session
        self._current_ctx: Optional[GaryContext] = None

    # -----------------------------------------------------------------------
    # Primary interface
    # -----------------------------------------------------------------------

    def ask(self, ctx: GaryContext, extra: str = "") -> str:
        """
        Ask Gary for his read on a fixture.
        Starts a fresh conversation for this match.

        Args:
            ctx:   GaryContext built by GaryBrain
            extra: Optional extra question to append to the match prompt
                   e.g. "Would you put money on this?"

        Returns:
            Gary's response as a string.
        """
        self._history = []
        self._current_ctx = ctx

        _, prompt = build_gary_prompt(ctx)
        if extra:
            prompt = f"{prompt}\n\n{extra}"

        return self._chat(prompt)

    def follow_up(self, question: str) -> str:
        """
        Ask a follow-up question in the current conversation.
        Must call ask() first.

        Args:
            question: Natural language follow-up e.g. "What about the away form?"

        Returns:
            Gary's response.
        """
        if not self._history:
            return "Gary hasn't been briefed on a match yet. Call ask() first."

        return self._chat(question)

    def matchday_briefing(self, ctx_list: List[GaryContext]) -> List[dict]:
        """
        Gary talks through a full list of fixtures — one by one.
        Returns list of {home, away, response} dicts.

        Useful for generating a full matchday predictions post.
        """
        results = []
        for ctx in ctx_list:
            mc = ctx.match_context
            print(f"\n  Gary on {mc.home_team} vs {mc.away_team}...")
            response = self.ask(ctx)
            results.append({
                "home": mc.home_team,
                "away": mc.away_team,
                "date": mc.date,
                "tier": mc.tier,
                "response": response,
            })
        return results

    def react_to_result(self, ctx: GaryContext, actual_result: str, actual_score: str = "") -> str:
        """
        Gary reacts to a result after the fact.
        Pass in the original context + what actually happened.

        Args:
            ctx:           The original match context Gary was briefed on
            actual_result: "H", "D", or "A"
            actual_score:  e.g. "0-0" or "2-1" (optional)

        Returns:
            Gary's reaction.
        """
        e = ctx.engine_output
        mc = ctx.match_context

        result_label = {
            "H": f"{mc.home_team} won",
            "D": "Draw",
            "A": f"{mc.away_team} won",
        }.get(actual_result, actual_result)

        pred_label = {
            "H": f"{mc.home_team}",
            "D": "Draw",
            "A": f"{mc.away_team}",
        }.get(e.prediction, "?") if e.prediction else "unknown"

        score_str = f" ({actual_score})" if actual_score else ""
        got_it_right = e.prediction == actual_result if e.prediction else None

        prompt = (
            f"Result just in: {mc.home_team} vs {mc.away_team}{score_str} — {result_label}.\n"
            f"You predicted: {pred_label}.\n"
        )

        if got_it_right is True:
            prompt += "You got it right."
        elif got_it_right is False:
            prompt += "You got it wrong."

        if e.approx_draw_flag and actual_result == "D":
            prompt += " Your ~D flag fired correctly."
        if e.upset_flag and actual_result != e.prediction:
            prompt += " Your upset flag fired correctly."

        prompt += "\nReact to this result Gary. Keep it short."

        # Brief Gary on the match first, then react
        self._history = []
        _, match = build_gary_prompt(ctx)
        self._chat(match)  # brief him silently
        return self._chat(prompt)

    # -----------------------------------------------------------------------
    # Internal API call
    # -----------------------------------------------------------------------

    def _chat(self, message: str) -> str:
        """
        Send a message in the current conversation.
        Appends to history, returns Gary's response text.
        """
        try:
            import urllib.request
        except ImportError:
            return "[Gary] urllib not available"

        self._history.append({"role": "user", "content": message})

        payload = {
            "model":      CLAUDE_MODEL,
            "max_tokens": MAX_TOKENS,
            "system":     self._system,
            "messages":   self._history,
        }

        try:
            req = urllib.request.Request(
                API_ENDPOINT,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type":      "application/json",
                    "x-api-key":         self.api_key,
                    "anthropic-version": "2023-06-01",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            response_text = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    response_text += block["text"]

            # Add Gary's response to history so follow-ups work
            self._history.append({"role": "assistant", "content": response_text})
            return response_text

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            logger.error(f"[Gary] API error {e.code}: {body}")
            return f"[Gary] API error {e.code} — check your key and try again."

        except Exception as e:
            logger.error(f"[Gary] Unexpected error: {e}")
            return f"[Gary] Something went wrong: {e}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="EdgeLab Gary — match analysis")
    parser.add_argument("--data",  required=True, help="Historical data folder e.g. history/")
    parser.add_argument("--home",  required=True, help="Home team name")
    parser.add_argument("--away",  required=True, help="Away team name")
    parser.add_argument("--date",  required=True, help="Match date YYYY-MM-DD")
    parser.add_argument("--tier",  required=True, help="Tier e.g. E0/E1/E2/E3/EC")
    parser.add_argument("--key",   default=None,  help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")
    parser.add_argument("--chat",  action="store_true", help="Stay in conversation after initial briefing")
    parser.add_argument("--react", type=str, default=None,
                        help="React to a result — pass actual result: H / D / A")
    parser.add_argument("--score", type=str, default="",
                        help="Actual scoreline for --react e.g. '0-0'")
    args = parser.parse_args()

    api_key = args.key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n  No API key. Set ANTHROPIC_API_KEY or pass --key YOUR_KEY\n")
        sys.exit(1)

    print("\n╔══════════════════════════════════════════╗")
    print("║           EdgeLab — Gary v1              ║")
    print("╚══════════════════════════════════════════╝\n")

    # Load brain
    brain = GaryBrain(args.data)

    # Build context
    ctx = brain.build_context(
        home_team=args.home,
        away_team=args.away,
        match_date=args.date,
        tier=args.tier,
    )

    # Print the context summary so we know what Gary's been given
    print(ctx)

    gary = Gary(api_key=api_key)

    # React mode
    if args.react:
        print(f"  Gary reacting to result: {args.react}  {args.score}")
        print(f"  {'─'*60}\n")
        response = gary.react_to_result(ctx, args.react, args.score)
        print(f"  Gary:\n\n{response}\n")
        return

    # Standard ask
    print(f"  Gary's read:\n  {'─'*60}\n")
    response = gary.ask(ctx)
    print(f"{response}\n")

    # Chat mode — keep going
    if args.chat:
        print(f"  {'─'*60}")
        print("  Chat mode — ask Gary anything about this match.")
        print("  Type 'quit' to exit.\n")

        while True:
            try:
                user_input = input("  You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n  Gary: Right. I'm off.\n")
                break

            if user_input.lower() in ("quit", "exit", "bye"):
                print("\n  Gary: Cheers mate. See you next week.\n")
                break

            if not user_input:
                continue

            reply = gary.follow_up(user_input)
            print(f"\n  Gary: {reply}\n")


if __name__ == "__main__":
    main()
