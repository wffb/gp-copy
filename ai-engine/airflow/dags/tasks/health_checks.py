"""
Health Check Tasks
==================
System health, connectivity, and configuration validation tasks.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any

from airflow.sdk import task, Variable
import psycopg2

from constants.environment import ENVIRONMENT_VARIABLES, is_sensitive

logger = logging.getLogger(__name__)

# Build variable lists from central registry
REQUIRED_VARS = [k for k, v in ENVIRONMENT_VARIABLES.items() if v.get('required', False)]
OPTIONAL_VARS = [k for k, v in ENVIRONMENT_VARIABLES.items() if not v.get('required', False)]


def _check_variable(var_name: str) -> tuple:
    """Check single variable, returns (found, value, source)."""
    try:
        value = Variable.get(var_name, default=None) or os.getenv(var_name)
        if value:
            sensitive = is_sensitive(var_name)
            masked = f"{value[:8]}..." if sensitive and len(value) > 8 else ("***" if sensitive else value)
            source = "airflow_variable" if Variable.get(var_name, default=None) else "environment"
            return True, masked, source
        return False, None, None
    except Exception as e:
        logger.warning(f"Error checking {var_name}: {e}")
        return False, None, None


@task(task_id="validate_airflow_variables")
def validate_airflow_variables() -> Dict[str, Any]:
    """Validate required and optional Airflow Variables."""
    logger.info("Validating Airflow variables...")
    
    required_vars, missing_required = {}, []
    optional_vars, missing_optional = {}, []
    
    for var in REQUIRED_VARS:
        found, value, source = _check_variable(var)
        if found:
            required_vars[var] = {"value": value, "source": source}
        else:
            missing_required.append(var)
            logger.error(f"Missing required: {var}")
    
    for var in OPTIONAL_VARS:
        found, value, source = _check_variable(var)
        if found:
            optional_vars[var] = {"value": value, "source": source}
        else:
            missing_optional.append(var)
    
    passed = len(missing_required) == 0
    logger.info(f"Variables: {len(required_vars)}/{len(REQUIRED_VARS)} required, {len(optional_vars)}/{len(OPTIONAL_VARS)} optional")
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "required_variables": required_vars,
        "optional_variables": optional_vars,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "validation_passed": passed,
    }


@task(task_id="test_database_connectivity")
def test_database_connectivity() -> Dict[str, Any]:
    """Test database connectivity and schema."""
    logger.info("Testing database...")
    
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "connection_ok": False,
        "table_count": 0,
        "migration_status": "unknown",
    }
    
    try:
        db_url = Variable.get("DATABASE_URL", default=os.getenv("DATABASE_URL"))
        if not db_url:
            raise ValueError("DATABASE_URL not configured")
        
        with psycopg2.connect(db_url) as conn, conn.cursor() as cursor:
            result["connection_ok"] = True
            
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
            result["table_count"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = {row[0] for row in cursor.fetchall()}
            
            expected = {'users', 'roles', 'permissions', 'papers', 'articles', 'author_profiles', 'fields'}
            found = expected & tables
            
            if len(found) == len(expected):
                result["migration_status"] = "complete"
                logger.info(f"Database OK: {result['table_count']} tables, all migrations applied")
            elif len(found) > 0:
                result["migration_status"] = "partial"
                result["missing_tables"] = list(expected - found)
                logger.warning(f"Missing tables: {result['missing_tables']}")
                raise ValueError(f"Migrations incomplete. Missing tables: {result['missing_tables']}")
            else:
                result["migration_status"] = "not_applied"
                logger.error("No expected tables found in database")
                raise ValueError("Migrations not applied. Database schema missing.")
    
    except psycopg2.Error as e:
        result["error"] = str(e)
        logger.error(f"Database connection failed: {e}")
        raise
    except ValueError:
        # Re-raise migration errors
        raise
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Database test failed: {e}")
        raise
    
    return result


@task(task_id="test_external_apis")
def test_external_apis() -> Dict[str, Any]:
    """Test connectivity to external APIs (arXiv only for paper extraction)."""
    logger.info("Testing arXiv API...")
    
    try:
        import requests
        resp = requests.get("http://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=1", timeout=10)
        if resp.status_code == 200:
            logger.info("arXiv API OK")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "arxiv_ok": True,
                "all_ok": True,
            }
        else:
            logger.error(f"arXiv API failed: {resp.status_code}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "arxiv_ok": False,
                "all_ok": False,
                "error": f"Status {resp.status_code}",
            }
    except Exception as e:
        logger.error(f"arXiv API error: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "arxiv_ok": False,
            "all_ok": False,
            "error": str(e)[:100],
        }


@task(task_id="check_system_resources")
def check_system_resources() -> Dict[str, Any]:
    """Check system resources (disk, memory)."""
    logger.info("Checking system resources...")
    
    warnings, errors = [], []
    disk_info = {}
    
    try:
        import shutil, psutil
        
        for path in ["/opt/airflow/data", "/opt/airflow/logs", "/opt/airflow/logs_app", "/opt/airflow/backups", "/tmp"]:
            if os.path.exists(path):
                usage = shutil.disk_usage(path)
                used_pct = (usage.used / usage.total) * 100
                disk_info[path] = round(used_pct, 1)
                
                if used_pct > 95:
                    errors.append(f"{path}: {used_pct:.1f}% full")
                elif used_pct > 85:
                    warnings.append(f"{path}: {used_pct:.1f}% full")
        
        memory = psutil.virtual_memory()
        mem_pct = memory.percent
        if mem_pct > 85:
            warnings.append(f"Memory: {mem_pct:.1f}%")
        
        logger.info(f"Resources OK: {len(warnings)} warnings, {len(errors)} errors")
    
    except Exception as e:
        errors.append(f"Resource check error: {e}")
        logger.error(f"Resource check failed: {e}")
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "disk_usage": disk_info,
        "warnings": warnings,
        "errors": errors,
    }


@task(task_id="generate_health_summary")
def generate_health_summary(vars_ok: Dict, db_ok: Dict, api_ok: Dict, res_ok: Dict) -> Dict[str, Any]:
    """Generate overall health summary from component checks."""
    
    components = {
        "variables": vars_ok.get("validation_passed", False),
        "database": db_ok.get("connection_ok", False),
        "apis": api_ok.get("all_ok", False),
        "resources": len(res_ok.get("errors", [])) == 0,
    }
    
    passed = sum(components.values())
    score = (passed / len(components)) * 100
    status = "healthy" if score == 100 else ("warning" if score >= 75 else "critical")
    
    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": status,
        "score": round(score, 1),
        "components": components,
        "variables": {
            "required": f"{len(vars_ok.get('required_variables', {}))}/{len(REQUIRED_VARS)}",
            "missing": vars_ok.get("missing_required", []),
        },
        "database": {
            "connected": db_ok.get("connection_ok", False),
            "tables": db_ok.get("table_count", 0),
            "migration": db_ok.get("migration_status", "unknown"),
        },
        "apis": {
            "arxiv_ok": api_ok.get("arxiv_ok", False),
        },
        "resources": {
            "warnings": len(res_ok.get("warnings", [])),
            "errors": len(res_ok.get("errors", [])),
        },
    }
    
    logger.info(f"Health: {status.upper()} ({score:.0f}%) - {passed}/{len(components)} components OK")
    logger.info(f"Variables: {summary['variables']['required']}, arXiv: {'OK' if summary['apis']['arxiv_ok'] else 'FAILED'}, DB: {summary['database']['tables']} tables")
    
    return summary

