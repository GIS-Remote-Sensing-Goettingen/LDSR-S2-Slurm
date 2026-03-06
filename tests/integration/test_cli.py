from pathlib import Path

from ldsrs2_launcher.cli import build_parser


def test_cli_validate_args() -> None:
    parser = build_parser()
    args = parser.parse_args(["validate-config", "--config", str(Path("configs/runtime/default.yaml"))])
    assert args.command == "validate-config"
