# Setup Checklist - Complete This in Order

## ✅ Step-by-Step Setup

### □ Step 1: Get Your OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Log in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)
5. **Important:** Save it somewhere safe - you won't see it again!

---

### □ Step 2: Create GitHub Repository
1. Go to https://github.com
2. Click the **+** icon (top right) → "New repository"
3. Repository name: `pubmed-hnc-filter` (or your choice)
4. Description (optional): "Automated PubMed RSS feed filter for head and neck cancer research"
5. Choose **Public** (recommended) or **Private**
6. ✅ Check "Add a README file"
7. Click **"Create repository"**

---

### □ Step 3: Add OpenAI API Key to GitHub
1. In your new repository, click **"Settings"** tab
2. Left sidebar: Click **"Secrets and variables"** → **"Actions"**
3. Click **"New repository secret"** (green button)
4. Name: `OPENAI_API_KEY` (must be exact)
5. Secret: Paste your OpenAI API key from Step 1
6. Click **"Add secret"**

---

### □ Step 4: Enable GitHub Actions Permissions
1. Still in Settings, click **"Actions"** → **"General"** (left sidebar)
2. Scroll to "Workflow permissions"
3. Select: ⦿ **"Read and write permissions"**
4. ✅ Check "Allow GitHub Actions to create and approve pull requests"
5. Click **"Save"**

---

### □ Step 5: Create Directory Structure

You'll create these files (use GitHub web interface):

#### File 1: Create `.github/workflows/filter_rss.yml`
1. Click **"Add file"** → **"Create new file"**
2. Type in the name: `.github/workflows/filter_rss.yml`
   - GitHub will automatically create folders when you type `/`
3. Copy-paste the entire contents from the `filter_rss.yml` file in this package
4. Scroll down and click **"Commit changes"** → **"Commit changes"**

#### File 2: Create `filter_pubmed.py`
1. Click **"Add file"** → **"Create new file"**
2. Name: `filter_pubmed.py`
3. Copy-paste the entire Python script
4. Click **"Commit changes"** → **"Commit changes"**

#### File 3: Create `requirements.txt`
1. Click **"Add file"** → **"Create new file"**
2. Name: `requirements.txt`
3. Copy-paste:
   ```
   openai==0.28.1
   feedparser==6.0.11
   requests==2.31.0
   lxml==5.1.0
   ```
4. Click **"Commit changes"** → **"Commit changes"**

#### File 4: Create `.gitignore`
1. Click **"Add file"** → **"Create new file"**
2. Name: `.gitignore`
3. Copy-paste the entire .gitignore contents
4. Click **"Commit changes"** → **"Commit changes"**

#### File 5: Replace `README.md`
1. Click on the existing `README.md` file
2. Click the pencil icon (✏️) to edit
3. Delete everything and paste the new README contents
4. Click **"Commit changes"** → **"Commit changes"**

---

### □ Step 6: Run Your First Workflow

1. Click the **"Actions"** tab at the top
2. If you see "Workflows aren't being run on this forked repository":
   - Click **"I understand my workflows, go ahead and enable them"**
3. In the left sidebar, click **"Filter PubMed RSS Feed"**
4. On the right side, click **"Run workflow"** dropdown
5. Make sure **"Branch: main"** is selected
6. Click the green **"Run workflow"** button
7. Wait a few seconds, then refresh the page
8. You should see a yellow dot (running) or green checkmark (completed)

---

### □ Step 7: Check Your Results

**Option A: View in Repository**
1. Click the **"Code"** tab
2. You should see a new `output/` folder
3. Click on it to see:
   - `filtered_feed.xml` ✅
   - `rejected_feed.xml` ❌

**Option B: Download from Artifacts**
1. Click **"Actions"** tab
2. Click on your completed workflow run (green checkmark)
3. Scroll down to **"Artifacts"**
4. Click **"filtered-rss-feeds"** to download ZIP file

---

## 🎉 Success Indicators

Your setup is working correctly if:
- ✅ Workflow shows green checkmark in Actions tab
- ✅ `output/` folder exists with two XML files
- ✅ XML files contain actual paper entries (not just placeholders)
- ✅ You can see "Accepted papers: X, Rejected papers: Y" in the logs

---

## 📱 Subscribe to Your Feed

Once everything is working, you can subscribe to your filtered feed:

**RSS Feed URL:**
```
https://raw.githubusercontent.com/YOUR-USERNAME/pubmed-hnc-filter/main/output/filtered_feed.xml
```

Replace `YOUR-USERNAME` with your actual GitHub username.

Use this URL in:
- Feedly
- Inoreader  
- Apple News
- Any RSS reader app

---

## 🔄 Ongoing Use

After initial setup, the workflow will:
- ✅ Run automatically every day at 6 AM UTC
- ✅ Update the XML files in your repository
- ✅ Keep 30 days of artifacts for download

You can also:
- 🔘 Trigger manually anytime (Actions → Run workflow)
- ⚙️ Change schedule in `.github/workflows/filter_rss.yml`
- 📝 Modify classification criteria in `filter_pubmed.py`

---

## ❓ Problems?

Check `TROUBLESHOOTING.md` for solutions to common issues:
- PubMed returning zero entries
- OpenAI API errors
- Files not appearing
- Workflow not running

---

## 💰 Cost Estimate

Using OpenAI GPT-4o-mini:
- ~100 papers/day = ~$0.01/day
- Monthly cost: ~$0.30
- Very affordable! ✨

---

## 🎯 You're Done!

Once you see green checkmarks and XML files with papers, you're all set.

The system will now automatically filter your PubMed feed every day! 🎊
