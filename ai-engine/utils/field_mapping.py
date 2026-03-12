"""Field Mapper Service - Maps arXiv categories to database field IDs."""

import logging
import re
from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from database.repositories.field import FieldRepository

logger = logging.getLogger(__name__)

# Valid arXiv category pattern: letters, optional dot, letters/numbers, optional dash
ARXIV_CATEGORY_PATTERN = re.compile(r'^[a-z]+(-[a-z]+)?(\.[a-z]+(-[a-z]+)?)?$', re.IGNORECASE)

PHYSICS_SUBFIELDS = {
    # Archives under Physics (no dot prefix)
    'astro-ph', 'cond-mat', 'gr-qc', 'hep-ex', 'hep-lat',
    'hep-ph', 'hep-th', 'math-ph', 'nlin', 'nucl-ex',
    'nucl-th', 'quant-ph',
    
    # Categories under physics archive (physics. prefix)
    'physics.acc-ph', 'physics.ao-ph', 'physics.app-ph', 'physics.atm-clus',
    'physics.atom-ph', 'physics.bio-ph', 'physics.chem-ph', 'physics.class-ph',
    'physics.comp-ph', 'physics.data-an', 'physics.ed-ph', 'physics.flu-dyn',
    'physics.gen-ph', 'physics.geo-ph', 'physics.hist-ph', 'physics.ins-det',
    'physics.med-ph', 'physics.optics', 'physics.plasm-ph', 'physics.pop-ph',
    'physics.soc-ph', 'physics.space-ph'
}


def _parse_category_to_codes(category_code: str) -> Tuple[str, str]:
    """
    Parse arXiv category into (field_code, subfield_code).
    
    Examples:
        cs.AI → (cs, cs.AI)
        astro-ph → (physics, astro-ph)
        astro-ph.CO → (physics, astro-ph)
        physics.optics → (physics, physics.optics)
    """
    category_code = category_code.strip()
    
    # Check exact match in physics subfields first
    if category_code in PHYSICS_SUBFIELDS:
        return ('physics', category_code)
    
    # Check if it's a third-level physics category (e.g., astro-ph.CO → astro-ph)
    if '.' in category_code:
        base_category = category_code.split('.', 1)[0]
        
        # If base is a physics archive (astro-ph, cond-mat, etc.)
        if base_category in PHYSICS_SUBFIELDS:
            return ('physics', base_category)
        
        # Check if the category with first dot is a physics category (e.g., physics.optics)
        first_two_parts = '.'.join(category_code.split('.')[:2])
        if first_two_parts in PHYSICS_SUBFIELDS:
            return ('physics', first_two_parts)
        
        # Standard dotted category (cs.AI, eess.AS, etc.)
        return (base_category, category_code)
    
    # No dot, not in physics
    logger.warning(f"Unexpected category format: {category_code}")
    return (category_code, category_code)


def _is_valid_arxiv_category(category_code: str) -> bool:
    """
    Check if category matches arXiv format.
    
    Valid: cs.AI, astro-ph, cond-mat.str-el, physics.optics
    Invalid: 68T07 (MSC), I.2 (ACM), 68T07, 65L06, 65G50 (multiple MSC)
    """
    category_code = category_code.strip()
    
    # Filter out obvious non-arXiv formats
    if ',' in category_code or ';' in category_code:
        return False  # Multiple codes in one string
    
    if category_code[0].isdigit():
        return False  # MSC codes start with numbers
    
    if len(category_code) <= 3 and category_code[0].isupper():
        return False  # ACM codes like "I.2", "G.1"
    
    # Match arXiv pattern
    return bool(ARXIV_CATEGORY_PATTERN.match(category_code))


def get_field_and_subfield_ids(
    category_code: str,
    session: Session
) -> Optional[Tuple[UUID, UUID]]:
    """
    Map arXiv category to (field_id, subfield_id).
    Returns None if not found or invalid format.
    
    Silently skips non-arXiv classification codes (MSC, ACM, etc.)
    """
    if not _is_valid_arxiv_category(category_code):
        logger.warning(f"Skipping non-arXiv classification code: {category_code}")
        return None
    
    field_code, subfield_code = _parse_category_to_codes(category_code)
    field_repo = FieldRepository(session)
    
    field = field_repo.find_by_code(field_code, parent_id=None)
    if not field:
        logger.warning(f"Field not found: {field_code} (from {category_code})")
        return None
    
    subfield = field_repo.find_by_code(subfield_code, parent_id=field.id)
    if not subfield:
        logger.warning(f"Subfield not found: {subfield_code} under {field_code}")
        return None
    
    return (field.id, subfield.id)