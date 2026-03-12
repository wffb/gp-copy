BEGIN;

-- ===========================================
-- Article Generation Prompts
-- ===========================================

-- 1. Extract Article Components (DocETL Map Operation)
INSERT INTO prompts (name, type, description, template_content, prompt_metadata, version, is_active)
VALUES (
    'extract_article_components',
    'article',
    'Extract title, description, keywords from research paper with content planning',
    '{% set paper = input %}
You are a science communicator transforming research papers into engaging articles for curious readers.

**Research Paper:**
Title: {{ paper.title }}
Abstract: {{ paper.abstract }}
Full Text: {{ paper.extracted_text[:3000] }}...

**Task:** Extract structured components for an engaging article.

**Output Requirements:**
1. **engaging_title**: Rewrite the title to be compelling and accessible (max 100 chars)
   - Make it catchy but accurate
   - Avoid clickbait
   - Focus on the key insight or discovery

2. **description**: Write a 2-3 sentence hook that captures interest (150-250 words)
   - Lead with the most exciting or important finding
   - Explain why this matters to readers
   - Make it accessible to non-experts

3. **keywords**: Extract 5-7 relevant keywords
   - Mix of technical and accessible terms
   - Reflect main topics and themes
   - Useful for search and categorization

**Content Planning (for next steps):**
As you extract these components, think about the article structure:
   - Hook paragraph: Opening that grabs attention and explains why this research matters
   - Key findings: Main discoveries explained simply, highlighting what makes them significant
   - Methodology summary: How the research was done in accessible terms (avoid technical jargon)
   - Implications: Why this matters to readers, real-world applications, and future impact
   - Conclusion: Memorable closing thought that ties it all together

Keep language accessible, avoid jargon, and focus on the human impact.',
    jsonb_build_object(
        'temperature', 0.7,
        'max_tokens', 2000,
        'model', 'gpt-4o-mini'
    ),
    1,
    true
);

-- 2. Generate Article Blocks (DocETL Map Operation)
INSERT INTO prompts (name, type, description, template_content, prompt_metadata, version, is_active)
VALUES (
    'generate_article_blocks',
    'article',
    'Convert paper content into structured article blocks with proper formatting',
    '{% set paper = input %}
Transform the paper content into structured article blocks.

**Paper Context:**
Title: {{ paper.engaging_title }}
Description: {{ paper.description }}
Keywords: {{ paper.keywords }}
Abstract: {{ paper.abstract }}
Full Text Excerpt: {{ paper.extracted_text[:2000] }}...

**Generate blocks in this exact order:**

1. **TITLE** block: Use {{ paper.engaging_title }}
2. **PARAGRAPH** block: Hook paragraph (100-150 words)
3. **SUBHEADING** block: "Key Findings"
4. **PARAGRAPH** block: Key findings explained (150-200 words)
5. **QUOTE** block: Most impactful finding as a pull quote
6. **SUBHEADING** block: "How They Did It"
7. **PARAGRAPH** block: Methodology summary (100-150 words)
8. **SUBHEADING** block: "Why This Matters"
9. **PARAGRAPH** block: Implications (150-200 words)
10. **PARAGRAPH** block: Conclusion (80-120 words)

**Writing Guidelines:**
- Use active voice and present tense
- Explain technical terms in parentheses
- Include transitions between sections
- Target 8th-grade reading level
- Make it engaging and human

**IMPORTANT OUTPUT FORMAT:**
You MUST output a valid JSON array string for blocks_json containing objects with:
- block_type: One of [title, paragraph, subheading, quote]
- content: The actual text content
- order_index: Sequential number starting from 0

Example format for blocks_json:
[{"block_type": "title", "content": "Title text", "order_index": 0}, {"block_type": "paragraph", "content": "Paragraph text...", "order_index": 1}]',
    jsonb_build_object(
        'temperature', 0.7,
        'max_tokens', 3000,
        'model', 'gpt-4o-mini'
    ),
    1,
    true
);

