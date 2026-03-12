"""
Environment Variables Registry
===============================
Single source of truth for all environment variables with descriptions.
"""

# Variable definitions: (key, description, category)
ENVIRONMENT_VARIABLES = {
    # Core Configuration
    'ENVIRONMENT': {
        'description': 'Deployment environment (development/staging/production)',
        'category': 'Core',
        'required': True,
    },
    'LOG_LEVEL': {
        'description': 'Logging level (DEBUG/INFO/WARNING/ERROR)',
        'category': 'Core',
        'required': True,
    },
    'DATABASE_URL': {
        'description': 'PostgreSQL connection string for ETL database',
        'category': 'Database',
        'required': True,
        'sensitive': True,
    },
    'AIRFLOW_DB_NAME': {
        'description': 'Database name for Airflow metadata (default: zara_airflow)',
        'category': 'Database',
        'required': False,
    },
    'ETL_DB_NAME': {
        'description': 'Database name for ETL data (default: zara_etl)',
        'category': 'Database',
        'required': False,
    },
    'AIRFLOW_DATABASE_URL': {
        'description': 'Override PostgreSQL connection string for Airflow (for external databases)',
        'category': 'Database',
        'required': False,
        'sensitive': True,
    },
    'SKIP_DB_CREATION': {
        'description': 'Skip database creation for external/managed databases (default: false)',
        'category': 'Database',
        'required': False,
    },
    
    # arXiv Ingestion - Required
    'ARXIV_MAX_RESULTS': {
        'description': 'Maximum papers to fetch per ingestion run',
        'category': 'arXiv Ingestion',
        'required': True,
    },
    'ARXIV_MAX_RESULTS_PER_REQUEST': {
        'description': 'Batch size for processing papers',
        'category': 'arXiv Ingestion',
        'required': True,
    },
    
    # arXiv Ingestion - Optional
    'ARXIV_CATEGORIES': {
        'description': 'Comma-separated arXiv categories to filter (e.g., cs.AI,cs.LG)',
        'category': 'arXiv Ingestion',
        'required': False,
    },
    'ARXIV_SORT_BY': {
        'description': 'Sort papers by (submittedDate/lastUpdatedDate/relevance)',
        'category': 'arXiv Ingestion',
        'required': False,
    },
    'ARXIV_SORT_ORDER': {
        'description': 'Sort order (ascending/descending)',
        'category': 'arXiv Ingestion',
        'required': False,
    },
    'ARXIV_START_INDEX': {
        'description': 'Starting index for pagination',
        'category': 'arXiv Ingestion',
        'required': False,
    },
    'ARXIV_RATE_LIMIT_SECONDS': {
        'description': 'Delay between API calls in seconds',
        'category': 'arXiv Ingestion',
        'required': False,
    },
    'ARXIV_MAX_RETRIES': {
        'description': 'Maximum retry attempts for failed operations',
        'category': 'arXiv Ingestion',
        'required': False,
    },
    
    # Quality Filter - PDF Structure
    'QF_PDF_MIN_PAGES': {
        'description': 'Minimum page count for valid papers',
        'category': 'Quality Filter',
        'required': False,
    },
    'QF_PDF_MAX_PAGES': {
        'description': 'Maximum page count for valid papers',
        'category': 'Quality Filter',
        'required': False,
    },
    'QF_PDF_MIN_SIZE_KB': {
        'description': 'Minimum PDF file size in KB',
        'category': 'Quality Filter',
        'required': False,
    },
    'QF_PDF_MAX_SIZE_MB': {
        'description': 'Maximum PDF file size in MB',
        'category': 'Quality Filter',
        'required': False,
    },
    'QF_TEXT_MIN_CHARS': {
        'description': 'Minimum extractable text characters',
        'category': 'Quality Filter',
        'required': False,
    },
    
    # Quality Filter - Content Quality
    'QF_LANGUAGE': {
        'description': 'Required language code (e.g., en)',
        'category': 'Quality Filter',
        'required': False,
    },
    'QF_ABSTRACT_MIN_WORDS': {
        'description': 'Minimum abstract word count',
        'category': 'Quality Filter',
        'required': False,
    },
    'QF_ABSTRACT_MAX_WORDS': {
        'description': 'Maximum abstract word count',
        'category': 'Quality Filter',
        'required': False,
    },
    
    # Quality Filter - Metadata
    'QF_PRIORITY_CATEGORIES': {
        'description': 'Comma-separated priority arXiv categories',
        'category': 'Quality Filter',
        'required': False,
    },
    'QF_EXCLUDE_CATEGORIES': {
        'description': 'Comma-separated excluded arXiv categories',
        'category': 'Quality Filter',
        'required': False,
    },
    'QF_RECENCY_YEARS': {
        'description': 'Maximum paper age in years',
        'category': 'Quality Filter',
        'required': False,
    },
    
    # Quality Filter - Format Validation
    'QF_MIN_SECTIONS': {
        'description': 'Minimum standard section headers required',
        'category': 'Quality Filter',
        'required': False,
    },
    'QF_MIN_FIGURES': {
        'description': 'Minimum figures/tables required',
        'category': 'Quality Filter',
        'required': False,
    },
    'QF_MAX_FIGURES': {
        'description': 'Maximum figures/tables (to avoid slides)',
        'category': 'Quality Filter',
        'required': False,
    },
    
    # Quality Filter - Processing
    'QF_BATCH_SIZE': {
        'description': 'Papers to process per batch',
        'category': 'Quality Filter',
        'required': False,
    },
    'QF_ENABLE_PDF_DOWNLOAD': {
        'description': 'Enable PDF downloading for quality checks',
        'category': 'Quality Filter',
        'required': False,
    },
    
    # OpenAI API Configuration (Required for DocETL)
    'OPENAI_API_KEY': {
        'description': 'OpenAI API key for DocETL processing (REQUIRED) - or Bearer token for self-hosted AI',
        'category': 'DocETL Processing',
        'required': True,
        'sensitive': True,
    },
    'OPENAI_API_BASE': {
        'description': 'Custom OpenAI API base URL (for self-hosted AI endpoints)',
        'category': 'DocETL Processing',
        'required': False,
        'sensitive': False,
    },
    'DEFAULT_MODEL': {
        'description': 'Default model name (e.g., gpt-4o-mini or gpt-oss:20b)',
        'category': 'AI Generation',
        'required': False,
    },
    # DocETL Processing - Core
    'DOCETL_BATCH_SIZE': {
        'description': 'Papers to process per batch',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_ENABLE': {
        'description': 'Enable/disable DocETL processing pipeline',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_MAX_RETRIES': {
        'description': 'Max retry attempts per paper',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_TIMEOUT_SECONDS': {
        'description': 'Timeout per paper processing',
        'category': 'DocETL Processing',
        'required': False,
    },
    
    # DocETL Processing - LLM Configuration
    'DOCETL_LLM_PROVIDER': {
        'description': 'LLM provider (openai, anthropic)',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_LLM_MODEL': {
        'description': 'Model for content generation',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_LLM_JUDGE_MODEL': {
        'description': 'Model for validation (cheaper)',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_LLM_TEMPERATURE': {
        'description': 'Generation creativity (0.0-1.0)',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_LLM_MAX_TOKENS': {
        'description': 'Max tokens per generation',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_LLM_REQUEST_TIMEOUT': {
        'description': 'LLM request timeout in seconds (for slow self-hosted models)',
        'category': 'DocETL Processing',
        'required': False,
    },
    
    # DocETL Processing - Article Settings
    'DOCETL_MIN_BLOCKS': {
        'description': 'Minimum blocks per article',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_MAX_BLOCKS': {
        'description': 'Maximum blocks per article',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_MIN_WORD_COUNT': {
        'description': 'Minimum article word count',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_MAX_WORD_COUNT': {
        'description': 'Maximum article word count',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_PARAGRAPH_TARGET_WORDS': {
        'description': 'Target words per paragraph',
        'category': 'DocETL Processing',
        'required': False,
    },
    
    # DocETL Processing - Validation
    'DOCETL_MIN_READABILITY_SCORE': {
        'description': 'Min readability score (0-10)',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_MIN_ENGAGEMENT_SCORE': {
        'description': 'Min engagement score (0-10)',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_MIN_ACCURACY_SCORE': {
        'description': 'Min accuracy score (0-10)',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_ENABLE_VALIDATION': {
        'description': 'Enable LLM validation',
        'category': 'DocETL Processing',
        'required': False,
    },
    
    # DocETL Processing - Gleaning (Automatic Retry with Feedback)
    'DOCETL_ENABLE_GLEANING': {
        'description': 'Enable gleaning (automatic retries with validation feedback)',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_GLEANING_ROUNDS': {
        'description': 'Number of gleaning rounds (retries with feedback)',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_VALIDATION_PROMPT': {
        'description': 'Custom validation prompt for gleaning (optional)',
        'category': 'DocETL Processing',
        'required': False,
    },
    
    # DocETL Processing - PDF
    'DOCETL_EXTRACT_FULL_TEXT': {
        'description': 'Extract full PDF text',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_EXTRACT_FIGURES': {
        'description': 'Extract figure references',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_MAX_PDF_SIZE_MB': {
        'description': 'Max PDF size to process (MB)',
        'category': 'DocETL Processing',
        'required': False,
    },
    'DOCETL_PDF_DOWNLOAD_TIMEOUT': {
        'description': 'PDF download timeout (seconds)',
        'category': 'DocETL Processing',
        'required': False,
    },
    
    # DocETL Processing - Internals
    'DOCETL_INTERMEDIATE_DIR': {
        'description': 'Directory for DocETL intermediate files',
        'category': 'DocETL Processing',
        'required': False,
    },
}


def get_variable_description(var_name: str) -> str:
    """Get description for a variable."""
    return ENVIRONMENT_VARIABLES.get(var_name, {}).get('description', '')


def is_sensitive(var_name: str) -> bool:
    """Check if variable contains sensitive data."""
    return ENVIRONMENT_VARIABLES.get(var_name, {}).get('sensitive', False)