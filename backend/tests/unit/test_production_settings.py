
import ast
from pathlib import Path


def test_production_debug_disabled():
    settings_file = (
        Path(__file__).resolve().parents[2]
        / "config"
        / "settings"
        / "production.py"
    )

    tree = ast.parse(settings_file.read_text())

    debug_assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "DEBUG"
            for target in node.targets
        )
    ]

    assert debug_assignments
    assert isinstance(debug_assignments[-1].value, ast.Constant)
    assert debug_assignments[-1].value.value is False
