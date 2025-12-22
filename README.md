# PubMed RSS Feed Filter for Head and Neck Cancer

This repository automatically filters a PubMed RSS feed to identify papers related to head and neck cancer using OpenAI's GPT-4 model. It runs daily via GitHub Actions and produces two RSS feed files:

1. **filtered_feed.xml** - Papers classified as relevant to head and neck cancer
2. **rejected_feed.xml** - Papers classified as not relevant

## 📋 Features

- ✅ Automated daily RSS feed filtering
- ✅ OpenAI GPT-4 classification
- ✅ Separate feeds for accepted and rejected papers
- ✅ Manual trigger option
- ✅ Artifact storage for historical data
- ✅ Automatic git commits of results

## 🚀 Setup Instructions

### Step 1: Create a New GitHub Repository

1. Go to [GitHub](https://github.com) and log in
2. Click the **"+"** icon in the top right corner
3. Select **"New repository"**
4. Name it (e.g., `pubmed-hnc-filter`)
5. Choose **Public** or **Private**
6. Check **"Add a README file"** (optional - we'll replace it)
7. Click **"Create repository"**

### Step 2: Add Your OpenAI API Key

1. In your GitHub repository, click on **"Settings"** tab
2. In the left sidebar, click **"Secrets and variables"** → **"Actions"**
3. Click **"New repository secret"**
4. Name: `OPENAI_API_KEY`
5. Value: Paste your OpenAI API key (starts with `sk-...`)
6. Click **"Add secret"**

### Step 3: Upload Files to Your Repository

You need to create the following file structure in your repository:

```
your-repo/
├── .github/
│   └── workflows/
│       └── filter_rss.yml
├── .gitignore
├── filter_pubmed.py
├── requirements.txt
└── README.md
```

**Option A: Using GitHub Web Interface**

1. Click **"Add file"** → **"Create new file"**
2. For the workflow file, type: `.github/workflows/filter_rss.yml`
   - GitHub will automatically create the folders
3. Copy the contents from `filter_rss.yml` (provided below)
4. Click **"Commit changes"**
5. Repeat for each file

**Option B: Using Git Command Line**

```bash
# Clone your repository
git clone https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
cd YOUR-REPO-NAME

# Create the workflow directory
mkdir -p .github/workflows

# Copy or create all the files (see file contents below)
# Then commit and push
git add .
git commit -m "Initial setup"
git push origin main
```

### Step 4: Enable GitHub Actions

1. Go to your repository on GitHub
2. Click the **"Actions"** tab
3. If you see a message about workflows, click **"I understand my workflows, go ahead and enable them"**

### Step 5: Run the Workflow Manually (First Time)

1. Click the **"Actions"** tab
2. Click on **"Filter PubMed RSS Feed"** in the left sidebar
3. Click **"Run workflow"** button (on the right)
4. Select the **main** branch
5. Click **"Run workflow"**

The workflow will start running! You can watch the progress in real-time.

## 📁 File Contents

### `.github/workflows/filter_rss.yml`

```yaml
name: Filter PubMed RSS Feed

on:
  # Run on schedule (daily at 6 AM UTC)
  schedule:
    - cron: '0 6 * * *'
  
  # Allow manual triggering
  workflow_dispatch:
  
  # Run on push to main (for testing)
  push:
    branches:
      - main

jobs:
  filter-rss:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run RSS filter
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python filter_pubmed.py
      
      - name: Upload filtered feed as artifact
        uses: actions/upload-artifact@v4
        with:
          name: filtered-rss-feeds
          path: output/
          retention-days: 30
      
      - name: Commit and push filtered feeds
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add output/
          git diff --staged --quiet || git commit -m "Update filtered RSS feeds - $(date +'%Y-%m-%d %H:%M:%S')"
          git push
```

### `requirements.txt`

```
openai==0.28.1
feedparser==6.0.11
requests==2.31.0
lxml==5.1.0
```

### `.gitignore`

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Local testing
.env
*.local

# Logs
*.log
```

### `filter_pubmed.py`

See the Python script in the main repository file.

## 📊 Output Files

After the workflow runs, you'll find two XML files in the `output/` directory:

- **`output/filtered_feed.xml`** - Contains papers classified as head and neck cancer related
- **`output/rejected_feed.xml`** - Contains papers classified as not related

These files are:
- Committed to your repository automatically
- Available as downloadable artifacts in the Actions tab
- Updated daily at 6 AM UTC

## 🔍 Viewing Results

**Option 1: View in Repository**
1. Go to your repository
2. Navigate to the `output/` folder
3. Click on `filtered_feed.xml` or `rejected_feed.xml`

**Option 2: Download Artifacts**
1. Go to **Actions** tab
2. Click on a completed workflow run
3. Scroll down to **Artifacts**
4. Download **filtered-rss-feeds.zip**

**Option 3: Subscribe to RSS Feed**
Use this URL in your RSS reader:
```
https://raw.githubusercontent.com/YOUR-USERNAME/YOUR-REPO/main/output/filtered_feed.xml
```

## ⚙️ Configuration

### Change the Schedule

Edit `.github/workflows/filter_rss.yml`:

```yaml
schedule:
  - cron: '0 6 * * *'  # Daily at 6 AM UTC
  # - cron: '0 */6 * * *'  # Every 6 hours
  # - cron: '0 0 * * 0'  # Weekly on Sunday
```

### Change the RSS Feed URL

Edit `filter_pubmed.py` and update:

```python
RSS_FEED_URL = "your-new-rss-url"
```

### Modify Classification Criteria

Edit the prompt in the `is_head_and_neck_cancer()` function in `filter_pubmed.py`.

## 🐛 Troubleshooting

### Workflow Fails with "No entries found"

**Problem:** PubMed RSS feeds can be sensitive to automated requests.

**Solutions:**
1. Verify the RSS feed URL works in your browser
2. Check that the feed actually contains entries
3. The script already includes proper headers - if it still fails, PubMed may be blocking GitHub's IP ranges

### OpenAI API Errors

**Problem:** "Invalid API key" or rate limit errors

**Solutions:**
1. Verify your API key is correct in GitHub Secrets
2. Check your OpenAI account has available credits
3. The script includes a 0.5-second delay between requests to avoid rate limiting

### No Output Files

**Problem:** Workflow runs but no files appear

**Solutions:**
1. Check the workflow logs in the Actions tab
2. Look for error messages in the "Run RSS filter" step
3. Ensure the `output/` directory is being created

## 📝 License

This project is provided as-is for educational and research purposes.

## 🤝 Contributing

Feel free to open issues or submit pull requests for improvements!

## 📧 Contact

For questions about this tool, please open an issue in this repository.

---

**Note:** This tool uses the OpenAI API which incurs costs. Monitor your usage at https://platform.openai.com/usage
