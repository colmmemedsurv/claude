import os
import openai
import feedparser
import requests
from lxml import etree
from datetime import datetime
import time
import json

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
CACHE_FILE = "feed_cache.json"

openai.api_key = os.environ.get("OPENAI_API_KEY")

# --------------------------------------------------
# FETCH PUBMED RSS WITH MULTIPLE FALLBACK METHODS
# --------------------------------------------------
def fetch_via_rss2json(url: str) -> feedparser.FeedParserDict:
    """
    Fetch RSS through rss2json.com API service as a workaround for PubMed blocking.
    This service acts as a proxy and can bypass IP blocks.
    """
    print("Attempting to fetch via rss2json.com proxy...")
    
    api_url = f"https://api.rss2json.com/v1/api.json?rss_url={requests.utils.quote(url)}&api_key=yourownkeyisfree&count=100"
    
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') != 'ok':
            raise Exception(f"rss2json error: {data.get('message', 'Unknown error')}")
        
        # Convert rss2json format to feedparser format
        feed = feedparser.FeedParserDict()
        feed.entries = []
        
        for item in data.get('items', []):
            entry = feedparser.FeedParserDict()
            entry.title = item.get('title', '')
            entry.link = item.get('link', '')
            entry.id = item.get('guid', item.get('link', ''))
            entry.summary = item.get('description', '')
            entry.published = item.get('pubDate', '')
            feed.entries.append(entry)
        
        print(f"✓ Successfully fetched {len(feed.entries)} entries via rss2json")
        return feed
        
    except Exception as e:
        print(f"✗ rss2json method failed: {e}")
        raise

def fetch_via_allorigins(url: str) -> feedparser.FeedParserDict:
    """
    Fetch RSS through allorigins.win proxy service.
    Another CORS proxy that can help bypass blocks.
    """
    print("Attempting to fetch via allorigins.win proxy...")
    
    proxy_url = f"https://api.allorigins.win/raw?url={requests.utils.quote(url)}"
    
    try:
        response = requests.get(proxy_url, timeout=30)
        response.raise_for_status()
        
        feed = feedparser.parse(response.text)
        
        if not feed.entries:
            raise Exception("No entries found in feed")
        
        print(f"✓ Successfully fetched {len(feed.entries)} entries via allorigins")
        return feed
        
    except Exception as e:
        print(f"✗ allorigins method failed: {e}")
        raise

