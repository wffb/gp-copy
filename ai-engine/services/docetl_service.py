"""
DocETL Service
==============
DocETL Python API integration for paper-to-article processing pipeline.

Based on: https://ucbepic.github.io/docetl/tutorial-pythonapi/
"""

import logging
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from docetl.api import (
    Pipeline, Dataset, MapOp, PipelineStep, 
    PipelineOutput
)

logger = logging.getLogger(__name__)


@dataclass
class DocETLConfig:
    """DocETL pipeline configuration."""
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_judge_model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4000
    request_timeout: int = 600  # LiteLLM request timeout in seconds
    enable_validation: bool = True
    intermediate_dir: str = "docetl_intermediate"
    # Gleaning configuration
    enable_gleaning: bool = True
    num_rounds: int = 2
    validation_prompt: Optional[str] = None


@dataclass
class ArticleComponents:
    """Extracted article components from DocETL processing."""
    engaging_title: str
    description: str
    keywords: List[str]
    slug: str
    blocks: List[Dict[str, Any]]
    validation_results: Optional[Dict[str, Any]] = None


class DocETLService:
    """
    Service for DocETL-based paper-to-article processing.
    
    Uses DocETL Python API to create pipelines that:
    1. Extract article components (title, description, keywords)
    2. Generate structured article blocks
    3. Validate generated content (optional)
    
    Based on DocETL tutorial: https://ucbepic.github.io/docetl/tutorial-pythonapi/
    """
    
    def __init__(self, config: DocETLConfig, prompts: Dict[str, str], 
                 system_prompt: Optional[str] = None):
        self.config = config
        self.prompts = prompts
        self.system_prompt = system_prompt or self._default_system_prompt()
        self._ensure_intermediate_dir()
    
    def process_paper_to_article(self, paper_data: Dict[str, Any]) -> ArticleComponents:
        """
        Process a single paper into article components using DocETL.
        
        Args:
            paper_data: Dict with paper fields (title, abstract, extracted_text, arxiv_id)
            
        Returns:
            ArticleComponents with generated content
            
        Raises:
            Exception: If DocETL processing fails
        """
        arxiv_id = paper_data.get('arxiv_id', 'unknown')
        logger.info(f"Processing paper {arxiv_id} with DocETL")
        
        # Create unique intermediate directory for this paper to prevent caching across papers
        paper_intermediate_dir = str(Path(self.config.intermediate_dir) / arxiv_id)
        
        try:
            # Create temporary input file
            input_path = self._create_temp_input([paper_data])
            output_path = tempfile.mktemp(suffix='.json')
            
            # Build and run pipeline with unique intermediate directory
            pipeline = self._build_pipeline(input_path, output_path, paper_intermediate_dir)
            cost = pipeline.run()
            
            logger.info(f"DocETL processing completed for {arxiv_id}. Cost: ${cost:.4f}")
            
            # Parse results
            components = self._parse_output(output_path, paper_data)
            
            # Cleanup temp files
            Path(input_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)
            
            # Cleanup paper-specific intermediate directory
            import shutil
            paper_intermediate_path = Path(paper_intermediate_dir)
            if paper_intermediate_path.exists():
                shutil.rmtree(paper_intermediate_path)
                logger.info(f"Cleaned up intermediate directory for {arxiv_id}")
            
            return components
            
        except Exception as e:
            logger.error(f"DocETL processing failed for {arxiv_id}: {e}", exc_info=True)
            raise
    
    def _build_pipeline(self, input_path: str, output_path: str, intermediate_dir: str) -> Pipeline:
        """
        Build DocETL pipeline for article generation.
        
        Args:
            input_path: Path to input JSON file
            output_path: Path to output JSON file
            intermediate_dir: Unique intermediate directory for this paper
        """
        
        # Define dataset
        dataset = Dataset(
            type="file",
            path=input_path
        )
        
        # Define operations
        operations = [
            # Step 1: Extract article components
            MapOp(
                name="extract_components",
                type="map",
                prompt=self.prompts.get('extract_article_components', ''),
                output={
                    "schema": {
                        "engaging_title": "str",
                        "description": "str",
                        "keywords": "list[str]"
                    }
                },
                model=self.config.llm_model,
                timeout=self.config.request_timeout
            ),
            
            # Step 2: Generate slug
            MapOp(
                name="generate_slug",
                type="map",
                prompt=self.prompts.get('generate_slug', ''),
                output={
                    "schema": {
                        "slug": "str"
                    }
                },
                model=self.config.llm_model,
                timeout=self.config.request_timeout
            ),
            
            # Step 3: Generate article blocks
            # Note: DocETL doesn't support list[dict], so we output as JSON string
            # Gleaning enabled: Automatically retry with feedback if validation fails
            MapOp(
                name="generate_blocks",
                type="map",
                prompt=self.prompts.get('generate_article_blocks', ''),
                output={
                    "schema": {
                        "blocks_json": "str"
                    }
                },
                model=self.config.llm_model,
                timeout=self.config.request_timeout,
                # Add gleaning for automatic retries with validation feedback
                gleaning=self._get_gleaning_config() if self.config.enable_gleaning else None,
                validate=self._get_validation_rules() if self.config.enable_gleaning else None
            ),
        ]
        
        # Add validation operations if enabled
        if self.config.enable_validation:
            validation_ops = [
                MapOp(
                    name="validate_readability",
                    type="map",
                    prompt=self.prompts.get('validate_readability', ''),
                    output={
                        "schema": {
                            "readability_score": "float",
                            "strengths": "list[str]",
                            "weaknesses": "list[str]",
                            "suggestions": "str"
                        }
                    },
                    model=self.config.llm_judge_model,
                    timeout=self.config.request_timeout
                ),
                MapOp(
                    name="validate_engagement",
                    type="map",
                    prompt=self.prompts.get('validate_engagement', ''),
                    output={
                        "schema": {
                            "engagement_score": "float",
                            "hook_quality": "str",
                            "narrative_strengths": "list[str]",
                            "improvement_areas": "str"
                        }
                    },
                    model=self.config.llm_judge_model,
                    timeout=self.config.request_timeout
                ),
                MapOp(
                    name="validate_accuracy",
                    type="map",
                    prompt=self.prompts.get('validate_accuracy', ''),
                    output={
                        "schema": {
                            "accuracy_score": "float",
                            "verified_claims": "int",
                            "concerns": "str",
                            "severity": "str"
                        }
                    },
                    model=self.config.llm_judge_model,
                    timeout=self.config.request_timeout
                ),
            ]
            operations.extend(validation_ops)
        
        # Define pipeline step
        operation_names = [op.name for op in operations]
        step = PipelineStep(
            name="paper_to_article",
            input="papers",
            operations=operation_names
        )
        
        # Define output with paper-specific intermediate directory
        output = PipelineOutput(
            type="file",
            path=output_path,
            intermediate_dir=intermediate_dir
        )
        
        # Create pipeline
        pipeline = Pipeline(
            name="paper_article_generation",
            datasets={"papers": dataset},
            operations=operations,
            steps=[step],
            output=output,
            default_model=self.config.llm_model,
            system_prompt={
                "dataset_description": "research papers from arXiv",
                "persona": self.system_prompt
            }
        )
        
        return pipeline
    
    def _get_gleaning_config(self) -> Dict[str, Any]:
        """Get gleaning configuration for automatic retries with validation feedback."""
        return {
            "num_rounds": self.config.num_rounds,
            "validation_prompt": self._get_validation_prompt()
        }
    
    def _get_validation_rules(self) -> List[str]:
        """
        Get validation rules for article blocks generation.
        These rules check if the generated content meets basic requirements.
        """
        return [
            "len(json.loads(output['blocks_json'])) >= 5",  # Min 5 blocks
            "len(json.loads(output['blocks_json'])) <= 15",  # Max 15 blocks
            "sum(len(b.get('content', '').split()) for b in json.loads(output['blocks_json']) if b.get('block_type') in ['paragraph', 'quote']) >= 500",  # Min 500 words
        ]
    
    def _get_validation_prompt(self) -> str:
        """
        Get validation prompt for gleaning.
        This prompt is used by DocETL to check if the generated content is valid.
        """
        if self.config.validation_prompt:
            return self.config.validation_prompt
        
        return """
Review the generated article blocks and verify:
1. **Block Count**: Between 5-15 blocks (includes title, paragraphs, lists, quotes)
2. **Word Count**: At least 500 words in paragraph and quote blocks combined
3. **Structure**: Must include title block and multiple paragraph blocks
4. **Content Quality**: Blocks should have meaningful content, not placeholders

If validation fails, provide specific feedback on what needs to be improved:
- If too short: "Add more detailed explanations and examples"
- If too few blocks: "Break down content into more structured blocks"
- If missing required blocks: "Add missing title or paragraph blocks"

Return your assessment and specific improvement suggestions.
""".strip()
    
    def _parse_blocks_json(self, blocks_json: str) -> List[Dict[str, Any]]:
        """
        Parse blocks_json string, handling cases where LLM adds extra text.
        
        Tries multiple strategies:
        1. Direct JSON parsing
        2. Extract first JSON array found in the string
        3. Find JSON between brackets and parse
        """
        if not blocks_json or blocks_json.strip() == '':
            return []
        
        # Strategy 1: Try direct parsing
        try:
            blocks = json.loads(blocks_json)
            if isinstance(blocks, list):
                return blocks
            else:
                logger.warning(f"blocks_json is not a list, got: {type(blocks)}")
                return []
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract first JSON array by finding matching brackets
        try:
            start_idx = blocks_json.find('[')
            if start_idx == -1:
                logger.error("No JSON array found in blocks_json")
                return []
            
            # Find matching closing bracket
            bracket_count = 0
            end_idx = -1
            for i in range(start_idx, len(blocks_json)):
                if blocks_json[i] == '[':
                    bracket_count += 1
                elif blocks_json[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_idx = i + 1
                        break
            
            if end_idx == -1:
                logger.error("No matching closing bracket found in blocks_json")
                return []
            
            json_str = blocks_json[start_idx:end_idx]
            blocks = json.loads(json_str)
            
            if isinstance(blocks, list):
                logger.info(f"Successfully extracted JSON array from position {start_idx}:{end_idx}")
                return blocks
            else:
                logger.warning(f"Extracted content is not a list, got: {type(blocks)}")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extracted JSON: {e}")
            logger.error(f"blocks_json content (first 500 chars): {blocks_json[:500]}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing blocks_json: {e}")
            logger.error(f"blocks_json content (first 500 chars): {blocks_json[:500]}")
            return []
    
    def _create_temp_input(self, papers: List[Dict[str, Any]]) -> str:
        """Create temporary JSON input file for DocETL."""
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        )
        
        json.dump(papers, temp_file, indent=2)
        temp_file.close()
        
        return temp_file.name
    
    def _parse_output(self, output_path: str, original_paper: Dict[str, Any]) -> ArticleComponents:
        """Parse DocETL output into ArticleComponents."""
        with open(output_path, 'r') as f:
            results = json.load(f)

        if not results:
            raise ValueError("DocETL returned empty results")

        result = results[0]

        # Parse blocks from JSON string (DocETL doesn't support list[dict] in schema)
        blocks = []
        blocks_json = result.get('blocks_json', '[]')
        if blocks_json:
            blocks = self._parse_blocks_json(blocks_json)

        # Extract validation results if present
        validation_results = None
        if self.config.enable_validation:
            validation_results = {
                'readability_score': result.get('readability_score', 0.0),
                'engagement_score': result.get('engagement_score', 0.0),
                'accuracy_score': result.get('accuracy_score', 0.0),
                'readability_weaknesses': result.get('weaknesses', []),
                'engagement_weaknesses': result.get('improvement_areas', ''),
                'accuracy_concerns': result.get('concerns', ''),
            }

        return ArticleComponents(
            engaging_title=result.get('engaging_title', original_paper.get('title', '')),
            description=result.get('description', ''),
            keywords=result.get('keywords', []),
            slug=result.get('slug', ''),
            blocks=blocks,
            validation_results=validation_results
        )
    
    def _ensure_intermediate_dir(self):
        """Ensure intermediate directory exists."""
        Path(self.config.intermediate_dir).mkdir(parents=True, exist_ok=True)
    
    def _default_system_prompt(self) -> str:
        """Default system prompt for DocETL pipeline."""
        return (
            "You are a science communication expert transforming academic research "
            "into engaging, accessible articles for a general audience. Maintain "
            "scientific accuracy while making complex topics understandable and exciting."
        )


def create_docetl_service_from_env(env_vars: Dict[str, Any], 
                                   prompts: Dict[str, str]) -> DocETLService:
    """Create DocETLService from environment variables."""
    config = DocETLConfig(
        llm_provider=env_vars.get('llm_provider', 'openai'),
        llm_model=env_vars.get('llm_model', 'gpt-4o-mini'),
        llm_judge_model=env_vars.get('llm_judge_model', 'gpt-4o-mini'),
        temperature=float(env_vars.get('llm_temperature', 0.7)),
        max_tokens=int(env_vars.get('llm_max_tokens', 4000)),
        request_timeout=int(env_vars.get('llm_request_timeout', 600)),
        enable_validation=env_vars.get('enable_validation', True),
        intermediate_dir=env_vars.get('intermediate_dir', 'docetl_intermediate'),
        # Gleaning configuration
        enable_gleaning=env_vars.get('enable_gleaning', True),
        num_rounds=int(env_vars.get('gleaning_rounds', 2)),
        validation_prompt=env_vars.get('validation_prompt'),
    )
    
    system_prompt = prompts.get('docetl_pipeline_system')
    
    return DocETLService(config, prompts, system_prompt)

