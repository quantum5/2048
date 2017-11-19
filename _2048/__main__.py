"""This module makes the package executable"""

from .main import run_game
import os


def main():
    """Execute the game and store state in the current directory."""
    run_game(data_dir=os.getcwd())


# Run the main function if this file is executed directly.
if __name__ == '__main__':
    main()
