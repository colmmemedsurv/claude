import os
import openai
import requests
from lxml import etree
from datetime import datetime, timedelta
import time
import xml.etree.ElementTree as ET

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
# Read PubMed search query from file
def load_search_query():
    """Load PubMed search query from pubmedsearchterm.txt"""
    search_file = 'pubmedsearchterm.txt'
    try:
        with open(search_file, 'r', encoding='utf-8') as f:
            query = f.read().strip()
        print(f"✓ Loaded search query from {search_file}")
        return query
    except FileNotFoundError:
        print(f"❌ ERROR: {search_file} not found!")
        print(f"Please create {search_file} in the root directory with your PubMed search query.")
        raise
    except Exception as e:
        print(f"❌ ERROR reading {search_file}: {e}")
        raise

# Read OpenAI classification instructions from file
def load_openai_instructions():
    """Load OpenAI classification instructions from openaiinstructions.txt"""
    instructions_file = 'openaiinstructions.txt'
    try:
        with open(instructions_file, 'r', encoding='utf-8') as f:
            instructions = f.read().strip()
        print(f"✓ Loaded OpenAI instructions from {instructions_file}")
        return instructions
    except FileNotFoundError:
        print(f"❌ ERROR: {instructions_file} not found!")
        print(f"Please create {instructions_file} in the root directory with your classification instructions.")
        raise
    except Exception as e:
        print(f"❌ ERROR reading {instructions_file}: {e}")
        raise

# Load configuration from files
PUBMED_SEARCH_QUERY = load_search_query()
OPENAI_INSTRUCTIONS = load_openai_instructions()

MAX_RESULTS = 100
DAYS_BACK = 7  # Filter to last 7 days

OUTPUT_ACCEPTED = "output/filtered_feed.xml"
OUTPUT_REJECTED = "output/rejected_feed.xml"

openai.api_key = os.environ.get("OPENAI_API_KEY")

# PubMed E-utilities API endpoints
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Email for NCBI API usage (required)
YOUR_EMAIL = "colmme.medsurv@gmail.com"

