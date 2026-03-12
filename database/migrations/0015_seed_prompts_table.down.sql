BEGIN;

-- Delete all seeded prompts
DELETE FROM prompts WHERE name IN (
    'extract_article_components',
    'generate_article_blocks',
    'generate_slug',
    'validate_readability',
    'validate_engagement',
    'validate_accuracy',
    'validate_structure',
    'docetl_pipeline_system',
    'regenerate_with_feedback'
);

COMMIT;

