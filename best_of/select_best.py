import os
import openai
import xml.etree.ElementTree as ET
from datetime import datetime
from lxml import etree

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

# Input: The filtered feed from the main script
INPUT_FEED = "../output/filtered_feed.xml"

# Output: The best-of feed
OUTPUT_FEED = "best_of_feed.xml"

# Load selection criteria from file
def load_selection_criteria():
    """Load selection criteria from best_of_instructions.txt"""
    instructions_file = 'best_of_instructions.txt'
    try:
        with open(instructions_file, 'r', encoding='utf-8') as f:
            criteria = f.read().strip()
        print(f"✓ Loaded selection criteria from {instructions_file}")
        return criteria
    except FileNotFoundError:
        print(f"❌ ERROR: {instructions_file} not found!")
        print(f"Please create {instructions_file} in the best_of directory.")
        raise
    except Exception as e:
        print(f"❌ ERROR reading {instructions_file}: {e}")
        raise

SELECTION_CRITERIA = load_selection_criteria()

openai.api_key = os.environ.get("OPENAI_API_KEY")

# --------------------------------------------------
# PARSE FILTERED FEED
# --------------------------------------------------
def parse_filtered_feed(feed_path: str) -> list:
    """
    Parse the filtered RSS feed and extract paper information.
    Returns list of paper dictionaries.
    """
    print(f"\nReading filtered feed from: {feed_path}")
    
    try:
        tree = ET.parse(feed_path)
        root = tree.getroot()
        
        papers = []
        
        # Find all items in the RSS feed
        for item in root.findall('.//item'):
            paper = {}
            
            # Extract basic fields
            paper['title'] = item.find('title').text if item.find('title') is not None else ''
            paper['link'] = item.find('link').text if item.find('link') is not None else ''
            paper['pubDate'] = item.find('pubDate').text if item.find('pubDate') is not None else ''
            
            # Extract description (contains abstract and metadata)
            description = item.find('description').text if item.find('description') is not None else ''
            paper['description'] = description
            
            # Extract author from dc:creator if present
            creator = item.find('{http://purl.org/dc/elements/1.1/}creator')
            paper['authors'] = creator.text if creator is not None else 'Unknown'
            
            # Parse description to extract journal and abstract
            # The description contains HTML with structured metadata
            if '<b>Journal:</b>' in description:
                journal_start = description.find('<b>Journal:</b>') + len('<b>Journal:</b>')
                journal_end = description.find('<br/>', journal_start)
                paper['journal'] = description[journal_start:journal_end].strip()
            else:
                paper['journal'] = 'Unknown'
            
            if '<b>Abstract:</b>' in description:
                abstract_start = description.find('<b>Abstract:</b>') + len('<b>Abstract:</b><br/>')
                paper['abstract'] = description[abstract_start:].strip()
            else:
                paper['abstract'] = ''
            
            papers.append(paper)
        
        print(f"✓ Found {len(papers)} papers in filtered feed")
        return papers
        
    except FileNotFoundError:
        print(f"❌ ERROR: Filtered feed not found at {feed_path}")
        print("Make sure the main filter script has run first!")
        raise
    except Exception as e:
        print(f"❌ ERROR parsing feed: {e}")
        raise

