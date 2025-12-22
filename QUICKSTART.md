# Quick Start Guide - PubMed RSS Filter

## 🚀 5-Minute Setup

### 1. Create GitHub Repository
- Go to github.com
- Click "+" → "New repository"
- Name it (e.g., `pubmed-hnc-filter`)
- Click "Create repository"

### 2. Add OpenAI API Key
- In your repo: Settings → Secrets and variables → Actions
- Click "New repository secret"
- Name: `OPENAI_API_KEY`
- Value: Your OpenAI API key (sk-...)
- Click "Add secret"

### 3. Create Files

Create these files in your repository (you can use the GitHub web interface):

#### File 1: `.github/workflows/filter_rss.yml`
Copy the entire contents from the file in this package.

#### File 2: `filter_pubmed.py`
Copy the entire Python script from this package.

#### File 3: `requirements.txt`
```
openai==0.28.1
feedparser==6.0.11
requests==2.31.0
lxml==5.1.0
```

#### File 4: `.gitignore`
Copy from the package.

#### File 5: `README.md`
Copy from the package.

### 4. Run It!
- Go to Actions tab
- Click "Filter PubMed RSS Feed"
- Click "Run workflow" → "Run workflow"
- Wait 2-3 minutes

### 5. Get Your Results
- Check the `output/` folder in your repo
- Or download from Actions → (your workflow run) → Artifacts

## 📊 What You Get

Two RSS XML files:
- `filtered_feed.xml` - Head & neck cancer papers ✅
- `rejected_feed.xml` - Other papers ❌

## 🔄 Automatic Updates

The workflow runs:
- ✅ Daily at 6 AM UTC (automatic)
- ✅ When you click "Run workflow" (manual)
- ✅ When you push to main branch (automatic)

## ⚡ Common Issues

**"No entries found"**
→ The PubMed RSS might be empty or blocking GitHub. Try running manually.

**"OpenAI API Error"**
→ Check your API key in Settings → Secrets. Make sure you have OpenAI credits.

**Files not appearing**
→ Check Actions tab for error logs. The script creates an `output/` folder automatically.

## 💰 Cost Estimate

OpenAI API costs (using gpt-4o-mini):
- ~100 papers/day × $0.0001/paper = $0.01/day
- Monthly: ~$0.30
- Very affordable!

## 🔗 Subscribe to Your Feed

Once files are created, use this URL in any RSS reader:
```
https://raw.githubusercontent.com/YOUR-USERNAME/YOUR-REPO/main/output/filtered_feed.xml
```

Replace `YOUR-USERNAME` and `YOUR-REPO` with your actual values.

---

**Need help?** Check the full README.md or open an issue!
