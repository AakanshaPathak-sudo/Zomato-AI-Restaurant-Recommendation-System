"""Phase 2 — user input: schema and validation (CLI now; same rules for web later)."""

from phase_2_user_input.models import UserInput
from phase_2_user_input.validation import UserInputError, parse_user_input

__all__ = ["UserInput", "UserInputError", "parse_user_input"]
