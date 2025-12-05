# verbose_mode.py
"""
Centralized verbose mode manager for all modules.
Use --verbose flag from terminal to enable debug output.

Usage:
    python host.py --verbose
    python joiner.py --verbose
    python spectator.py --verbose
"""

import sys


class VerboseManager:
    """Singleton for managing verbose mode across all modules."""
    _verbose = "--verbose" in sys.argv

    @classmethod
    def set_verbose(cls, verbose: bool):
        """Set verbose mode on/off."""
        cls._verbose = verbose

    @classmethod
    def is_verbose(cls) -> bool:
        """Check if verbose mode is enabled."""
        return cls._verbose

    @classmethod
    def toggle_verbose(cls):
        """Toggle verbose mode."""
        cls._verbose = not cls._verbose

    @classmethod
    def log(cls, prefix: str, *args):
        """Utility method to log with prefix if verbose mode is on."""
        if cls.is_verbose():
            print(f"[{prefix}]", *args)
