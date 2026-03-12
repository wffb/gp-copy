BEGIN;

-- Seed one paper + article per top-level field (choose any subfield deterministically)
-- Idempotent: papers keyed by arxiv_id = 'seed-field:'||field_code, articles by slug

WITH fields_top(code, top_field_id) AS (
  SELECT code, id AS top_field_id
  FROM fields
  WHERE parent_id IS NULL
    AND code IN ('cs','econ','eess','math','physics','q-bio','q-fin','stat')
),
sub_choice AS (
  SELECT
    ft.code,
    ft.top_field_id AS top_id,
    (
      SELECT id
      FROM fields sf
      WHERE sf.parent_id = ft.top_field_id
      ORDER BY sf.sort_order NULLS LAST, sf.code
      LIMIT 1
    ) AS sub_id
  FROM fields_top ft
),
content(code, title, description, slug) AS (
  VALUES
    ('cs',
     'AI Engineering: From Models to Systems',
     'What it takes to ship AI today: evaluation-first development, data and feedback loops, safety guardrails, and the infrastructure that turns state-of-the-art models into reliable products.',
     'ai-engineering-from-models-to-systems'
    ),
    ('econ',
     'Macroeconomics Nowcasting with Machine Learning',
     'A practical guide to building high-frequency indicators for GDP and inflation, handling revisions, and blending econometrics with modern ML.',
     'macroeconomics-nowcasting-with-ml'
    ),
    ('eess',
     'Signals, Systems, and Learning',
     'How classical DSP meets deep learning: differentiable filters, learned priors, and real-time constraints on edge devices.',
     'signals-systems-and-learning'
    ),
    ('math',
     'The Shape of Proof: Modern Mathematics',
     'Trends from category-theoretic abstractions to computer-assisted proof, and how new tools are changing collaboration.',
     'the-shape-of-proof-modern-mathematics'
    ),
    ('physics',
     'Quantum Frontiers: From Qubits to Materials',
     'Progress in quantum error correction, simulators, and materials discovery driven by first-principles modeling and ML-accelerated experiments.',
     'quantum-frontiers-from-qubits-to-materials'
    ),
    ('q-bio',
     'Cells as Programs: Computation in Biology',
     'Viewing gene circuits, signaling, and morphology through the lens of computation to design, predict, and control living systems.',
     'cells-as-programs-computation-in-biology'
    ),
    ('q-fin',
     'Market Microstructure in the ML Era',
     'Order books, liquidity, and execution under adaptive algorithms—what changes and what stays the same when models trade.',
     'market-microstructure-in-the-ml-era'
    ),
    ('stat',
     'Causal Inference at Scale: Practical Patterns',
     'Designing robust A/Bs and observational studies with heterogeneous effects, interference, and production constraints.',
     'causal-inference-at-scale-practical-patterns'
    )
),
prepared AS (
  SELECT sc.code, sc.top_id, sc.sub_id, c.title, c.description, c.slug
  FROM sub_choice sc
  JOIN content c USING (code)
),
ins_papers AS (
  INSERT INTO papers (
    title, abstract, arxiv_id, primary_field_id, primary_subfield_id,
    subjects, categories, pdf_url, published_date, submitted_date, status
  )
  SELECT
    p.title,
    p.description,
    'seed-field:' || p.code,
    p.top_id,
    p.sub_id,
    ARRAY[p.code],
    ARRAY[p.code],
    NULL,
    NOW() - INTERVAL '7 days',
    NOW() - INTERVAL '8 days',
    'published'
  FROM prepared p
  WHERE NOT EXISTS (
    SELECT 1 FROM papers existing WHERE existing.arxiv_id = 'seed-field:' || p.code
  )
  RETURNING id, arxiv_id
),
papers_final AS (
  SELECT p2.id, p.code, p.title, p.description, p.slug
  FROM prepared p
  JOIN (
    SELECT id, arxiv_id FROM ins_papers
    UNION ALL
    SELECT id, arxiv_id FROM papers WHERE arxiv_id IN (SELECT 'seed-field:' || code FROM prepared)
  ) p2 ON p2.arxiv_id = 'seed-field:' || p.code
),
upsert_articles AS (
  INSERT INTO articles (
    paper_id, title, description, keywords, slug, status, featured_image_url, is_edited, view_count, engagement_metrics
  )
  SELECT
    pf.id,
    pf.title,
    pf.description,
    ARRAY[pf.code],
    pf.slug,
    'published',
    NULL,
    FALSE,
    0,
    '{}'::jsonb
  FROM papers_final pf
  ON CONFLICT (slug) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    keywords = EXCLUDED.keywords,
    status = EXCLUDED.status,
    updated_at = NOW()
  RETURNING id AS article_id, slug
),
custom AS (
  SELECT * FROM (VALUES
    ('cs',      'Evaluation loops, data pipelines, observability, guardrails, scalable serving, and continuous delivery for models.',
                'Componentized model stacks, small+specialist models, real-time feedback, and safety-by-default platforms.',
                '"Ship value, not just models."'),
    ('econ',    'Nowcasting from alternative data, mixed-frequency models, revision-aware training, and uncertainty quantification.',
                'Unified pipelines from ingestion to policy dashboards, with causal+forecast hybrids and auditable decisions.',
                '"Timely signals beat perfect hindsight."'),
    ('eess',    'Differentiable signal processing, neural codecs, adaptive filtering, and spectral priors meeting deep learning.',
                'Edge-first model design, learned DSP blocks, and hardware–model co-design for latency and power.',
                '"Learned filters, real-world constraints."'),
    ('math',    'Abstraction layers, formalization, proof assistants, and computable algebra for exploration and verification.',
                'Interactive theorem proving in research workflows and executable, reproducible mathematical papers.',
                '"Proofs are products of design."'),
    ('physics', 'Quantum error correction, variational algorithms, and materials informatics accelerated by simulation and ML.',
                'Scaling to logical qubits and AI-driven autonomous discovery loops across theory and experiment.',
                '"Noise is the enemy; structure is the ally."'),
    ('q-bio',   'Gene circuits, single-cell atlases, dynamical systems modeling, and control-theoretic designs for biology.',
                'Programmable tissues and closed-loop bio experiments with predictive, causal, and safe controllers.',
                '"Cells compute with matter."'),
    ('q-fin',   'Microstructure modeling, market impact estimation, agent-based simulations, and risk-aware learning.',
                'Safer auto-execution, regulation-aware ML, and interpretable strategies in production.',
                '"Liquidity is a moving target."'),
    ('stat',    'Causal graphs, identification, heterogeneity, interference, and robust estimation under constraints.',
                'Causal CI/CD with experiment design, off-policy evaluation, and continuous validation at scale.',
                '"Assumptions are features; make them explicit."')
  ) AS t(code, key_ideas, future, quote)
)
INSERT INTO article_blocks (article_id, block_type, content, order_index)
-- 0: Title
SELECT ua.article_id, 'title'::block_type, p.title, 0
FROM upsert_articles ua
JOIN prepared p USING (slug)
UNION ALL
-- 1: Intro paragraph
SELECT ua.article_id, 'paragraph'::block_type, p.description, 1
FROM upsert_articles ua
JOIN prepared p USING (slug)
UNION ALL
-- 2: Key Ideas subheading
SELECT ua.article_id, 'subheading'::block_type, 'Key Ideas', 2
FROM upsert_articles ua
UNION ALL
-- 3: Key Ideas paragraph (per field)
SELECT ua.article_id, 'paragraph'::block_type, c.key_ideas, 3
FROM upsert_articles ua
JOIN prepared p USING (slug)
JOIN custom c ON c.code = p.code
UNION ALL
-- 4: Where It's Going subheading
SELECT ua.article_id, 'subheading'::block_type, 'Where it''s going', 4
FROM upsert_articles ua
UNION ALL
-- 5: Future paragraph (per field)
SELECT ua.article_id, 'paragraph'::block_type, c.future, 5
FROM upsert_articles ua
JOIN prepared p USING (slug)
JOIN custom c ON c.code = p.code
UNION ALL
-- 6: Quote (per field)
SELECT ua.article_id, 'quote'::block_type, c.quote, 6
FROM upsert_articles ua
JOIN prepared p USING (slug)
JOIN custom c ON c.code = p.code
ON CONFLICT (article_id, order_index) DO UPDATE SET
  content = EXCLUDED.content,
  updated_at = NOW();

COMMIT;
