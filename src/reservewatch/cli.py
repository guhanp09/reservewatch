import argparse
import json

from .pipeline import run


def main():
    p = argparse.ArgumentParser(
        description="Reconstruct paid triangles, backtest reserves and produce review artifacts"
    )
    p.add_argument("command", choices=["run"], nargs="?", default="run")
    p.add_argument("--refresh", action="store_true")
    a = p.parse_args()
    print(json.dumps(run(a.refresh), indent=2))
