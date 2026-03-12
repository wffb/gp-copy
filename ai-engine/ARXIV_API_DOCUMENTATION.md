# arXiv API Documentation (2025)

## Table of Contents
1. [Overview](#overview)
2. [Main arXiv API](#main-arxiv-api)
3. [Search Query Syntax](#search-query-syntax)
4. [API Parameters](#api-parameters)
5. [Response Structure](#response-structure)
6. [OAI-PMH Protocol](#oai-pmh-protocol)
7. [Bulk Data Access](#bulk-data-access)
8. [Examples](#examples)
9. [Best Practices](#best-practices)
10. [Important Considerations](#important-considerations)

---

## Overview

The arXiv API provides programmatic access to metadata and search functionalities for research papers. As of 2025, arXiv offers several methods for accessing its collection:

1. **Main API** - Real-time HTTP queries returning Atom XML
2. **OAI-PMH** - Bulk metadata harvesting protocol
3. **Amazon S3** - Full-text PDF and source file access
4. **Search API (Alpha)** - New JSON-based search interface

---

## Main arXiv API

### Base URL
```
http://export.arxiv.org/api/query
```

### Request Method
- HTTP GET or POST

### Response Format
- Atom XML format

### Use Cases
- Real-time metadata queries
- Application integration
- Specific paper searches
- Author/subject searches

---

## Search Query Syntax

### Field Prefixes

You can search specific fields using the following prefixes:

| Prefix | Field | Example |
|--------|-------|---------|
| `all:` | All fields (title, abstract, authors, etc.) | `all:quantum computing` |
| `ti:` | Title | `ti:machine learning` |
| `au:` | Author | `au:einstein` |
| `abs:` | Abstract | `abs:neural networks` |
| `cat:` | Category/Subject | `cat:cs.AI` |
| `co:` | Comment | `co:preliminary results` |
| `jr:` | Journal reference | `jr:Nature` |
| `rn:` | Report number | `rn:CERN-1234` |

### Boolean Operators

- `AND` - Both terms must be present
- `OR` - Either term can be present
- `ANDNOT` - First term must be present, second must not
- `()` - Parentheses for grouping

### Examples

```
# Simple search
all:quantum

# Author search
au:hawking

# Title and abstract
ti:machine+learning+AND+abs:neural+networks

# Category search
cat:cs.AI

# Complex query
(ti:quantum OR ti:classical) AND au:feynman AND cat:physics

# Multiple authors
au:einstein AND au:bohr

# Exclude terms
ti:physics ANDNOT abs:quantum
```

---

## API Parameters

### Complete Parameter List

| Parameter | Type | Description | Default | Example |
|-----------|------|-------------|---------|---------|
| `search_query` | string | Search terms with field prefixes | - | `all:electron` |
| `id_list` | string | Comma-separated arXiv IDs | - | `2301.00001,2301.00002` |
| `start` | integer | Starting index (0-based) | 0 | `0`, `10`, `20` |
| `max_results` | integer | Maximum results to return | 10 | `10`, `100`, `1000` |
| `sortBy` | string | Sort criteria | `relevance` | `relevance`, `lastUpdatedDate`, `submittedDate` |
| `sortOrder` | string | Sort order | `descending` | `ascending`, `descending` |

### Parameter Details

#### `search_query`
- Combines field prefixes with search terms
- Supports boolean operators
- URL-encode spaces and special characters

#### `id_list`
- Alternative to `search_query`
- Retrieves specific papers by arXiv ID
- Can retrieve up to ~1000 papers per request
- Format: `YYMM.NNNNN` or `YYMM.NNNNNvN` (with version)

#### `start` and `max_results`
- Used for pagination
- Maximum recommended: 2000 results per request
- For more results, use multiple requests with different `start` values

#### `sortBy`
- `relevance` - Most relevant first (default)
- `lastUpdatedDate` - Most recently updated
- `submittedDate` - Most recently submitted

#### `sortOrder`
- `descending` - Newest/highest first (default)
- `ascending` - Oldest/lowest first

---

## Response Structure

### Atom XML Format

The API returns results in Atom XML format compliant with Atom 1.0 specification.

### Feed-Level Elements

```xml
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  
  <title>ArXiv Query: search_query=all:electron</title>
  <id>http://arxiv.org/api/...</id>
  <updated>2025-10-03T00:00:00-04:00</updated>
  <link href="http://arxiv.org/api/query?..." rel="self" type="application/atom+xml"/>
  
  <opensearch:totalResults>1000</opensearch:totalResults>
  <opensearch:startIndex>0</opensearch:startIndex>
  <opensearch:itemsPerPage>10</opensearch:itemsPerPage>
  
  <!-- Entries follow... -->
</feed>
```

### Entry-Level Elements

Each paper is represented as an `<entry>` element:

```xml
<entry>
  <!-- Identifier -->
  <id>http://arxiv.org/abs/2301.00001v1</id>
  
  <!-- Dates -->
  <updated>2023-01-01T00:00:00Z</updated>
  <published>2023-01-01T00:00:00Z</published>
  
  <!-- Title -->
  <title>Understanding Quantum Mechanics Through Deep Learning</title>
  
  <!-- Abstract -->
  <summary>
    This paper explores the intersection of quantum mechanics and deep learning...
  </summary>
  
  <!-- Authors -->
  <author>
    <name>John Doe</name>
    <arxiv:affiliation>MIT</arxiv:affiliation>
  </author>
  <author>
    <name>Jane Smith</name>
    <arxiv:affiliation>Stanford University</arxiv:affiliation>
  </author>
  
  <!-- Optional fields -->
  <arxiv:comment>20 pages, 5 figures</arxiv:comment>
  <arxiv:journal_ref>Nature Physics 15, 123-145 (2023)</arxiv:journal_ref>
  <arxiv:doi>10.1038/s41567-023-01234-5</arxiv:doi>
  
  <!-- Categories -->
  <arxiv:primary_category term="quant-ph" scheme="http://arxiv.org/schemas/atom"/>
  <category term="quant-ph" scheme="http://arxiv.org/schemas/atom"/>
  <category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
  <category term="physics.comp-ph" scheme="http://arxiv.org/schemas/atom"/>
  
  <!-- Links -->
  <link href="http://arxiv.org/abs/2301.00001v1" rel="alternate" type="text/html"/>
  <link title="pdf" href="http://arxiv.org/pdf/2301.00001v1" rel="related" type="application/pdf"/>
  <link title="doi" href="http://dx.doi.org/10.1038/s41567-023-01234-5" rel="related"/>
</entry>
```

### Key Response Fields

| Field | Namespace | Description | Required |
|-------|-----------|-------------|----------|
| `id` | atom | Unique identifier URL | Yes |
| `title` | atom | Paper title | Yes |
| `summary` | atom | Abstract text | Yes |
| `author/name` | atom | Author name(s) | Yes |
| `published` | atom | Original submission date | Yes |
| `updated` | atom | Last update date | Yes |
| `primary_category` | arxiv | Main subject category | Yes |
| `category` | atom | All categories | Yes |
| `link` | atom | URLs (abstract, PDF) | Yes |
| `affiliation` | arxiv | Author affiliation | No |
| `comment` | arxiv | Additional comments | No |
| `journal_ref` | arxiv | Journal reference | No |
| `doi` | arxiv | Digital Object Identifier | No |

---

## OAI-PMH Protocol

### Overview
Open Archives Initiative Protocol for Metadata Harvesting - designed for bulk metadata retrieval.

### Base URL
```
http://export.arxiv.org/oai2
```

### Key Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `verb` | OAI-PMH request type | `ListRecords`, `GetRecord`, `Identify` |
| `metadataPrefix` | Metadata format | `oai_dc`, `arXiv`, `arXivRaw` |
| `set` | Filter by category | `physics:hep-th`, `cs`, `math` |
| `from` | Start date (inclusive) | `2025-01-01` |
| `until` | End date (inclusive) | `2025-12-31` |
| `resumptionToken` | Pagination token | (provided in response) |

### Common Verbs

#### `Identify`
Get repository information
```
http://export.arxiv.org/oai2?verb=Identify
```

#### `ListMetadataFormats`
List available metadata formats
```
http://export.arxiv.org/oai2?verb=ListMetadataFormats
```

#### `ListSets`
List available sets (categories)
```
http://export.arxiv.org/oai2?verb=ListSets
```

#### `ListRecords`
Retrieve multiple records
```
http://export.arxiv.org/oai2?verb=ListRecords&metadataPrefix=oai_dc&from=2025-01-01
```

#### `GetRecord`
Retrieve a single record
```
http://export.arxiv.org/oai2?verb=GetRecord&identifier=oai:arXiv.org:2301.00001&metadataPrefix=oai_dc
```

### Metadata Formats

1. **oai_dc** - Dublin Core metadata (simple, standardized)
2. **arXiv** - arXiv-specific metadata (more detailed)
3. **arXivRaw** - Raw metadata as submitted

### Update Frequency
- Updated daily with new submissions
- Preferred method for maintaining up-to-date metadata

---

## Bulk Data Access

### Amazon S3 Access

#### Overview
- Full-text PDFs and source files (LaTeX, etc.)
- Organized in `.tar` archives (~500MB each)
- Total size: ~9.2 TB (as of April 2025)
- Growth rate: ~100 GB/month
- Updated approximately monthly

#### Bucket Configuration
- Bucket name: `arxiv`
- Region: US East (N. Virginia)
- Type: **Requester Pays** (user pays data transfer costs)

#### Directory Structure

**PDFs:**
```
s3://arxiv/pdf/arXiv_pdf_[yymm]_[chunk].tar
```

**Source Files:**
```
s3://arxiv/src/arXiv_src_[yymm]_[chunk].tar
```

**Example:**
```
s3://arxiv/pdf/arXiv_pdf_1001_001.tar  # January 2010, chunk 1
s3://arxiv/pdf/arXiv_pdf_1001_002.tar  # January 2010, chunk 2
s3://arxiv/src/arXiv_src_2501_001.tar  # January 2025, chunk 1
```

#### Access Methods

**Using AWS CLI:**
```bash
# List PDF files
aws s3 ls s3://arxiv/pdf/ --request-payer requester

# Download a specific file
aws s3 cp s3://arxiv/pdf/arXiv_pdf_2501_001.tar . --request-payer requester
```

**Using s3cmd:**
```bash
# List files
s3cmd ls s3://arxiv/pdf/

# Download file
s3cmd get s3://arxiv/pdf/arXiv_pdf_2501_001.tar
```

#### Cost Considerations
- Data transfer costs apply (requester pays)
- Request costs apply
- Consider using AWS EC2 in same region to minimize costs

### Kaggle Dataset

arXiv's full dataset is also available on Kaggle:
- Machine-readable format
- Includes titles, authors, categories, abstracts, PDFs
- Useful for data analysis and machine learning

---

## Examples

### Example 1: Simple Search
```
GET http://export.arxiv.org/api/query?search_query=all:quantum&max_results=10
```

### Example 2: Author Search
```
GET http://export.arxiv.org/api/query?search_query=au:hawking&max_results=50&sortBy=submittedDate&sortOrder=descending
```

### Example 3: Category Search with Pagination
```
# First page
GET http://export.arxiv.org/api/query?search_query=cat:cs.AI&start=0&max_results=100

# Second page
GET http://export.arxiv.org/api/query?search_query=cat:cs.AI&start=100&max_results=100
```

### Example 4: Complex Query
```
GET http://export.arxiv.org/api/query?search_query=(ti:quantum+OR+ti:classical)+AND+cat:physics&max_results=20
```

### Example 5: Retrieve Specific Papers
```
GET http://export.arxiv.org/api/query?id_list=2301.00001,2301.00002,2301.00003
```

### Example 6: Recent Papers by Date
```
GET http://export.arxiv.org/api/query?search_query=cat:cs.LG&sortBy=submittedDate&sortOrder=descending&max_results=50
```

### Python Example

```python
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

def search_arxiv(query, max_results=10, start=0):
    """
    Search arXiv API and return results.
    
    Args:
        query: Search query string (e.g., "all:quantum" or "au:hawking")
        max_results: Maximum number of results to return
        start: Starting index for pagination
    
    Returns:
        List of paper dictionaries
    """
    base_url = "http://export.arxiv.org/api/query"
    
    params = {
        'search_query': query,
        'start': start,
        'max_results': max_results,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    with urllib.request.urlopen(url) as response:
        xml_data = response.read()
    
    # Parse XML
    root = ET.fromstring(xml_data)
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom'
    }
    
    papers = []
    for entry in root.findall('atom:entry', ns):
        paper = {
            'id': entry.find('atom:id', ns).text,
            'title': entry.find('atom:title', ns).text.strip(),
            'summary': entry.find('atom:summary', ns).text.strip(),
            'published': entry.find('atom:published', ns).text,
            'updated': entry.find('atom:updated', ns).text,
            'authors': [author.find('atom:name', ns).text 
                       for author in entry.findall('atom:author', ns)],
            'categories': [cat.get('term') 
                          for cat in entry.findall('atom:category', ns)],
            'pdf_url': None,
            'doi': None,
            'journal_ref': None,
            'comment': None
        }
        
        # Extract PDF link
        for link in entry.findall('atom:link', ns):
            if link.get('type') == 'application/pdf':
                paper['pdf_url'] = link.get('href')
        
        # Extract optional fields
        doi_elem = entry.find('arxiv:doi', ns)
        if doi_elem is not None:
            paper['doi'] = doi_elem.text
        
        journal_elem = entry.find('arxiv:journal_ref', ns)
        if journal_elem is not None:
            paper['journal_ref'] = journal_elem.text
        
        comment_elem = entry.find('arxiv:comment', ns)
        if comment_elem is not None:
            paper['comment'] = comment_elem.text
        
        papers.append(paper)
    
    return papers

# Usage examples
if __name__ == "__main__":
    # Search by keyword
    results = search_arxiv("all:machine learning", max_results=5)
    
    # Search by author
    results = search_arxiv("au:bengio", max_results=10)
    
    # Search by category
    results = search_arxiv("cat:cs.AI", max_results=20)
    
    # Complex query
    results = search_arxiv("ti:transformer AND cat:cs.CL", max_results=15)
    
    # Print results
    for paper in results:
        print(f"Title: {paper['title']}")
        print(f"Authors: {', '.join(paper['authors'])}")
        print(f"Published: {paper['published']}")
        print(f"PDF: {paper['pdf_url']}")
        print(f"Categories: {', '.join(paper['categories'])}")
        print("-" * 80)
```

---

## Best Practices

### Rate Limiting
1. **Wait 3 seconds between requests** - Recommended by arXiv
2. Use `time.sleep(3)` in loops
3. Consider exponential backoff for errors
4. Don't overwhelm the server

### Pagination
```python
import time

def get_all_results(query, total_needed=500):
    """Get results with pagination."""
    all_papers = []
    start = 0
    batch_size = 100  # Get 100 at a time
    
    while len(all_papers) < total_needed:
        papers = search_arxiv(query, max_results=batch_size, start=start)
        if not papers:
            break
        all_papers.extend(papers)
        start += batch_size
        time.sleep(3)  # Rate limiting
    
    return all_papers[:total_needed]
```

### Error Handling
```python
import time
from urllib.error import HTTPError, URLError

def safe_arxiv_request(query, max_results=10, max_retries=3):
    """Make request with error handling and retries."""
    for attempt in range(max_retries):
        try:
            return search_arxiv(query, max_results)
        except HTTPError as e:
            if e.code == 503:  # Service unavailable
                wait_time = (2 ** attempt) * 3  # Exponential backoff
                print(f"Server busy, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
        except URLError as e:
            print(f"Network error: {e}")
            time.sleep(3)
    
    raise Exception("Max retries exceeded")
```

### Efficient Querying
1. **Use specific field searches** - More efficient than `all:`
2. **Use categories** - Pre-filters results
3. **Batch requests** - Use `id_list` for multiple papers
4. **Cache results** - Don't re-query same data
5. **Use OAI-PMH for bulk** - Better for large-scale harvesting

### Respect Terms of Service
1. Use dedicated server: `export.arxiv.org`
2. Identify your application in User-Agent
3. Link back to arXiv when using full-text
4. Acknowledge arXiv in publications
5. Don't create mirrors without permission

---

## Important Considerations

### Terms of Use
- Review arXiv's API Terms of Use: https://info.arxiv.org/help/api/tou.html
- Use the dedicated API server: `export.arxiv.org`
- Don't use the main website for programmatic access
- Identify your client appropriately

### Licensing
- Most articles use the default arXiv license
- arXiv has a non-exclusive license to distribute
- Copyright remains with authors
- Must link back to arXiv for downloads
- Cannot create competing archives

### Attribution
When using arXiv data, include:
```
"Thank you to arXiv for use of its open access interoperability."
```

### Update Frequency
| Method | Update Frequency | Best For |
|--------|------------------|----------|
| Main API | Real-time | Current searches, small-scale |
| OAI-PMH | Daily | Metadata harvesting, staying updated |
| Amazon S3 | Monthly | Bulk full-text, large datasets |

### Data Quality Notes
1. **Metadata quality varies** - Submitted by authors
2. **Categories may overlap** - Papers can have multiple
3. **Versions exist** - Papers can be updated (v1, v2, etc.)
4. **Withdrawals** - Papers can be withdrawn
5. **Not peer-reviewed** - Preprint server

### Categories Overview

Common categories include:
- `cs.*` - Computer Science (cs.AI, cs.LG, cs.CV, etc.)
- `math.*` - Mathematics
- `physics.*` - Physics
- `stat.*` - Statistics
- `q-bio.*` - Quantitative Biology
- `q-fin.*` - Quantitative Finance
- `econ.*` - Economics

Full list: https://arxiv.org/category_taxonomy

### API Limits
- No hard rate limit, but be respectful (3 seconds recommended)
- Maximum ~2000 results per request recommended
- Use pagination for more results
- OAI-PMH uses resumption tokens for large result sets

### Troubleshooting

#### Issue: Empty Results
- Check query syntax
- Verify category codes are correct
- Try simpler queries first
- Check date ranges

#### Issue: 503 Errors
- Server is busy
- Wait and retry
- Use exponential backoff
- Consider using OAI-PMH instead

#### Issue: Malformed XML
- Ensure proper URL encoding
- Check for special characters
- Validate parameter values

---

## Additional Resources

- **API Basics**: https://info.arxiv.org/help/api/basics.html
- **User Manual**: https://info.arxiv.org/help/api/user-manual.html
- **Bulk Data**: https://info.arxiv.org/help/bulk_data.html
- **S3 Access**: https://info.arxiv.org/help/bulk_data_s3.html
- **Terms of Use**: https://info.arxiv.org/help/api/tou.html
- **Category Taxonomy**: https://arxiv.org/category_taxonomy

---

## Summary

The arXiv API provides multiple access methods for different use cases:

1. **Real-time API** - For searches and small-scale data retrieval
2. **OAI-PMH** - For bulk metadata and daily updates
3. **Amazon S3** - For full-text PDFs and source files

Choose the method that best fits your needs based on:
- Volume of data needed
- Update frequency required
- Whether you need full-text or just metadata
- Budget (S3 has costs)

Always respect rate limits, follow terms of service, and acknowledge arXiv appropriately.

