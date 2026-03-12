#!/usr/bin/env python3
"""
Generate Airflow variables.json from environment variables.
Simple and straightforward - no overcomplicated management.
"""

import json
import os
import sys
from pathlib import Path

from constants.environment import ENVIRONMENT_VARIABLES, is_sensitive

def load_env_file(env_path: Path) -> dict:
    """Load environment variables from .env file."""
    env_vars = {}
    
    if not env_path.exists():
        print(f"Warning: {env_path} not found")
        return env_vars
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                
                if value:  # Only add non-empty values
                    env_vars[key] = value
    
    return env_vars


def get_relevant_variables(env_vars: dict) -> dict:
    """Extract variables with descriptions from environment registry."""
    variables = {}
    
    for key, config in ENVIRONMENT_VARIABLES.items():
        # Try environment variable first, then .env file
        value = os.getenv(key) or env_vars.get(key)
        
        if value:
            # Store value with description for Airflow
            variables[key] = {
                'value': value,
                'description': config.get('description', '')
            }
    
    return variables


def generate_variables_json(output_path: Path, dry_run: bool = False):
    """Generate variables.json from environment."""
    print("Generating Airflow variables from environment...")
    
    # Load from .env file
    project_root = Path(__file__).parent.parent
    env_path = project_root / '.env'
    
    env_vars = load_env_file(env_path)
    variables = get_relevant_variables(env_vars)
    
    if not variables:
        print("Warning: No variables found. Make sure .env file is configured.")
        sys.exit(1)
    
    print(f"Found {len(variables)} variables")
    
    if dry_run:
        print("\nVariables to be generated:")
        for key, var_data in variables.items():
            value = var_data['value']
            desc = var_data['description']
            
            # Mask sensitive values
            if is_sensitive(key):
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value
            
            print(f"   {key}: {display_value}")
            print(f"      └─ {desc}")
        return
    
    # Write variables.json (Airflow format with descriptions)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(variables, f, indent=2, sort_keys=True)
    
    print(f"Generated: {output_path}")
    print(f"  - {len(variables)} variables with descriptions")
    print("  - Variables will be encrypted by Airflow using Fernet key")
    print("  - Descriptions visible in Airflow UI")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Airflow variables from .env')
    parser.add_argument('--output', default='airflow/variables/variables.json', help='Output path')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be generated')
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    output_path = project_root / args.output
    
    try:
        generate_variables_json(output_path, args.dry_run)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