-- 3. Generate Slug
INSERT INTO prompts (name, type, description, template_content, prompt_metadata, version, is_active)
VALUES (
    'generate_slug',
    'article',
    'Generate URL-friendly slug from article title and arxiv_id',
    '{% set paper = input %}
Create a URL-friendly slug from: {{ paper.engaging_title }}
ArXiv ID: {{ paper.arxiv_id }}

Rules:
- Lowercase only
- Replace spaces/special chars with hyphens
- Max 60 characters
- Append arxiv_id at end (replace dots with hyphens)
- No consecutive hyphens

Example: "quantum-computing-breakthrough-2301-12345"',
    jsonb_build_object(
        'temperature', 0.3,
        'max_tokens', 100,
        'model', 'gpt-4o-mini'
    ),
    1,
    true
);

-- ===========================================
-- Validation Prompts (LLM as Judge)
-- ===========================================

-- 4. Validate Readability
INSERT INTO prompts (name, type, description, template_content, prompt_metadata, version, is_active)
VALUES (
    'validate_readability',
    'article',
    'Assess article readability for non-expert audience',
    '{% set article = input %}
Evaluate the readability of this article for a general audience.

**Article Title:** {{ article.engaging_title }}
**Content:** {{ article.blocks_json }}

**Evaluation Criteria:**
1. Language complexity (is jargon explained?)
2. Sentence structure (varied but clear?)
3. Paragraph flow (smooth transitions?)
4. Engagement level (holds interest?)
5. Accessibility (understandable to non-experts?)

**Score 0-10 and provide:**
- readability_score: (0-10)
- strengths: (list 2-3)
- weaknesses: (list issues if any)
- suggestions: (how to improve if score < 7)

Target: Scores 7+ pass, below 7 need revision.',
    jsonb_build_object(
        'temperature', 0.3,
        'max_tokens', 800,
        'model', 'gpt-4o-mini'
    ),
    1,
    true
);

-- 5. Validate Engagement
INSERT INTO prompts (name, type, description, template_content, prompt_metadata, version, is_active)
VALUES (
    'validate_engagement',
    'article',
    'Assess article engagement and narrative quality',
    '{% set article = input %}
Evaluate the engagement quality of this article.

**Article Title:** {{ article.engaging_title }}
**Content:** {{ article.blocks_json }}

**Evaluation Criteria:**
1. Hook strength (does opening grab attention?)
2. Narrative flow (compelling story arc?)
3. Human interest (relatable and relevant?)
4. Memorable insights (takeaways that stick?)
5. Emotional connection (evokes curiosity/wonder?)

**Score 0-10 and provide:**
- engagement_score: (0-10)
- hook_quality: (assessment of opening)
- narrative_strengths: (what works well)
- improvement_areas: (if score < 7)

Target: Scores 7+ pass, below 7 need revision.',
    jsonb_build_object(
        'temperature', 0.3,
        'max_tokens', 800,
        'model', 'gpt-4o-mini'
    ),
    1,
    true
);

-- 6. Validate Accuracy
INSERT INTO prompts (name, type, description, template_content, prompt_metadata, version, is_active)
VALUES (
    'validate_accuracy',
    'article',
    'Verify article accuracy against source paper',
    '{% set article = input %}
Verify this article accurately represents the source paper.

**Source Paper:**
Title: {{ article.title }}
Abstract: {{ article.abstract }}
Key Excerpts: {{ article.extracted_text[:2000] }}...

**Generated Article:**
Title: {{ article.engaging_title }}
Content: {{ article.blocks_json }}

**Evaluation Criteria:**
1. Factual accuracy (no hallucinations?)
2. Claim verification (statements match source?)
3. Context preservation (meaning maintained?)
4. Appropriate simplification (not distorted?)
5. Attribution clarity (findings vs interpretation?)

**Score 0-10 and provide:**
- accuracy_score: (0-10)
- verified_claims: (count of accurate claims)
- concerns: (any inaccuracies or distortions)
- severity: (critical/minor if issues found)

Target: Scores 9+ pass, below 9 need revision.',
    jsonb_build_object(
        'temperature', 0.2,
        'max_tokens', 1000,
        'model', 'gpt-4o-mini'
    ),
    1,
    true
);

