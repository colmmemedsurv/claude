import os
import openai
import feedparser
import requests
from lxml import etree
from datetime import datetime
import time

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
RSS_FEED_URL = (
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/"
    "1FKYAX__W2XmZZnH7wCJZ2gjg5p61zj0lAum4ErUZK11BzSsdZ/"
    "?limit=100"
)

OUTPUT_ACCEPTED = "output/filtered_feed.xml"
OUTPUT_REJECTED = "output/rejected_feed.xml"

openai.api_key = os.environ.get("OPENAI_API_KEY")

# --------------------------------------------------
# FETCH PUBMED RSS WITH HEADERS
# --------------------------------------------------
def fetch_pubmed_rss(url: str) -> feedparser.FeedParserDict:
    """
    Fetch PubMed RSS feed with proper headers.
    PubMed requires a User-Agent and may block automated requests.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; PubMedRSSBot/1.0; +https://github.com/yourusername/yourrepo)",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }

    print(f"Fetching RSS feed from: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        print(f"Successfully fetched RSS feed (status code: {response.status_code})")
        print(f"Content length: {len(response.text)} characters")
        
        # Parse the feed
        feed = feedparser.parse(response.text)
        
        # Check for parsing errors
        if feed.bozo:
            print(f"Warning: Feed parsing issue: {feed.bozo_exception}")
        
        return feed
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching RSS feed: {e}")
        raise

# --------------------------------------------------
# OPENAI CLASSIFICATION (USER-SUPPLIED QUERY)
# --------------------------------------------------
def is_head_and_neck_cancer(text: str) -> bool:
    """
    Use OpenAI to classify if a paper is related to head and neck cancer.
    Returns True if related, False otherwise.
    """
    prompt = f"""You are a biomedical expert.
Answer ONLY "YES" or "NO".

Is the following paper related to head and neck cancer
(including oral, laryngeal, tonsil, oropharynx, pharyngeal, larynx,
hypopharynx, nasopharynx, nasal, thyroid, head and neck skin SCC,
salivary gland cancers, rare head and neck cancer)?

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
        print(f"Error calling OpenAI API: {e}")
        # In case of error, default to accepting (safer than rejecting)
        return True

# --------------------------------------------------
# RSS HELPERS
# --------------------------------------------------
def create_channel(title: str, link: str, description: str):
    """Create an RSS channel structure."""
    rss = etree.Element("rss", version="2.0")
    channel = etree.SubElement(rss, "channel")

    etree.SubElement(channel, "title").text = title
    etree.SubElement(channel, "link").text = link
    etree.SubElement(channel, "description").text = description
    etree.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    return rss, channel

def add_item(channel, entry):
    """Add an RSS item to a channel."""
    item = etree.SubElement(channel, "item")
    etree.SubElement(item, "title").text = entry.title
    etree.SubElement(item, "link").text = entry.link
    etree.SubElement(item, "guid").text = entry.id
    etree.SubElement(item, "description").text = entry.get("summary", "")
    etree.SubElement(item, "pubDate").text = entry.get("published", "")

# --------------------------------------------------
# MAIN
# --------------------------------------------------
def main():
    print("=" * 60)
    print("PubMed RSS Feed Filter - Head and Neck Cancer")
    print("=" * 60)
    
    # Fetch the feed
    feed = fetch_pubmed_rss(RSS_FEED_URL)

    if not feed.entries:
        error_msg = (
            "PubMed RSS returned zero entries. "
            "Check User-Agent and feed URL. "
            f"Feed info: {feed.feed.get('title', 'No title')}"
        )
        print(f"ERROR: {error_msg}")
        raise RuntimeError(error_msg)

    print(f"\nFound {len(feed.entries)} entries to process")

    # Create output RSS structures
    accepted_rss, accepted_channel = create_channel(
        "Filtered PubMed – Head and Neck Cancer",
        RSS_FEED_URL,
        "Papers classified as related to head and neck cancer"
    )

    rejected_rss, rejected_channel = create_channel(
        "Rejected PubMed Papers – Not Head and Neck Cancer",
        RSS_FEED_URL,
        "Papers rejected by the automated classifier"
    )

    accepted_count = 0
    rejected_count = 0
    error_count = 0

    # Process each entry
    print("\nProcessing entries...")
    for i, entry in enumerate(feed.entries, 1):
        print(f"\n[{i}/{len(feed.entries)}] Processing: {entry.title[:60]}...")
        
        text_blob = f"{entry.title}\n\n{entry.get('summary', '')}"

        try:
            if is_head_and_neck_cancer(text_blob):
                add_item(accepted_channel, entry)
                accepted_count += 1
                print("  ✓ ACCEPTED")
            else:
                add_item(rejected_channel, entry)
                rejected_count += 1
                print("  ✗ REJECTED")
                
            # Small delay to avoid rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ⚠ ERROR processing entry: {e}")
            # Add to rejected by default if error occurs
            add_item(rejected_channel, entry)
            error_count += 1

    # Create output directory
    os.makedirs("output", exist_ok=True)

    # Write output files
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
    print("RESULTS:")
    print(f"  Accepted papers: {accepted_count}")
    print(f"  Rejected papers: {rejected_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total processed: {len(feed.entries)}")
    print("=" * 60)
    print(f"\nOutput files created:")
    print(f"  - {OUTPUT_ACCEPTED}")
    print(f"  - {OUTPUT_REJECTED}")

# --------------------------------------------------
if __name__ == "__main__":
    main()
