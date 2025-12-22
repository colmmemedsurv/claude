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
# Your complex PubMed search query
# Note: The original "last 7 days"[crdt] is automatically handled below
PUBMED_SEARCH_QUERY = """(("Lancet Oncol"[ta] OR "Nat Rev Clin Oncol"[ta] OR "Nat Cancer"[ta] OR "Cancer Discov"[ta] OR "Cancer Cell"[ta] OR "JAMA Oncol"[ta] OR "Ann Oncol"[ta] OR "ESMO Open"[ta] OR "Clin Cancer Res"[ta] OR "Cancer"[ta] OR "Oncologist"[ta] OR "Br J Cancer"[ta] OR "Cancer Res"[ta] OR "Int J Cancer"[ta] OR "Cancer Treat Rev"[ta] OR "J Geriatr Oncol"[ta] OR "JCO Oncol Pract"[ta] OR "JCO Oncol Adv"[ta] OR "JCO Precis Oncol"[ta] OR "Int J Radiat Oncol Biol Phys"[ta] OR "Radiother Oncol"[ta] OR "JAMA Otolaryngol Head Neck Surg"[ta] OR "Ann Otol Rhinol Laryngol"[ta] OR "Head Neck"[ta] OR "Oral Oncol"[ta] OR "Oral Dis"[ta] OR "J Oral Maxillofac Surg"[ta] OR "Laryngoscope"[ta] OR "Am J Otolaryngol"[ta] OR "Thyroid"[ta] OR "Lancet Diabetes Endocrinol"[ta] OR "N Engl J Med"[ta] OR "Lancet"[ta] OR "JAMA"[ta] OR "BMJ"[ta] OR "Nat Med"[ta] OR "PLoS Med"[ta] OR "Lancet Healthy Longev"[ta] OR "Nat Commun"[ta] OR "Oncogene"[ta] OR "J Clin Oncol"[ta] OR "J Natl Cancer Inst"[ta] OR "Otolaryngol Head Neck Surg"[ta] OR "ESMO Rare Cancers"[ta]) AND ("Head and Neck"[tiab] OR "HNSCC"[tiab] OR "SCCHN"[tiab] OR "Oral"[tiab] OR "Mouth"[tiab] OR "Lip"[tiab] OR "Tongue"[tiab] OR "Gingival"[tiab] OR "Palate"[tiab] OR "Pharynx"[tiab] OR "Pharyngeal"[tiab] OR "Nasopharynx"[tiab] OR "Oropharynx"[tiab] OR "Hypopharynx"[tiab] OR "Larynx"[tiab] OR "Laryngeal"[tiab] OR "Epiglottis"[tiab] OR "Voice Box"[tiab] OR "Sino-nasal"[tiab] OR "Paranasal"[tiab] OR "Maxillary Sinus"[tiab] OR "Ethmoid Sinus"[tiab] OR "Salivary"[tiab] OR "Parotid"[tiab] OR "Submandibular"[tiab] OR "Thyroid"[tiab] OR "Parathyroid"[tiab] OR "Skull Base"[tiab] OR "Esthesioneuroblastoma"[tiab] OR "Olfactory Neuroblastoma"[tiab] OR "Chordoma"[tiab] OR "Nasopharyngeal Carcinoma"[tiab] OR "SNUC"[tiab] OR "NUT Carcinoma"[tiab] OR "Ameloblastoma"[tiab])) NOT ("Case Reports"[pt] OR "Letter"[pt] OR "Comment"[pt] OR "Published Erratum"[pt])"""

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
        response = requests.get(ESEARCH_URL, params=params, timeout=30)
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
                
                # Extract publication date
                pub_date = article.find('.//PubDate')
                date_str = ''
                if pub_date is not None:
                    year = pub_date.find('Year')
                    month = pub_date.find('Month')
                    day = pub_date.find('Day')
                    
                    year_text = year.text if year is not None else ''
                    month_text = month.text if month is not None else ''
                    day_text = day.text if day is not None else ''
                    
                    date_str = f"{year_text}-{month_text}-{day_text}".strip('-')
                
                # Extract journal
                journal_elem = article.find('.//Journal/Title')
                journal = journal_elem.text if journal_elem is not None else 'Unknown Journal'
                
                # Construct PubMed URL
                pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid_text}/"
                
                papers.append({
                    'pmid': pmid_text,
                    'title': title,
                    'abstract': abstract,
                    'journal': journal,
                    'date': date_str,
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
def is_head_and_neck_cancer(paper: dict) -> bool:
    """
    Use OpenAI to classify if a paper is related to head and neck cancer.
    """
    text = f"Title: {paper['title']}\n\nAbstract: {paper['abstract']}"
    
    prompt = f"""You are a biomedical expert.
Answer ONLY "YES" or "NO".

Is the following paper related to head and neck cancer
(including oral, laryngeal, tonsil, oropharynx, pharyngeal, larynx,
hypopharynx, nasopharynx, nasal, thyroid, head and neck skin SCC,
salivary gland cancers, rare head and neck cancer)?

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
    """Create an RSS channel structure."""
    rss = etree.Element("rss", version="2.0")
    channel = etree.SubElement(rss, "channel")

    etree.SubElement(channel, "title").text = title
    etree.SubElement(channel, "link").text = "https://pubmed.ncbi.nlm.nih.gov"
    etree.SubElement(channel, "description").text = description
    etree.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    return rss, channel

def add_paper_to_channel(channel, paper: dict):
    """Add a paper to an RSS channel."""
    item = etree.SubElement(channel, "item")
    etree.SubElement(item, "title").text = paper['title']
    etree.SubElement(item, "link").text = paper['url']
    etree.SubElement(item, "guid").text = paper['url']
    
    # Create description with abstract and metadata
    description = f"<b>Journal:</b> {paper['journal']}<br/><br/>"
    if paper['abstract']:
        description += f"<b>Abstract:</b> {paper['abstract']}"
    else:
        description += "<i>No abstract available</i>"
    
    etree.SubElement(item, "description").text = description
    etree.SubElement(item, "pubDate").text = paper['date']

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
            if is_head_and_neck_cancer(paper):
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