# --------------------------------------------------
# FETCH FROM PUBMED E-UTILITIES API
# --------------------------------------------------
def search_pubmed(query: str, max_results: int = 100, days_back: int = 7) -> list:
    """
    Search PubMed using the official E-utilities API.
    Returns a list of PubMed IDs (PMIDs).
    Automatically filters to last N days using datetype=crdt (creation date).
    """
    # Calculate date range (last N days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Format dates as YYYY/MM/DD for PubMed
    mindate = start_date.strftime("%Y/%m/%d")
    maxdate = end_date.strftime("%Y/%m/%d")
    
    print(f"Searching PubMed for papers from {mindate} to {maxdate}")
    print(f"Query: {query[:100]}..." if len(query) > 100 else f"Query: {query}")
    print(f"Maximum results: {max_results}")
    
    params = {
        'db': 'pubmed',
        'term': query,
        'retmax': max_results,
        'retmode': 'json',
        'sort': 'pub_date',  # Most recent first
        'datetype': 'crdt',  # Creation date (when added to PubMed)
        'mindate': mindate,
        'maxdate': maxdate,
        'email': YOUR_EMAIL,
        'tool': 'pubmed_hnc_filter',
    }
    
    try:
        # Use POST instead of GET to avoid URL length limits with complex queries
        response = requests.post(ESEARCH_URL, data=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        pmids = data['esearchresult']['idlist']
        
        print(f"✓ Found {len(pmids)} papers from the last {days_back} days")
        
        if len(pmids) == 0:
            print(f"⚠ No papers found. This could mean:")
            print(f"  - No new papers matching your criteria in the last {days_back} days")
            print(f"  - Try increasing DAYS_BACK or checking your search query")
        
        return pmids
        
    except Exception as e:
        print(f"✗ Error searching PubMed: {e}")
        raise

def fetch_paper_details(pmids: list) -> list:
    """
    Fetch full details for a list of PMIDs using E-utilities.
    Returns list of paper dictionaries.
    """
    if not pmids:
        return []
    
    print(f"\nFetching details for {len(pmids)} papers...")
    
    # E-utilities allows fetching multiple papers at once (max 200 at a time)
    pmid_str = ','.join(pmids)
    
    params = {
        'db': 'pubmed',
        'id': pmid_str,
        'retmode': 'xml',
        'email': YOUR_EMAIL,
        'tool': 'pubmed_hnc_filter',
    }
    
    try:
        response = requests.get(EFETCH_URL, params=params, timeout=60)
        response.raise_for_status()
        
        # Parse XML response
        root = ET.fromstring(response.content)
        
        papers = []
        articles = root.findall('.//PubmedArticle')
        
        for article in articles:
            try:
                # Extract PMID
                pmid = article.find('.//PMID')
                pmid_text = pmid.text if pmid is not None else 'Unknown'
                
                # Extract title
                title_elem = article.find('.//ArticleTitle')
                title = ''.join(title_elem.itertext()) if title_elem is not None else 'No title'
                
                # Extract abstract
                abstract_elem = article.find('.//Abstract')
                abstract = ''
                if abstract_elem is not None:
                    abstract_texts = []
                    for abstract_text in abstract_elem.findall('.//AbstractText'):
                        label = abstract_text.get('Label', '')
                        text = ''.join(abstract_text.itertext())
                        if label:
                            abstract_texts.append(f"{label}: {text}")
                        else:
                            abstract_texts.append(text)
                    abstract = ' '.join(abstract_texts)
                
                # Extract authors
                authors = []
                author_list = article.find('.//AuthorList')
                if author_list is not None:
                    for author in author_list.findall('.//Author')[:10]:  # Limit to first 10 authors
                        last_name = author.find('LastName')
                        initials = author.find('Initials')
                        fore_name = author.find('ForeName')
                        
                        if last_name is not None:
                            if initials is not None:
                                authors.append(f"{last_name.text} {initials.text}")
                            elif fore_name is not None:
                                authors.append(f"{last_name.text} {fore_name.text}")
                            else:
                                authors.append(last_name.text)
                
                author_string = ', '.join(authors) if authors else 'No authors listed'
                if len(author_list.findall('.//Author')) > 10:
                    author_string += ', et al.'
                
                # Extract publication date
                pub_date = article.find('.//PubDate')
                date_str = ''
                rfc822_date = ''
                
                if pub_date is not None:
                    year = pub_date.find('Year')
                    month = pub_date.find('Month')
                    day = pub_date.find('Day')
                    
                    year_text = year.text if year is not None else ''
                    month_text = month.text if month is not None else '01'
                    day_text = day.text if day is not None else '01'
                    
                    # Human-readable date
                    date_str = f"{year_text}-{month_text}-{day_text}".strip('-')
                    
                    # Convert to RFC 822 format for RSS (required for proper date display)
                    try:
                        # Convert month name to number if needed
                        month_map = {
                            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12',
                            'January': '01', 'February': '02', 'March': '03', 'April': '04',
                            'June': '06', 'July': '07', 'August': '08', 'September': '09',
                            'October': '10', 'November': '11', 'December': '12'
                        }
                        
                        month_num = month_map.get(month_text, month_text)
                        
                        if year_text and month_num and day_text:
                            # Create proper date object
                            from datetime import datetime as dt
                            date_obj = dt.strptime(f"{year_text}-{month_num}-{day_text}", "%Y-%m-%d")
                            rfc822_date = date_obj.strftime("%a, %d %b %Y 12:00:00 +0000")
                        else:
                            # Fallback to just year if incomplete
                            rfc822_date = f"01 Jan {year_text} 12:00:00 +0000"
                    except:
                        rfc822_date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
                
                # Extract journal
                journal_elem = article.find('.//Journal/Title')
                journal = journal_elem.text if journal_elem is not None else 'Unknown Journal'
                
                # Extract DOI
                doi = ''
                article_id_list = article.findall('.//ArticleId')
                for article_id in article_id_list:
                    if article_id.get('IdType') == 'doi':
                        doi = article_id.text
                        break
                
                # Construct PubMed URL
                pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid_text}/"
                
                papers.append({
                    'pmid': pmid_text,
                    'title': title,
                    'abstract': abstract,
                    'journal': journal,
                    'authors': author_string,
                    'date': date_str,
                    'rfc822_date': rfc822_date,
                    'doi': doi,
                    'url': pubmed_url,
                })
                
            except Exception as e:
                print(f"⚠ Warning: Could not parse article: {e}")
                continue
        
        print(f"✓ Successfully parsed {len(papers)} papers")
        return papers
        
    except Exception as e:
        print(f"✗ Error fetching paper details: {e}")
        raise

