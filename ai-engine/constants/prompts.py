"""
Prompt Constants
================
Constants and fallback prompts for article generation.

Note: Primary prompts are stored in the database (prompts table).
These are fallback defaults if database prompts are not available.
"""

# Prompt names used in the system
PROMPT_NAMES = {
    'EXTRACT_COMPONENTS': 'extract_article_components',
    'GENERATE_BLOCKS': 'generate_article_blocks',
    'GENERATE_SLUG': 'generate_slug',
    'VALIDATE_READABILITY': 'validate_readability',
    'VALIDATE_ENGAGEMENT': 'validate_engagement',
    'VALIDATE_ACCURACY': 'validate_accuracy',
    'VALIDATE_STRUCTURE': 'validate_structure',
    'SYSTEM_PROMPT': 'docetl_pipeline_system',
    'REGENERATE_WITH_FEEDBACK': 'regenerate_with_feedback',
}

# Fallback prompts (used if database is unavailable)
FALLBACK_PROMPTS = {
    'extract_article_components': """
    You are a science communicator transforming research papers into engaging articles.

    Research Paper:
    Title: {{ input.title }}
    Abstract: {{ input.abstract }}
    Full Text: {{ input.extracted_text[:3000] }}

    Extract:
    1. engaging_title: Compelling, accessible title (max 100 chars)
    2. description: 2-3 sentence hook (150-250 words)
    3. keywords: 5-7 relevant keywords
    """,

    'generate_article_blocks': """
    Transform the paper content into structured article blocks.

    Paper: {{ input.engaging_title }}
    Description: {{ input.description }}
    Abstract: {{ input.abstract }}

    Generate blocks: TITLE, PARAGRAPH (hook), SUBHEADING, PARAGRAPH (findings),
    QUOTE, SUBHEADING, PARAGRAPH (methodology), SUBHEADING, PARAGRAPH (implications),
    PARAGRAPH (conclusion)

    Use active voice, present tense, 8th-grade reading level.

    IMPORTANT: Output as valid JSON array for blocks_json with objects containing:
    block_type, content, order_index
    """,

    'docetl_pipeline_system': """
    You are a science communication expert transforming academic research into
    engaging, accessible articles. Target educated general audience. Balance
    accuracy with readability. Focus on human impact.
    """,
}

# Validation thresholds
VALIDATION_THRESHOLDS = {
    'MIN_READABILITY_SCORE': 7.0,
    'MIN_ENGAGEMENT_SCORE': 7.0,
    'MIN_ACCURACY_SCORE': 9.0,
}

# Article structure requirements
STRUCTURE_REQUIREMENTS = {
    'MIN_BLOCKS': 5,
    'MAX_BLOCKS': 20,
    'MIN_WORD_COUNT': 500,
    'MAX_WORD_COUNT': 2000,
    'REQUIRED_BLOCK_TYPES': ['title', 'paragraph'],
    'RECOMMENDED_BLOCK_TYPES': ['title', 'paragraph', 'subheading', 'quote'],
}

# DocETL operation names
DOCETL_OPERATIONS = {
    'EXTRACT': 'extract_components',
    'SLUG': 'generate_slug',
    'BLOCKS': 'generate_blocks',
    'VALIDATE_READ': 'validate_readability',
    'VALIDATE_ENGAGE': 'validate_engagement',
    'VALIDATE_ACCURACY': 'validate_accuracy',
}

