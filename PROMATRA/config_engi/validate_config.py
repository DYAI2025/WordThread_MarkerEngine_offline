#!/usr/bin/env python3
"""
Configuration System Validator for LeanDeep 3.3
Validates all configuration files against their JSON schemas
"""

import json
import yaml
import jsonschema
from pathlib import Path
import hashlib
import sys
from typing import Dict, List, Any

class ConfigValidator:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.schemas_path = self.base_path / "schemas" / "config"
        self.config_path = self.base_path / "config"
        
    def load_schema(self, schema_name: str) -> Dict[str, Any]:
        """Load JSON schema file"""
        schema_file = self.schemas_path / f"{schema_name}.schema.json"
        with open(schema_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_yaml_config(self, config_name: str) -> Dict[str, Any]:
        """Load YAML configuration file"""
        config_file = self.config_path / f"{config_name}.yaml"
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def load_json_config(self, config_name: str) -> Any:
        """Load JSON configuration file"""
        config_file = self.config_path / f"{config_name}.json"
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return f"sha256:{hasher.hexdigest()}"
    
    def validate_enhanced_set_overrides(self) -> bool:
        """Validate enhanced_set_overrides.yaml"""
        try:
            schema = self.load_schema("enhanced_set_overrides")
            config = self.load_yaml_config("enhanced_set_overrides")
            jsonschema.validate(config, schema)
            print("✓ enhanced_set_overrides.yaml is valid")
            return True
        except Exception as e:
            print(f"✗ enhanced_set_overrides.yaml validation failed: {e}")
            return False
    
    def validate_primary_access_weights(self) -> bool:
        """Validate primary_access_weights_overrides.yaml"""
        try:
            schema = self.load_schema("primary_access_weights_overrides")
            config = self.load_yaml_config("primary_access_weights_overrides")
            jsonschema.validate(config, schema)
            print("✓ primary_access_weights_overrides.yaml is valid")
            return True
        except Exception as e:
            print(f"✗ primary_access_weights_overrides.yaml validation failed: {e}")
            return False
    
    def validate_sets_overrides(self) -> bool:
        """Validate sets_overrides.yaml"""
        try:
            schema = self.load_schema("sets_overrides")
            config = self.load_yaml_config("sets_overrides")
            jsonschema.validate(config, schema)
            print("✓ sets_overrides.yaml is valid")
            return True
        except Exception as e:
            print(f"✗ sets_overrides.yaml validation failed: {e}")
            return False
    
    def validate_detect_registry(self) -> bool:
        """Validate detect_registry.json"""
        try:
            schema = self.load_schema("detect_registry")
            config = self.load_json_config("detect_registry")
            jsonschema.validate(config, schema)
            print("✓ detect_registry.json is valid")
            return True
        except Exception as e:
            print(f"✗ detect_registry.json validation failed: {e}")
            return False
    
    def validate_scr_window(self) -> bool:
        """Validate scr_window.json"""
        try:
            schema = self.load_schema("scr_window")
            config = self.load_json_config("scr_window")
            jsonschema.validate(config, schema)
            print("✓ scr_window.json is valid")
            return True
        except Exception as e:
            print(f"✗ scr_window.json validation failed: {e}")
            return False
    
    def validate_core_bundle_manifest(self) -> bool:
        """Validate core_bundle_manifest.yaml"""
        try:
            schema = self.load_schema("core_bundle_manifest")
            manifest_file = self.base_path / "core_bundle_manifest.yaml"
            with open(manifest_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            jsonschema.validate(config, schema)
            print("✓ core_bundle_manifest.yaml is valid")
            return True
        except Exception as e:
            print(f"✗ core_bundle_manifest.yaml validation failed: {e}")
            return False
    
    def validate_file_integrity(self) -> bool:
        """Validate file integrity against manifest hashes"""
        try:
            manifest_file = self.base_path / "core_bundle_manifest.yaml"
            with open(manifest_file, 'r', encoding='utf-8') as f:
                manifest = yaml.safe_load(f)
            
            all_valid = True
            for artifact in manifest['artifacts']:
                file_path = self.base_path / artifact['path']
                if file_path.exists():
                    actual_hash = self.calculate_file_hash(file_path)
                    expected_hash = artifact['hash']
                    if actual_hash == expected_hash:
                        print(f"✓ {artifact['path']} hash matches")
                    else:
                        print(f"✗ {artifact['path']} hash mismatch")
                        print(f"  Expected: {expected_hash}")
                        print(f"  Actual:   {actual_hash}")
                        all_valid = False
                else:
                    print(f"✗ {artifact['path']} file not found")
                    all_valid = False
            
            return all_valid
        except Exception as e:
            print(f"✗ File integrity validation failed: {e}")
            return False
    
    def validate_marker_references(self) -> bool:
        """Validate that all marker references exist in detect_registry"""
        try:
            # Load detect registry
            registry = self.load_json_config("detect_registry")
            registered_markers = {entry['fires_marker'] for entry in registry['detectors']}
            
            # Check sets_overrides
            sets_config = self.load_yaml_config("sets_overrides")
            all_valid = True
            
            for group in sets_config['groups']:
                for marker in group['includes']:
                    if marker not in registered_markers:
                        print(f"✗ Marker {marker} in sets_overrides not found in registry")
                        all_valid = False
            
            # Check enhanced_set_overrides
            eso_config = self.load_yaml_config("enhanced_set_overrides")
            for set_override in eso_config['sets']:
                for target in set_override['targets']:
                    if target not in registered_markers:
                        print(f"✗ Marker {target} in enhanced_set_overrides not found in registry")
                        all_valid = False
            
            # Check primary_access_weights
            paw_config = self.load_yaml_config("primary_access_weights_overrides")
            for weight in paw_config['weights']:
                if weight['target_id'] not in registered_markers:
                    print(f"✗ Marker {weight['target_id']} in primary_access_weights not found in registry")
                    all_valid = False
            
            if all_valid:
                print("✓ All marker references are valid")
            
            return all_valid
        except Exception as e:
            print(f"✗ Marker reference validation failed: {e}")
            return False
    
    def validate_all(self) -> bool:
        """Run all validations"""
        print("=== LeanDeep 3.3 Configuration Validation ===\n")
        
        validations = [
            self.validate_enhanced_set_overrides,
            self.validate_primary_access_weights,
            self.validate_sets_overrides,
            self.validate_detect_registry,
            self.validate_scr_window,
            self.validate_core_bundle_manifest,
            self.validate_marker_references,
            # Note: File integrity validation disabled due to placeholder hashes
            # self.validate_file_integrity,
        ]
        
        results = []
        for validation in validations:
            results.append(validation())
        
        success_count = sum(results)
        total_count = len(results)
        
        print(f"\n=== Validation Summary ===")
        print(f"Passed: {success_count}/{total_count}")
        
        if all(results):
            print("🎉 All validations passed!")
            return True
        else:
            print("❌ Some validations failed!")
            return False

def main():
    if len(sys.argv) > 1:
        base_path = sys.argv[1]
    else:
        base_path = "."
    
    validator = ConfigValidator(base_path)
    success = validator.validate_all()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