# --------------------------------------------------
# OPENAI CLASSIFICATION
# --------------------------------------------------
def is_relevant_paper(paper: dict) -> bool:
    """
    Use OpenAI to classify if a paper matches the criteria.
    Uses instructions from openaiinstructions.txt
    """
    text = f"Title: {paper['title']}\n\nAbstract: {paper['abstract']}"
    
    prompt = f"""{OPENAI_INSTRUCTIONS}

Paper:
{text}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        answer = response.choices[0].message["content"].strip().upper()
        return answer == "YES"
        
    except Exception as e:
        print(f"⚠ OpenAI API error: {e}")
        return True  # Default to accepting

# --------------------------------------------------
# RSS GENERATION
# --------------------------------------------------
def create_channel(title: str, link: str, description: str):
    """Create an RSS channel structure with Dublin Core namespace for authors."""
    # Create RSS element with Dublin Core namespace for author metadata
    rss = etree.Element("rss", 
                        version="2.0",
                        nsmap={
                            'dc': 'http://purl.org/dc/elements/1.1/',
                            'atom': 'http://www.w3.org/2005/Atom'
                        })
    channel = etree.SubElement(rss, "channel")

    etree.SubElement(channel, "title").text = title
    etree.SubElement(channel, "link").text = "https://pubmed.ncbi.nlm.nih.gov"
    etree.SubElement(channel, "description").text = description
    etree.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    return rss, channel

def add_paper_to_channel(channel, paper: dict):
    """Add a paper to an RSS channel with proper metadata."""
    item = etree.SubElement(channel, "item")
    
    # Title
    etree.SubElement(item, "title").text = paper['title']
    
    # Link (PubMed URL)
    etree.SubElement(item, "link").text = paper['url']
    
    # GUID (unique identifier)
    etree.SubElement(item, "guid").text = paper['url']
    
    # Author (DC:Creator for RSS readers)
    # Many RSS readers recognize dc:creator for author display
    dc_creator = etree.SubElement(item, "{http://purl.org/dc/elements/1.1/}creator")
    dc_creator.text = paper['authors']
    
    # Publication date (RFC 822 format - critical for proper date display)
    etree.SubElement(item, "pubDate").text = paper['rfc822_date']
    
    # Create rich description with all metadata
    description_parts = []
    
    # Authors
    description_parts.append(f"<b>Authors:</b> {paper['authors']}")
    
    # Journal with DOI if available
    journal_line = f"<b>Journal:</b> {paper['journal']}"
    if paper['doi']:
        journal_line += f" | <b>DOI:</b> <a href='https://doi.org/{paper['doi']}'>{paper['doi']}</a>"
    description_parts.append(journal_line)
    
    # Publication date (human readable)
    description_parts.append(f"<b>Published:</b> {paper['date']}")
    
    # PubMed ID
    description_parts.append(f"<b>PMID:</b> <a href='{paper['url']}'>{paper['pmid']}</a>")
    
    # Abstract
    description_parts.append("<br/><br/>")
    if paper['abstract']:
        description_parts.append(f"<b>Abstract:</b><br/>{paper['abstract']}")
    else:
        description_parts.append("<i>No abstract available</i>")
    
    description = "<br/>".join(description_parts)
    etree.SubElement(item, "description").text = description

# --------------------------------------------------
# MAIN
# --------------------------------------------------
def main():
    print("\n" + "=" * 60)
    print("PubMed Filter - Head and Neck Cancer")
    print("Using PubMed E-utilities API")
    print(f"Filtering to last {DAYS_BACK} days")
    print("=" * 60)
    
    # Step 1: Search PubMed with date filtering
    try:
        pmids = search_pubmed(PUBMED_SEARCH_QUERY, MAX_RESULTS, DAYS_BACK)
    except Exception as e:
        print(f"\n❌ Failed to search PubMed: {e}")
        raise
    
    if not pmids:
        print(f"\n⚠ No papers found in the last {DAYS_BACK} days matching your criteria")
        print("\nThis is normal if:")
        print(f"  - Your journals haven't published relevant papers recently")
        print(f"  - The search criteria are very specific")
        print(f"\nConsider:")
        print(f"  - Increasing DAYS_BACK in the configuration")
        print(f"  - Checking if the search query is correct")
        
        # Create empty output files
        os.makedirs("output", exist_ok=True)
        
        accepted_rss, accepted_channel = create_channel(
            "Filtered PubMed – Head and Neck Cancer",
            "https://pubmed.ncbi.nlm.nih.gov",
            f"Papers classified as related to head and neck cancer (last {DAYS_BACK} days)"
        )
        
        etree.ElementTree(accepted_rss).write(
            OUTPUT_ACCEPTED,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8"
        )
        
        rejected_rss, rejected_channel = create_channel(
            "Rejected PubMed Papers – Not Head and Neck Cancer",
            "https://pubmed.ncbi.nlm.nih.gov",
            f"Papers rejected by the automated classifier (last {DAYS_BACK} days)"
        )
        
        etree.ElementTree(rejected_rss).write(
            OUTPUT_REJECTED,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8"
        )
        
        print(f"\n✓ Created empty output files")
        return
    
    # Step 2: Fetch paper details
    try:
        papers = fetch_paper_details(pmids)
    except Exception as e:
        print(f"\n❌ Failed to fetch paper details: {e}")
        raise
    
    if not papers:
        print("\n⚠ Could not retrieve any paper details")
        return
    
    # Step 3: Create RSS structures
    accepted_rss, accepted_channel = create_channel(
        "Filtered PubMed – Head and Neck Cancer",
        "https://pubmed.ncbi.nlm.nih.gov",
        f"Papers classified as related to head and neck cancer (last {DAYS_BACK} days)"
    )

    rejected_rss, rejected_channel = create_channel(
        "Rejected PubMed Papers – Not Head and Neck Cancer",
        "https://pubmed.ncbi.nlm.nih.gov",
        f"Papers rejected by the automated classifier (last {DAYS_BACK} days)"
    )

    # Step 4: Classify and filter papers
    print("\n" + "=" * 60)
    print("Classifying papers with OpenAI...")
    print("=" * 60)
    
    accepted_count = 0
    rejected_count = 0
    
    for i, paper in enumerate(papers, 1):
        print(f"\n[{i}/{len(papers)}] {paper['title'][:70]}...")
        
        try:
            if is_relevant_paper(paper):
                add_paper_to_channel(accepted_channel, paper)
                accepted_count += 1
                print("  → ✓ ACCEPTED")
            else:
                add_paper_to_channel(rejected_channel, paper)
                rejected_count += 1
                print("  → ✗ REJECTED")
            
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  → ⚠ ERROR: {e}")
            add_paper_to_channel(rejected_channel, paper)
            rejected_count += 1
    
    # Step 5: Write output files
    os.makedirs("output", exist_ok=True)
    
    etree.ElementTree(accepted_rss).write(
        OUTPUT_ACCEPTED,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8"
    )
    
    etree.ElementTree(rejected_rss).write(
        OUTPUT_REJECTED,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8"
    )
    
    # Summary
    print("\n" + "=" * 60)
    print("✓ COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print(f"Accepted papers:  {accepted_count}")
    print(f"Rejected papers:  {rejected_count}")
    print(f"Total processed:  {len(papers)}")
    print("=" * 60)
    print(f"\n📁 Output files:")
    print(f"   • {OUTPUT_ACCEPTED}")
    print(f"   • {OUTPUT_REJECTED}")
    print()

if __name__ == "__main__":
    main()