# --------------------------------------------------
# OPENAI SELECTION
# --------------------------------------------------
def score_paper(paper: dict) -> dict:
    """
    Use OpenAI to score a paper's importance/impact.
    Returns the paper dict with added 'score' and 'reasoning' fields.
    """
    
    # Create a concise summary for scoring
    paper_summary = f"""
Title: {paper['title']}

Authors: {paper['authors']}

Journal: {paper['journal']}

Abstract: {paper['abstract'][:800]}...
"""

    prompt = f"""{SELECTION_CRITERIA}

Paper to evaluate:
{paper_summary}

Return your response as a JSON object with:
- "score": A number from 0-100 (where 100 is highest impact/importance)
- "reasoning": A 1-2 sentence explanation of your score

Example format:
{{"score": 85, "reasoning": "Large randomized trial in NEJM showing significant survival benefit with novel therapy. Clear practice-changing implications."}}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3  # Slight variation for nuanced scoring
        )
        
        result_text = response.choices[0].message["content"].strip()
        
        # Parse JSON response
        import json
        # Remove markdown code blocks if present
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]
        
        result = json.loads(result_text.strip())
        
        paper['score'] = result.get('score', 0)
        paper['reasoning'] = result.get('reasoning', 'No reasoning provided')
        
        return paper
        
    except Exception as e:
        print(f"⚠ Error scoring paper: {e}")
        paper['score'] = 0
        paper['reasoning'] = f"Error during scoring: {str(e)}"
        return paper

def select_best_papers(papers: list, top_n: int = 10) -> list:
    """
    Score all papers and return the top N.
    """
    print(f"\n{'='*60}")
    print("Scoring papers with OpenAI...")
    print(f"{'='*60}")
    
    scored_papers = []
    
    for i, paper in enumerate(papers, 1):
        print(f"\n[{i}/{len(papers)}] Scoring: {paper['title'][:60]}...")
        
        scored_paper = score_paper(paper)
        scored_papers.append(scored_paper)
        
        print(f"  Score: {scored_paper['score']}/100")
        print(f"  Reasoning: {scored_paper['reasoning']}")
        
        # Small delay to avoid rate limiting
        import time
        time.sleep(0.5)
    
    # Sort by score (highest first)
    scored_papers.sort(key=lambda x: x['score'], reverse=True)
    
    # Return top N
    best_papers = scored_papers[:top_n]
    
    print(f"\n{'='*60}")
    print(f"Selected top {len(best_papers)} papers")
    print(f"{'='*60}")
    
    return best_papers

# --------------------------------------------------
# RSS GENERATION
# --------------------------------------------------
def create_best_of_feed(papers: list, output_path: str):
    """
    Create RSS feed with the best papers, including scores and reasoning.
    """
    print(f"\nCreating Best Of feed...")
    
    # Create RSS structure
    rss = etree.Element("rss", 
                        version="2.0",
                        nsmap={
                            'dc': 'http://purl.org/dc/elements/1.1/',
                            'atom': 'http://www.w3.org/2005/Atom'
                        })
    channel = etree.SubElement(rss, "channel")
    
    etree.SubElement(channel, "title").text = "Best Of Week - Head & Neck Cancer"
    etree.SubElement(channel, "link").text = "https://pubmed.ncbi.nlm.nih.gov"
    etree.SubElement(channel, "description").text = f"Top {len(papers)} most impactful head and neck cancer papers this week, selected by AI"
    etree.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
    
    # Add each paper
    for rank, paper in enumerate(papers, 1):
        item = etree.SubElement(channel, "item")
        
        # Add rank to title
        ranked_title = f"#{rank} [{paper['score']}/100] {paper['title']}"
        etree.SubElement(item, "title").text = ranked_title
        
        # Link
        etree.SubElement(item, "link").text = paper['link']
        etree.SubElement(item, "guid").text = paper['link']
        
        # Author
        dc_creator = etree.SubElement(item, "{http://purl.org/dc/elements/1.1/}creator")
        dc_creator.text = paper['authors']
        
        # Publication date
        etree.SubElement(item, "pubDate").text = paper['pubDate']
        
        # Enhanced description with AI reasoning
        description_parts = []
        
        # Importance badge
        if paper['score'] >= 90:
            badge = "🔥 CRITICAL"
        elif paper['score'] >= 80:
            badge = "⭐ HIGH IMPACT"
        elif paper['score'] >= 70:
            badge = "✨ NOTABLE"
        else:
            badge = "📌 SELECTED"
        
        description_parts.append(f"<h3>{badge} - Score: {paper['score']}/100</h3>")
        
        # AI reasoning
        description_parts.append(f"<p><b>Why this matters:</b> {paper['reasoning']}</p>")
        
        # Separator
        description_parts.append("<hr/>")
        
        # Original metadata from filtered feed
        description_parts.append(paper['description'])
        
        description = "".join(description_parts)
        etree.SubElement(item, "description").text = description
    
    # Write to file
    tree = etree.ElementTree(rss)
    tree.write(output_path,
               pretty_print=True,
               xml_declaration=True,
               encoding="UTF-8")
    
    print(f"✓ Created Best Of feed: {output_path}")

# --------------------------------------------------
# MAIN
# --------------------------------------------------
def main():
    print("\n" + "="*60)
    print("BEST OF WEEK - Head & Neck Cancer")
    print("Selecting top papers using AI evaluation")
    print("="*60)
    
    # Step 1: Parse filtered feed
    papers = parse_filtered_feed(INPUT_FEED)
    
    if not papers:
        print("\n⚠ No papers in filtered feed. Nothing to select from.")
        return
    
    # Step 2: Select best papers
    best_papers = select_best_papers(papers, top_n=10)
    
    # Step 3: Create output feed
    create_best_of_feed(best_papers, OUTPUT_FEED)
    
    # Summary
    print("\n" + "="*60)
    print("✓ COMPLETED - BEST OF WEEK")
    print("="*60)
    print(f"Selected: {len(best_papers)} papers")
    print(f"Output: {OUTPUT_FEED}")
    print("\nTop 3 papers:")
    for i, paper in enumerate(best_papers[:3], 1):
        print(f"\n{i}. [{paper['score']}/100] {paper['title'][:70]}...")
        print(f"   {paper['reasoning']}")
    print()

if __name__ == "__main__":
    main()
