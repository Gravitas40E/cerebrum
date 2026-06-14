"""Cerebrum launcher."""
import argparse

import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Cerebrum knowledge terminal")
    parser.add_argument("--no-boot", action="store_true", help="skip the boot animation")
    args = parser.parse_args()
    app.main(show_boot=not args.no_boot)


if __name__ == "__main__":
    main()
