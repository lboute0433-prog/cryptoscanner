#!/bin/bash
# Task 11 — Deployment to Production (Railway)
# Morning Brief Redesign — Production Deployment Script
# Run this on your local machine (NOT in the Cowork sandbox)

set -e

echo "=========================================="
echo "Task 11: Deploy Morning Brief to Production"
echo "=========================================="
echo ""

# Step 1: Verify git status
echo "[1/5] Vérifying git status..."
cd "C:\Users\loyan\Documents\Antigravity\cryptoscanner"

# Check if morning_brief.py is already committed
git_status=$(git status --porcelain morning_brief.py 2>/dev/null || echo "")
if [ -z "$git_status" ]; then
    echo "✓ morning_brief.py already staged/committed"
else
    echo "! morning_brief.py has uncommitted changes"
    echo "Staging changes..."
    git add morning_brief.py
    git commit -m "refactor: morning brief redesign — CSS + HTML refactoring (Tasks 1-9)

- Task 1-5: CSS variables, card styles, table styles (Approche C), winners/losers, footer
- Task 6-7: Toggle JS, HTML header, sections with proper classes
- Task 8-9: Performance bars, remaining sections refactored
- Changes: Added 11 CSS variables, gradient bg, ranking medals, hover effects, responsive mobile
- All CSS inline for Telegram compatibility
- Production-ready for Railway deployment" || echo "✓ No new changes to commit"
fi

echo ""
echo "[2/5] Checking current branch and remote..."
current_branch=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $current_branch"

# If we're on master, ensure it's up to date with origin
if [ "$current_branch" = "master" ]; then
    echo "On master branch. Checking remote..."
    git remote -v
fi

echo ""
echo "[3/5] Pushing to GitHub..."
echo "Executing: git push origin $current_branch"
git push origin "$current_branch"

if [ $? -eq 0 ]; then
    echo "✓ Push successful"
else
    echo "! Push failed. Check your GitHub authentication."
    exit 1
fi

echo ""
echo "[4/5] Deployment initiated — Railway is auto-deploying..."
echo "Railway will auto-redeploy when it detects the push."
echo "Wait 2-3 minutes for deployment to complete."
echo ""
echo "Monitor deployment at:"
echo "  https://railway.app/project/[YOUR_PROJECT_ID]"
echo ""

echo "[5/5] Verification checklist..."
echo ""
echo "After 2-3 minutes, verify production at:"
echo "  https://46.225.234.71/brief"
echo "  OR"
echo "  https://web-production-34b51.up.railway.app/brief"
echo ""
echo "═══════════════════════════════════════════"
echo "Checklist (verify all items):"
echo "═══════════════════════════════════════════"
echo ""
echo "Visual Design:"
echo "  [ ] Page loads without error (200 OK)"
echo "  [ ] Gradient bleu/violet visible in background"
echo "  [ ] Header with logo + date/time in French"
echo "  [ ] Score card with colored progress bar"
echo ""
echo "Interactive Elements:"
echo "  [ ] Sections are clickable (expand/collapse toggle)"
echo "  [ ] Medals 🥇🥈🥉 visible on altcoin rankings"
echo "  [ ] Tables display with proper styling"
echo ""
echo "Layout:"
echo "  [ ] Fear & Greed index in 2-column layout"
echo "  [ ] All sections properly formatted"
echo "  [ ] Responsive design works on mobile"
echo ""
echo "Browser Console:"
echo "  [ ] No JavaScript errors in console (F12)"
echo "  [ ] No 404 errors in network tab"
echo ""
echo "═══════════════════════════════════════════"
echo ""
echo "If all checks pass: Task 11 complete!"
echo "If errors occur: Check Railway logs (railway logs)"
echo ""
echo "═══════════════════════════════════════════"
