"""CLI: validate city, budget, and optional preferences (same rules as future web UI)."""

from __future__ import annotations

import argparse
import json
import sys

from phase_2_user_input import UserInputError, parse_user_input


def main() -> None:
    p = argparse.ArgumentParser(description="Validate user input for restaurant recommendations.")
    p.add_argument("--city", required=True, help="City name (e.g. Bangalore)")
    p.add_argument("--price", required=True, help="Max budget for two (same units as dataset)")
    p.add_argument("--preferences", default=None, help="Optional cuisine or style preferences")
    args = p.parse_args()

    try:
        user = parse_user_input(args.city, args.price, args.preferences)
    except UserInputError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    out = {
        "city": user.city,
        "max_price_for_two": user.max_price_for_two,
        "preferences": user.preferences,
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
