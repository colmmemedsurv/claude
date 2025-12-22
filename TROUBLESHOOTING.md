# Troubleshooting Guide

## Issue: "PubMed RSS returned zero entries"

### Symptoms
- Workflow runs but fails with error message
- Log shows "ERROR: PubMed RSS returned zero entries"

### Causes & Solutions

**1. PubMed blocking GitHub Actions IP addresses**
- PubMed may temporarily block automated requests from GitHub's servers
- **Solution A:** Wait 1-2 hours and try again
- **Solution B:** Try running at different times of day
- **Solution C:** Use a different RSS feed URL from PubMed

**2. RSS feed URL is invalid or empty**
- The search that generates your RSS may have no results
- **Solution:** Check the RSS URL in your browser first
  - Visit: https://pubmed.ncbi.nlm.nih.gov/rss/search/1FKYAX__W2XmZZnH7wCJZ2gjg5p61zj0lAum4ErUZK11BzSsdZ/?limit=100
  - Make sure you see XML content with `<item>` entries
  - If empty, update your PubMed search to include more results

**3. User-Agent being rejected**
- The script already includes proper headers
- **Solution:** Update the User-Agent in `filter_pubmed.py`:
  ```python
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  ```

---

## Issue: "OpenAI API Error" or "Invalid API Key"

### Symptoms
- Workflow fails at "Run RSS filter" step
- Error message mentions OpenAI or API key

### Solutions

**1. API Key not set correctly**
- Go to: Repository → Settings → Secrets and variables → Actions
- Verify `OPENAI_API_KEY` exists
- Make sure there are no extra spaces or characters
- The key should start with `sk-...`

**2. API Key has no credits**
- Go to: https://platform.openai.com/account/billing
- Check if you have available credits
- Add payment method if needed

**3. Rate limiting**
- The script already includes delays between requests
- If you have many papers, you may hit rate limits
- **Solution:** Reduce `limit=100` to `limit=50` in RSS_FEED_URL

---

## Issue: "Workflow doesn't run automatically"

### Symptoms
- Workflow doesn't run daily as scheduled
- Only runs when you trigger manually

### Solutions

**1. Enable GitHub Actions**
- Go to: Repository → Settings → Actions → General
- Under "Actions permissions", select "Allow all actions and reusable workflows"

**2. Repository must have recent activity**
- GitHub disables scheduled workflows on inactive repositories
- **Solution:** Make any commit (even updating README) every 60 days

**3. Check workflow schedule**
- Verify the cron schedule in `.github/workflows/filter_rss.yml`
- Remember: cron uses UTC time, not your local time

---

## Issue: "Output files not appearing"

### Symptoms
- Workflow completes successfully
- No `output/` folder or files in repository

### Solutions

**1. Check git permissions**
- The workflow needs permission to push changes
- Go to: Settings → Actions → General
- Scroll to "Workflow permissions"
- Select "Read and write permissions"
- Check "Allow GitHub Actions to create and approve pull requests"
- Save changes

**2. Files might be in Artifacts instead**
- Go to: Actions tab → (your workflow run)
- Scroll down to "Artifacts" section
- Download `filtered-rss-feeds.zip`
- This happens if git push fails

---

## Issue: "All papers are being rejected/accepted"

### Symptoms
- One output file is empty or has all papers
- Classification seems wrong

### Solutions

**1. Adjust the classification prompt**
- Edit `filter_pubmed.py`
- Modify the prompt in `is_head_and_neck_cancer()` function
- Make the criteria more/less strict

**2. Check OpenAI model**
- Ensure you're using `gpt-4o-mini` or `gpt-4`
- Older models may not classify as accurately

**3. Verify with manual test**
- Copy a paper title and abstract
- Ask ChatGPT: "Is this about head and neck cancer?"
- If ChatGPT also gets it wrong, refine your prompt

---

## Issue: "Workflow takes too long"

### Symptoms
- Processing 100 papers takes 10+ minutes
- Workflow times out

### Solutions

**1. Reduce number of papers**
- Change RSS URL from `limit=100` to `limit=50`
- This will process faster

**2. The script already includes rate limiting**
- 0.5 second delay between API calls is necessary
- Removing it will cause API errors

**3. Use faster model**
- Already using `gpt-4o-mini` (fastest and cheapest)
- Don't change to GPT-4 (slower and more expensive)

---

## Issue: "Cannot access RSS feed URL"

### Symptoms
- Browser can access the feed
- GitHub Actions cannot

### Solutions

**1. IP blocking by PubMed**
- PubMed may block GitHub's IP ranges
- **Workaround A:** Save RSS to repository and filter from there
- **Workaround B:** Use a different hosting service (not recommended for beginners)
- **Workaround C:** Contact PubMed support to whitelist GitHub Actions

**2. Authentication required**
- Some PubMed RSS feeds require authentication
- Check if your search is private or public
- Make sure the RSS URL is publicly accessible

---

## Testing Locally

Want to test before running on GitHub?

### Setup Local Environment

```bash
# Install Python 3.11+
python --version

# Create virtual environment
python -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set your API key
# On Mac/Linux:
export OPENAI_API_KEY="sk-your-key-here"
# On Windows:
set OPENAI_API_KEY=sk-your-key-here

# Run the script
python filter_pubmed.py
```

If it works locally but not on GitHub, the issue is GitHub-specific (likely IP blocking).

---

## Still Having Issues?

1. **Check the workflow logs**
   - Actions tab → Click on failed workflow
   - Click on "filter-rss" job
   - Read error messages carefully

2. **Enable debug logging**
   - Add this to `.github/workflows/filter_rss.yml` before "Run RSS filter":
   ```yaml
   - name: Enable debug logging
     run: echo "ACTIONS_STEP_DEBUG=true" >> $GITHUB_ENV
   ```

3. **Open an issue**
   - Include the error message
   - Include the workflow log
   - Describe what you've tried

---

## Common Error Messages Explained

**"ModuleNotFoundError: No module named 'openai'"**
→ Dependencies not installed. Check `requirements.txt` exists and is correct.

**"Response [403] Forbidden"**
→ PubMed is blocking the request. Try different User-Agent or wait and retry.

**"RateLimitError"**
→ Too many OpenAI API requests. The script has delays, but you may need to reduce paper count.

**"remote: Permission to user/repo.git denied"**
→ Workflow doesn't have write permissions. Check Settings → Actions → Workflow permissions.

**"feed.entries is empty"**
→ RSS feed has no papers. Verify the feed URL in your browser.
