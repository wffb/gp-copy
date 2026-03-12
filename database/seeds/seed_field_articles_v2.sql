BEGIN;

-- Seed multiple articles across diverse subfields (v2)
-- Idempotent: papers keyed by arxiv_id = 'seed-v2:'||code||':'||variant, articles by slug

WITH top_fields AS (
  SELECT code, id AS top_id
  FROM fields
  WHERE parent_id IS NULL
    AND code IN ('cs','econ','eess','math','physics','q-bio','q-fin','stat')
),
-- Choose two different subfields per top field to diversify from v1
sub_choice_1 AS (
  SELECT tf.code, tf.top_id,
         (
           SELECT id FROM fields sf
           WHERE sf.parent_id = tf.top_id
           ORDER BY sf.sort_order NULLS LAST, sf.code
           LIMIT 1
         ) AS sub_id_1
  FROM top_fields tf
),
sub_choice_2 AS (
  SELECT tf.code, tf.top_id,
         (
           SELECT id FROM fields sf
           WHERE sf.parent_id = tf.top_id
           ORDER BY sf.sort_order NULLS LAST, sf.code
           OFFSET 1 LIMIT 1
         ) AS sub_id_2
  FROM top_fields tf
),
-- Per-field, two distinct article variants with titles, descriptions, and slugs
content(code, variant, title, description, slug,
        para_intro, sub_1, para_1, sub_2, para_2, quote_line, image_url) AS (
  VALUES
    ('cs','a',
     'Engineering Reliable AI Systems',
     'Patterns for building evaluation-first, observable, and safe AI systems in production.',
     'v2-engineering-reliable-ai-systems',
     'From sandboxed deployments to shadow traffic and red-teaming, reliability comes from feedback loops and guardrails.',
     'Evaluation Loops',
     'Treat eval as CI: dataset versioning, slice-aware metrics, and human-in-the-loop triage.',
     'Safety By Default',
     'Use least-privilege model access, policy layers, and rollbackable configs.',
     '"Shipping AI means shipping process."',
     'https://example.com/images/ai-systems.png'
    ),
    ('cs','b',
     'Small Models, Big Impact',
     'Specialist models paired with retrieval and tools can beat monoliths for many workloads.',
     'v2-small-models-big-impact',
     'Latency budgets and cost ceilings often favor compact models with strong retrieval and caching.',
     'Right-size the Model',
     'Quantization, distillation, and instruction-tuning narrow models for task fit.',
     'Tool Use',
     'Externalize skills via search, code-execution, and structured APIs.',
     '"Do more with less compute."',
     'https://example.com/images/small-models.png'
    ),

    ('econ','a',
     'Nowcasting that Survives Revisions',
     'Design nowcasts robust to data revisions, outliers, and structural breaks.',
     'v2-nowcasting-that-survives-revisions',
     'Vintage-aware pipelines, mixed-frequency models, and revision maps keep estimates stable.',
     'Vintage Discipline',
     'Never leak future vintages; lock snapshots and track transformations.',
     'Uncertainty',
     'Report posteriors, intervals, and contributions—not just point estimates.',
     '"Hindsight is not a feature."',
     'https://example.com/images/nowcasting.png'
    ),
    ('econ','b',
     'Policy Evaluation in the Wild',
     'From A/Bs to difference-in-differences, evaluate policy under drift and interference.',
     'v2-policy-evaluation-in-the-wild',
     'Observational designs need diagnostics, placebo tests, and careful identification.',
     'Design First',
     'Define estimands, units, and spillovers before fitting models.',
     'Heterogeneity',
     'Estimate treatment effects that vary across segments and time.',
     '"Assumptions are part of the result."',
     'https://example.com/images/policy-eval.png'
    ),

    ('eess','a',
     'Neural Signal Processing on the Edge',
     'Low-latency learned filters and codecs for streaming audio and sensors.',
     'v2-neural-signal-processing-on-the-edge',
     'DSP meets deep learning: differentiable filters with hardware-aware constraints.',
     'Latency Budgeting',
     'Pipeline for frame sizes, lookahead, and memory reuse.',
     'Compression',
     'Perceptual losses and vector quantization for tiny bitrates.',
     '"Real-time is the harshest teacher."',
     'https://example.com/images/edge-dsp.png'
    ),
    ('eess','b',
     'Learning to See: Image Pipelines',
     'Robust image enhancement pipelines mixing priors and learned components.',
     'v2-learning-to-see-image-pipelines',
     'Classical priors still matter: regularization, physics, and constraints guide learning.',
     'Hybrid Pipelines',
     'Plug learned denoisers and super-resolution into interpretable chains.',
     'Deployment',
     'Quantize and fuse ops; validate quality on realistic distributions.',
     '"Beauty needs constraints."',
     'https://example.com/images/image-pipeline.png'
    ),

    ('math','a',
     'Category Theory for Working Engineers',
     'Interfaces, compositionality, and algebraic reasoning for complex systems.',
     'v2-category-theory-for-working-engineers',
     'Abstract structures help split big problems into small reusable parts.',
     'Compositional Design',
     'Think arrows and objects: composable interfaces, functors as adapters.',
     'Proof to Product',
     'Executable mathematics: property-based testing, proof assistants, and specs.',
     '"Abstraction is leverage, not obscurity."',
     'https://example.com/images/category-theory.png'
    ),
    ('math','b',
     'Probability as a Design Tool',
     'Engineer with randomness: stochastic models, concentration, and tail bounds in practice.',
     'v2-probability-as-a-design-tool',
     'From back-of-the-envelope to rigorous guarantees, probabilistic thinking guides choices.',
     'Concentration',
     'Hoeffding to Bernstein: pick the right tool for the variance.',
     'Tail Risk',
     'Guard against rare-but-costly events; budget for safety margins.',
     '"Expect the unexpected—quantify it."',
     'https://example.com/images/probability.png'
    ),

    ('physics','a',
     'Quantum Error Correction 101',
     'Stabilizer codes, surface codes, and the road to logical qubits.',
     'v2-quantum-error-correction-101',
     'Quantum computation survives noise via redundancy and clever measurements.',
     'Stabilizers',
     'Syndrome extraction detects errors without destroying information.',
     'Scaling',
     'From distance to thresholds: why hardware-software co-design matters.',
     '"Silence the noise, not the signal."',
     'https://example.com/images/qec.png'
    ),
    ('physics','b',
     'From Simulators to Materials',
     'Using quantum and classical simulators to discover new phases and materials.',
     'v2-from-simulators-to-materials',
     'Phase diagrams, many-body effects, and ML-guided exploration close the loop.',
     'Simulation Loops',
     'Active learning on the lattice; surrogate models speed sweeps.',
     'Experiment Ties',
     'Tight iterations between theory, sim, and lab validate discoveries.',
     '"Data is the new microscope."',
     'https://example.com/images/materials.png'
    ),

    ('q-bio','a',
     'Learning in Living Systems',
     'Gene circuits, morphogenesis, and control in biological computation.',
     'v2-learning-in-living-systems',
     'Cells compute with matter: programs built from molecules and forces.',
     'Circuits',
     'Design motifs and feedback: from toggles to oscillators.',
     'Control',
     'Closed-loop experiments enable robust behaviors and safety.',
     '"Biology learns by growing."',
     'https://example.com/images/qbio.png'
    ),
    ('q-bio','b',
     'Single Cells at Scale',
     'From atlases to interventions using high-throughput single-cell assays.',
     'v2-single-cells-at-scale',
     'Latent variable models and causal tools reveal cell state and fate.',
     'Representation',
     'Manifold learning with biological priors for interpretability.',
     'Perturbations',
     'CRISPR screens and lineage tracing map causal mechanisms.',
     '"Maps become controllers."',
     'https://example.com/images/single-cell.png'
    ),

    ('q-fin','a',
     'Execution under Algorithms',
     'Market microstructure meets adaptive agents in modern execution.',
     'v2-execution-under-algorithms',
     'Impact models, inventory risk, and adversarial markets shape optimal policies.',
     'Impact',
     'Calibrate response functions; avoid toxic flow and gaming.',
     'Risk',
     'Balance slippage, inventory, and opportunity costs.',
     '"Liquidity appears, disappears, and costs."',
     'https://example.com/images/execution.png'
    ),
    ('q-fin','b',
     'Interpretable Strategies at Scale',
     'From features to factors: build interpretable trading signals.',
     'v2-interpretable-strategies-at-scale',
     'Regularization and monotonicity constraints keep models grounded.',
     'Signals',
     'Stationarity checks, leakage tests, and live drift monitors.',
     'Governance',
     'Audit trails and risk gates for deployment decisions.',
     '"Explain first, optimize second."',
     'https://example.com/images/factors.png'
    ),

    ('stat','a',
     'Causal Inference Beyond A/B',
     'Handle interference, heterogeneity, and selection with principled designs.',
     'v2-causal-inference-beyond-ab',
     'Plan for network spillovers and time-varying effects before estimation.',
     'Identification',
     'Graphical criteria, front-door paths, and sensitivity analysis.',
     'Validation',
     'Placebo tests, subset checks, and triangulation for robustness.',
     '"Causality is a team sport."',
     'https://example.com/images/causal.png'
    ),
    ('stat','b',
     'Production ML Experimentation',
     'Design experiments and observational studies that survive deployment realities.',
     'v2-production-ml-experimentation',
     'Guard against interference, saturation, and feedback loops at scale.',
     'Power',
     'Sequential tests and variance reduction methods for speed.',
     'Safety',
     'Kill-switches, guardrails, and alerting baked into the plan.',
     '"Measure twice, ship once."',
     'https://example.com/images/experiments.png'
    )
),
prepared AS (
  SELECT c.code,
         c.variant,
         tf.top_id,
         COALESCE(
           CASE WHEN c.variant = 'a' THEN s1.sub_id_1 ELSE s2.sub_id_2 END,
           s1.sub_id_1
         ) AS sub_id, -- fallback to first if second missing
         c.title,
         c.description,
         c.slug,
         c.para_intro,
         c.sub_1,
         c.para_1,
         c.sub_2,
         c.para_2,
         c.quote_line,
         c.image_url
  FROM content c
  JOIN top_fields tf USING (code)
  LEFT JOIN sub_choice_1 s1 USING (code)
  LEFT JOIN sub_choice_2 s2 USING (code)
),
ins_papers AS (
  INSERT INTO papers (
    title, abstract, arxiv_id, primary_field_id, primary_subfield_id,
    subjects, categories, pdf_url, published_date, submitted_date, status
  )
  SELECT
    p.title,
    p.description,
    'seed-v2:' || p.code || ':' || p.variant,
    p.top_id,
    p.sub_id,
    ARRAY[p.code],
    ARRAY[p.code],
    NULL,
    NOW() - INTERVAL '3 days',
    NOW() - INTERVAL '4 days',
    'published'
  FROM prepared p
  WHERE NOT EXISTS (
    SELECT 1 FROM papers existing WHERE existing.arxiv_id = 'seed-v2:' || p.code || ':' || p.variant
  )
  RETURNING id, arxiv_id
),
papers_final AS (
  SELECT p2.id, p.code, p.variant, p.title, p.description, p.slug,
         p.para_intro, p.sub_1, p.para_1, p.sub_2, p.para_2, p.quote_line, p.image_url
  FROM prepared p
  JOIN (
    SELECT id, arxiv_id FROM ins_papers
    UNION ALL
    SELECT id, arxiv_id FROM papers WHERE arxiv_id IN (
      SELECT 'seed-v2:' || code || ':' || variant FROM prepared
    )
  ) p2 ON p2.arxiv_id = 'seed-v2:' || p.code || ':' || p.variant
),
upsert_articles AS (
  INSERT INTO articles (
    paper_id, title, description, keywords, slug, status, featured_image_url, is_edited, view_count, engagement_metrics
  )
  SELECT
    pf.id,
    pf.title,
    pf.description,
    ARRAY[pf.code, pf.variant],
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
)
INSERT INTO article_blocks (article_id, block_type, content, order_index)
-- 0: Title
SELECT ua.article_id, 'title'::block_type, pf.title, 0
FROM upsert_articles ua
JOIN papers_final pf USING (slug)
UNION ALL
-- 1: Intro paragraph
SELECT ua.article_id, 'paragraph'::block_type, pf.para_intro, 1
FROM upsert_articles ua
JOIN papers_final pf USING (slug)
UNION ALL
-- 2: First subheading
SELECT ua.article_id, 'subheading'::block_type, pf.sub_1, 2
FROM upsert_articles ua
JOIN papers_final pf USING (slug)
UNION ALL
-- 3: First detail paragraph
SELECT ua.article_id, 'paragraph'::block_type, pf.para_1, 3
FROM upsert_articles ua
JOIN papers_final pf USING (slug)
UNION ALL
-- 4: Second subheading
SELECT ua.article_id, 'subheading'::block_type, pf.sub_2, 4
FROM upsert_articles ua
JOIN papers_final pf USING (slug)
UNION ALL
-- 5: Second detail paragraph
SELECT ua.article_id, 'paragraph'::block_type, pf.para_2, 5
FROM upsert_articles ua
JOIN papers_final pf USING (slug)
UNION ALL
-- 6: Quote
SELECT ua.article_id, 'quote'::block_type, pf.quote_line, 6
FROM upsert_articles ua
JOIN papers_final pf USING (slug)
UNION ALL
-- 7: Image
SELECT ua.article_id, 'image'::block_type, pf.image_url, 7
FROM upsert_articles ua
JOIN papers_final pf USING (slug)
ON CONFLICT (article_id, order_index) DO UPDATE SET
  content = EXCLUDED.content,
  updated_at = NOW();

COMMIT;

