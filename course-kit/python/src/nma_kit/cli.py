"""`nma-kit` command line (subcommands are added in a later task)."""

import sys


def main(argv: list[str] | None = None) -> int:
    print("usage: nma-kit <command> [options]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
