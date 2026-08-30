"""Compatibility entrypoint for the src-based app layout."""

from src.main import RegisterRequest, app, register_user

__all__ = ["app", "RegisterRequest", "register_user"]