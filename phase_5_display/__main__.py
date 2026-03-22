"""CLI: full stack from Parquet + user input to terminal output."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from phase_2_user_input import UserInputError
from phase_5_display.format_output import format_file_error
from phase_5_display.pipeline import run_pipeline


def main() -> None:
    p = argparse.ArgumentParser(description="Zomato-style AI restaurant recommendations (CLI).")
    p.add_argument("--parquet", required=True, type=Path, help="Path to processed restaurants.parquet")
    p.add_argument("--city", required=True, help="City name")
    p.add_argument("--price", required=True, help="Max budget for two (same units as dataset)")
    p.add_argument("--preferences", default=None, help="Optional preferences for the LLM")
    p.add_argument("--top-k", type=int, default=10, dest="top_k", help="Number of recommendations")
    args = p.parse_args()

    try:
        text = run_pipeline(
            city=args.city,
            price=args.price,
            preferences=args.preferences,
            parquet_path=args.parquet,
            top_k=args.top_k,
        )
    except UserInputError as e:
        print(f"Invalid input: {e}", file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError:
        print(
            format_file_error(str(args.parquet), "File not found."),
            file=sys.stderr,
            end="",
        )
        sys.exit(1)
    except OSError as e:
        print(format_file_error(str(args.parquet), str(e)), file=sys.stderr, end="")
        sys.exit(1)

    print(text, end="")


if __name__ == "__main__":
    main()
