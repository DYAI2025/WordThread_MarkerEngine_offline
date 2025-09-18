#!/usr/bin/env python3
"""
Migration script to convert free text activation rules to normalized format.
"""

import yaml
import re
from pathlib import Path

def parse_free_text_rule(rule_text):
    """Parse free text activation rule into normalized format."""
    rule_text = rule_text.strip().strip('"').strip("'")

    # Handle complex rules with OR
    if " OR " in rule_text:
        parts = rule_text.split(" OR ")
        # For now, take the first part as primary rule
        rule_text = parts[0].strip()

    # Parse simple rules
    patterns = {
        r"ANY in (\d+) message": ("ANY", {"count": int}),
        r"ALL in (\d+) message": ("ALL", {"count": int}),
        r"ANY (\d+) in (\d+) messages": ("FREQUENCY", {"count": int, "window": int}),
        r"X_OF_Y\((\d+),(\d+)\)": ("X_OF_Y", {"x": int, "y": int}),
        r"AT_LEAST_DISTINCT\((\d+)\)": ("AT_LEAST_DISTINCT", {"count": int}),
        r"WEIGHTED_AND\((\d+)\)": ("WEIGHTED_AND", {"threshold": float}),
    }

    for pattern, (rule_type, param_types) in patterns.items():
        match = re.match(pattern, rule_text)
        if match:
            params = {}
            for i, (param_name, param_type) in enumerate(param_types.items()):
                if i < len(match.groups()):
                    params[param_name] = param_type(match.groups()[i])
            return {"rule": rule_type, "params": params}

    # Default fallback
    return {"rule": "ANY", "params": {"count": 1}}

def migrate_activation_rules():
    """Migrate all YAML files with free text activation rules."""
    marker_dir = Path("_Marker_5.0")
    migrated_count = 0

    for yaml_file in marker_dir.glob("*.yaml"):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if "activation" in data:
                activation = data["activation"]

                # Skip if activation is None or not a string/dict
                if activation is None:
                    continue

                # Check if it's a string (free text) rather than dict (normalized)
                if isinstance(activation, str):
                    print(f"Migrating {yaml_file.name}: '{activation}'")
                    normalized = parse_free_text_rule(activation)
                    data["activation"] = normalized
                    migrated_count += 1

                    # Write back
                    with open(yaml_file, 'w', encoding='utf-8') as f:
                        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

                elif isinstance(activation, dict):
                    # Handle case where activation is dict but rule is string
                    if "rule" in activation and isinstance(activation["rule"], str):
                        rule_text = activation["rule"]
                        if not rule_text.isupper() or " in " in rule_text:
                            print(f"Normalizing {yaml_file.name}: '{rule_text}'")
                            normalized = parse_free_text_rule(rule_text)
                            data["activation"] = normalized
                            migrated_count += 1

                            with open(yaml_file, 'w', encoding='utf-8') as f:
                                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        except Exception as e:
            print(f"Error processing {yaml_file}: {e}")

    print(f"\nMigration complete: {migrated_count} files updated")

if __name__ == "__main__":
    migrate_activation_rules()