-- 7. Validate Structure
INSERT INTO prompts (name, type, description, template_content, prompt_metadata, version, is_active)
VALUES (
    'validate_structure',
    'article',
    'Check article structure and completeness',
    '{% set article = input %}
Validate the structural completeness of this article.

**Article Blocks:**
{% for block in article.blocks %}
- {{ block.block_type }}: {{ block.content[:100] }}...
{% endfor %}

**Required Elements:**
1. Title block present
2. Opening paragraph (hook)
3. At least 2 subheadings
4. 4-6 body paragraphs
5. At least 1 quote/highlight
6. Logical flow and order
7. Closing paragraph

**Check:**
- block_count: (total blocks)
- missing_elements: (list any required elements missing)
- structure_issues: (order problems, gaps)
- word_count: (total words in paragraphs)

**Pass Criteria:**
- All required elements present
- 500-2000 total words
- Logical block ordering',
    jsonb_build_object(
        'temperature', 0.1,
        'max_tokens', 600,
        'model', 'gpt-4o-mini'
    ),
    1,
    true
);

-- ===========================================
-- System Prompts for DocETL Pipeline Context
-- ===========================================

-- 8. DocETL Pipeline System Prompt
INSERT INTO prompts (name, type, description, template_content, prompt_metadata, version, is_active)
VALUES (
    'docetl_pipeline_system',
    'article',
    'System-level context for DocETL article generation pipeline',
    'You are a science communication expert working on a platform that transforms academic research papers into engaging, accessible articles for a general audience.

**Your Goals:**
- Make complex research understandable and exciting
- Maintain scientific accuracy while simplifying language
- Create articles that hook readers and keep them engaged
- Target educated general audience (not specialists)
- Write at 8th-10th grade reading level

**Your Audience:**
Curious, educated readers who:
- Want to stay informed about scientific advances
- May not have technical background in the field
- Appreciate clear explanations over jargon
- Value both accuracy and readability
- Are looking for "why this matters" insights

**Quality Standards:**
- Every claim must be traceable to source paper
- Technical terms must be explained in simple language
- Articles should tell a story, not just list facts
- Focus on human impact and real-world implications
- Balance accessibility with intellectual respect for readers',
    jsonb_build_object(
        'temperature', 0.7,
        'model', 'gpt-4o-mini'
    ),
    1,
    true
);

-- ===========================================
-- Regeneration Prompts (for failed validations)
-- ===========================================

-- 9. Regenerate with Feedback
INSERT INTO prompts (name, type, description, template_content, prompt_metadata, version, is_active)
VALUES (
    'regenerate_with_feedback',
    'article',
    'Regenerate article blocks incorporating validation feedback',
    '{% set paper = input %}
{% set feedback = input.validation_feedback %}
Regenerate article blocks addressing the following feedback.

**Original Paper:**
Title: {{ paper.title }}
Abstract: {{ paper.abstract }}
Full Text: {{ paper.extracted_text[:2000] }}...

**Validation Feedback:**
Readability Issues: {{ feedback.readability_weaknesses }}
Engagement Issues: {{ feedback.engagement_weaknesses }}
Accuracy Concerns: {{ feedback.accuracy_concerns }}

**Your Task:**
Rewrite the article blocks addressing ALL feedback points.
Focus on:
1. Simplifying language if readability < 7
2. Strengthening hook/narrative if engagement < 7
3. Verifying all claims if accuracy < 9
4. Maintaining structure and completeness

Generate complete article blocks (same format as before) with improvements applied.',
    jsonb_build_object(
        'temperature', 0.7,
        'max_tokens', 3000,
        'model', 'gpt-4o-mini'
    ),
    1,
    true
);

COMMIT;