def fetch_direct(url: str) -> feedparser.FeedParserDict:
    """
    Direct fetch with enhanced headers (may work sometimes).
    """
    print("Attempting direct fetch with enhanced headers...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        feed = feedparser.parse(response.text)
        
        if not feed.entries:
            raise Exception("No entries found in feed")
        
        print(f"✓ Successfully fetched {len(feed.entries)} entries directly")
        return feed
        
    except Exception as e:
        print(f"✗ Direct method failed: {e}")
        raise

def load_from_cache() -> feedparser.FeedParserDict:
    """
    Load feed from cache file as last resort.
    """
    print("Attempting to load from cache...")
    
    if not os.path.exists(CACHE_FILE):
        raise Exception("No cache file found")
    
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        feed = feedparser.FeedParserDict()
        feed.entries = []
        
        for item in data:
            entry = feedparser.FeedParserDict()
            entry.title = item.get('title', '')
            entry.link = item.get('link', '')
            entry.id = item.get('id', '')
            entry.summary = item.get('summary', '')
            entry.published = item.get('published', '')
            feed.entries.append(entry)
        
        print(f"✓ Loaded {len(feed.entries)} entries from cache")
        return feed
        
    except Exception as e:
        print(f"✗ Cache load failed: {e}")
        raise

def save_to_cache(feed: feedparser.FeedParserDict):
    """
    Save feed to cache for future use.
    """
    try:
        cache_data = []
        for entry in feed.entries:
            cache_data.append({
                'title': entry.title,
                'link': entry.link,
                'id': entry.id,
                'summary': entry.get('summary', ''),
                'published': entry.get('published', ''),
            })
        
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved {len(cache_data)} entries to cache")
    except Exception as e:
        print(f"⚠ Warning: Could not save cache: {e}")

def fetch_pubmed_rss(url: str) -> feedparser.FeedParserDict:
    """
    Fetch PubMed RSS with multiple fallback methods.
    Tries in order: rss2json, allorigins, direct, cache
    """
    print("=" * 60)
    print(f"Fetching RSS feed from: {url}")
    print("=" * 60)
    
    methods = [
        ("RSS2JSON Proxy", fetch_via_rss2json),
        ("AllOrigins Proxy", fetch_via_allorigins),
        ("Direct Fetch", fetch_direct),
        ("Cache Fallback", load_from_cache),
    ]
    
    last_error = None
    
    for method_name, method_func in methods:
        try:
            print(f"\n[Method {methods.index((method_name, method_func)) + 1}/4] {method_name}")
            feed = method_func(url)
            
            if feed.entries:
                print(f"✓ SUCCESS: Retrieved {len(feed.entries)} entries using {method_name}")
                
                # Save to cache for future use (unless we're loading from cache)
                if method_name != "Cache Fallback":
                    save_to_cache(feed)
                
                return feed
            else:
                print(f"✗ {method_name} returned no entries")
                
        except Exception as e:
            last_error = e
            print(f"✗ {method_name} failed: {str(e)[:100]}")
            continue
    
    # All methods failed
    print("\n" + "=" * 60)
    print("ERROR: All fetch methods failed!")
    print("=" * 60)
    raise RuntimeError(
        f"Could not fetch RSS feed using any method. "
        f"Last error: {last_error}"
    )

# --------------------------------------------------
# OPENAI CLASSIFICATION
# --------------------------------------------------
def is_head_and_neck_cancer(text: str) -> bool:
    """
    Use OpenAI to classify if a paper is related to head and neck cancer.
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
        print(f"⚠ Error calling OpenAI API: {e}")
        # Default to accepting to be safe
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
    print("\n" + "=" * 60)
    print("PubMed RSS Feed Filter - Head and Neck Cancer")
    print("=" * 60)
    
    # Fetch the feed with fallback methods
    try:
        feed = fetch_pubmed_rss(RSS_FEED_URL)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        print("\nTroubleshooting suggestions:")
        print("1. Check if the RSS feed URL works in your browser")
        print("2. Try running this script locally (not on GitHub Actions)")
        print("3. Check TROUBLESHOOTING.md for more solutions")
        raise

    if not feed.entries:
        raise RuntimeError("Feed was fetched but contains no entries")

    print(f"\n✓ Successfully retrieved {len(feed.entries)} papers to process")

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
    print("\n" + "=" * 60)
    print("Processing papers with OpenAI classification...")
    print("=" * 60)
    
    for i, entry in enumerate(feed.entries, 1):
        print(f"\n[{i}/{len(feed.entries)}] {entry.title[:70]}...")
        
        text_blob = f"{entry.title}\n\n{entry.get('summary', '')}"

        try:
            if is_head_and_neck_cancer(text_blob):
                add_item(accepted_channel, entry)
                accepted_count += 1
                print("  → ✓ ACCEPTED (relevant)")
            else:
                add_item(rejected_channel, entry)
                rejected_count += 1
                print("  → ✗ REJECTED (not relevant)")
                
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  → ⚠ ERROR: {e}")
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
    print("✓ COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print(f"Accepted papers:  {accepted_count}")
    print(f"Rejected papers:  {rejected_count}")
    print(f"Errors:           {error_count}")
    print(f"Total processed:  {len(feed.entries)}")
    print("=" * 60)
    print(f"\n📁 Output files created:")
    print(f"   • {OUTPUT_ACCEPTED}")
    print(f"   • {OUTPUT_REJECTED}")
    print()

if __name__ == "__main__":
    main()
