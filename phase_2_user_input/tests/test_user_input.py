"""Unit tests for phase_2_user_input validation."""

import pytest

from phase_2_user_input import UserInput, UserInputError, parse_user_input
from phase_2_user_input.validation import MAX_CITY_LEN, MAX_PREFERENCES_LEN


class TestParseUserInputSuccess:
    def test_minimal_city_and_price(self) -> None:
        out = parse_user_input("Bangalore", 800)
        assert isinstance(out, UserInput)
        assert out.city == "Bangalore"
        assert out.max_price_for_two == pytest.approx(800.0)
        assert out.preferences is None

    def test_normalizes_city_whitespace(self) -> None:
        out = parse_user_input("  New  Delhi  ", 1500)
        assert out.city == "New Delhi"

    def test_price_from_string_with_commas(self) -> None:
        out = parse_user_input("Mumbai", "1,200.50")
        assert out.max_price_for_two == pytest.approx(1200.50)

    def test_preferences_trimmed_and_kept(self) -> None:
        out = parse_user_input("Pune", 500, "  spicy vegetarian  ")
        assert out.preferences == "spicy vegetarian"

    def test_empty_preferences_becomes_none(self) -> None:
        out = parse_user_input("Chennai", 900, "   ")
        assert out.preferences is None

    def test_none_preferences(self) -> None:
        out = parse_user_input("Hyderabad", 700, None)
        assert out.preferences is None


class TestParseUserInputErrors:
    def test_empty_city(self) -> None:
        with pytest.raises(UserInputError, match="city is required"):
            parse_user_input("", 100)

    def test_whitespace_only_city(self) -> None:
        with pytest.raises(UserInputError, match="city is required"):
            parse_user_input("   \t  ", 100)

    def test_city_too_long(self) -> None:
        long_city = "x" * (MAX_CITY_LEN + 1)
        with pytest.raises(UserInputError, match="city must be at most"):
            parse_user_input(long_city, 100)

    def test_price_zero(self) -> None:
        with pytest.raises(UserInputError, match="price must be greater than zero"):
            parse_user_input("Kolkata", 0)

    def test_price_negative(self) -> None:
        with pytest.raises(UserInputError, match="price must be greater than zero"):
            parse_user_input("Kolkata", -50)

    def test_price_invalid_string(self) -> None:
        with pytest.raises(UserInputError, match="valid number"):
            parse_user_input("Kolkata", "abc")

    def test_price_bool_rejected(self) -> None:
        with pytest.raises(UserInputError, match="number"):
            parse_user_input("Kolkata", True)  # type: ignore[arg-type]

    def test_preferences_too_long(self) -> None:
        prefs = "x" * (MAX_PREFERENCES_LEN + 1)
        with pytest.raises(UserInputError, match="preferences must be at most"):
            parse_user_input("Kolkata", 100, prefs)


class TestUserInputDataclass:
    def test_frozen_immutable(self) -> None:
        u = parse_user_input("A", 1)
        with pytest.raises(Exception):
            u.city = "B"  # type: ignore[misc]
