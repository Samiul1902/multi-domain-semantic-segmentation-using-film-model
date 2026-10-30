"""No scientific execution route exists in the repair work package."""
import argparse
from .contracts import Refusal, CONFIG, validate_config
from .authorization import production_authorization


def main(argv=None):
    parser = argparse.ArgumentParser(description="BARR-M1 v1.0d engineering repair; execution disabled")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--authorization")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args(argv)
    try:
        validate_config(CONFIG)
        if args.execute or args.authorization:
            production_authorization()
        print("NO_EXECUTION: run the isolated synthetic unittest suite for engineering validation")
        return 0
    except Refusal as exc:
        print(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
