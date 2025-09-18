import yaml
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ActivationUnifier:
    """Handles unification of activation logic into standardized format."""

    def __init__(self, marker_path: str = "_Marker_5.0"):
        self.marker_path = Path(marker_path)
        self.processed_count = 0
        self.error_count = 0

    def parse_activation_rule(self, logic: str) -> Optional[Dict[str, Any]]:
        """Parse activation logic string into structured format."""
        logic = logic.strip()

        # Rule: ANY
        match = re.match(r"ANY (\d+)$", logic)
        if match:
            return {"rule": "ANY", "params": {"count": int(match.group(1))}}

        match = re.match(r"ANY (\d+) IN (\d+) messages", logic)
        if match:
            return {"rule": "ANY", "params": {"count": int(match.group(1)), "window": {"size": int(match.group(2)), "unit": "messages"}}}

        # Rule: ALL
        match = re.match(r"ALL (\d+) IN (\d+) messages", logic)
        if match:
            return {"rule": "ALL", "params": {"count": int(match.group(1)), "window": {"size": int(match.group(2)), "unit": "messages"}}}

        # Rule: AT_LEAST
        match = re.match(r"AT_LEAST (\d+) IN (\d+) messages", logic)
        if match:
            return {"rule": "AT_LEAST", "params": {"count": int(match.group(1)), "window": {"size": int(match.group(2)), "unit": "messages"}}}

        match = re.match(r"AT_LEAST (\d+) INSTANCES IN (\d+) days", logic)
        if match:
            return {"rule": "AT_LEAST", "params": {"count": int(match.group(1)), "window": {"size": int(match.group(2)), "unit": "days"}}}

        # Rule: SUM(weight)
        match = re.match(r"SUM\(weight\)≥([\d.]+) WITHIN (\d+)([a-z])", logic)
        if match:
            return {"rule": "SUM_WEIGHT", "params": {"threshold": float(match.group(1)), "window": {"size": int(match.group(2)), "unit": match.group(3)}}}

        # Rule: AT_LEAST DISTINCT
        match = re.match(r"AT_LEAST (\d+) DISTINCT (\w+) IN (\d+) messages", logic)
        if match:
            return {"rule": "AT_LEAST_DISTINCT", "params": {"count": int(match.group(1)), "type": match.group(2), "window": {"size": int(match.group(3)), "unit": "messages"}}}

        # Rule: FREQUENCY
        match = re.match(r"FREQUENCY ≥(\d+) per (\w+) FOR (\d+) (\w+)", logic)
        if match:
            return {"rule": "FREQUENCY", "params": {"count": int(match.group(1)), "per": match.group(2), "for": {"size": int(match.group(3)), "unit": match.group(4)}}}

        return None

    def process_file(self, file_path: Path) -> bool:
        """Process a single marker file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data or "activation" not in data:
                return True  # No activation to process

            activation_data = data["activation"]
            if not (isinstance(activation_data, dict) and "rule" in activation_data and isinstance(activation_data["rule"], str)):
                return True  # Already in correct format

            logic = activation_data["rule"].strip()
            logger.info(f"Processing {file_path} with logic: '{logic}'")

            new_activation = self.parse_activation_rule(logic)
            if new_activation:
                activation_data.update(new_activation)
                logger.info(f"Updated activation in {file_path}")

                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

                self.processed_count += 1
                return True
            else:
                logger.warning(f"Could not parse activation rule: {logic} in {file_path}")
                return False

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            self.error_count += 1
            return False

    def unify_all(self) -> Dict[str, int]:
        """Process all marker files in the directory."""
        logger.info("Starting activation unification...")

        if not self.marker_path.exists():
            raise FileNotFoundError(f"Marker path does not exist: {self.marker_path}")

        marker_files = list(self.marker_path.glob("*.yaml"))
        logger.info(f"Found {len(marker_files)} marker files")

        success_count = 0
        for file_path in marker_files:
            if self.process_file(file_path):
                success_count += 1

        logger.info(f"Processing complete: {success_count}/{len(marker_files)} files processed successfully")
        if self.error_count > 0:
            logger.warning(f"Encountered {self.error_count} errors during processing")

        return {
            "total_files": len(marker_files),
            "processed": self.processed_count,
            "successful": success_count,
            "errors": self.error_count
        }

def unify_activation():
    """Legacy function for backward compatibility."""
    unifier = ActivationUnifier()
    return unifier.unify_all()

if __name__ == "__main__":
    unifier = ActivationUnifier()
    result = unifier.unify_all()
    print(f"Results: {result}")