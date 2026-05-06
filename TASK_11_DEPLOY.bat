@echo off
REM Task 11 — Deployment to Production (Railway)
REM Morning Brief Redesign — Production Deployment Script
REM Run this on your local machine (NOT in the Cowork sandbox)

setlocal enabledelayedexpansion

echo.
echo ==========================================
echo Task 11: Deploy Morning Brief to Production
echo ==========================================
echo.

REM Step 1: Navigate to project root
cd /d "C:\Users\loyan\Documents\Antigravity\cryptoscanner"
if errorlevel 1 (
    echo ERROR: Could not navigate to project directory
    exit /b 1
)

REM Step 2: Verify git status
echo [1/5] Verifying git status...
git status --porcelain morning_brief.py >nul 2>&1
if errorlevel 0 (
    echo Checking morning_brief.py for uncommitted changes...
)

git status

echo.
echo [2/5] Checking current branch and remote...
for /f %%i in ('git rev-parse --abbrev-ref HEAD') do set "current_branch=%%i"
echo Current branch: %current_branch%

echo.
echo [3/5] Pushing to GitHub...
echo Executing: git push origin %current_branch%
echo.

git push origin %current_branch%

if errorlevel 1 (
    echo.
    echo ERROR: Push failed
    echo Check your GitHub authentication and try again
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Push completed!
echo.

echo [4/5] Deployment initiated — Railway is auto-deploying...
echo Railway will auto-redeploy when it detects the push.
echo Wait 2-3 minutes for deployment to complete.
echo.
echo Monitor deployment at:
echo   https://railway.app/project/[YOUR_PROJECT_ID]
echo.

echo [5/5] Verification checklist...
echo.
echo ==========================================
echo Production Verification URLs
echo ==========================================
echo.
echo After 2-3 minutes, verify at:
echo   https://46.225.234.71/brief
echo   OR
echo   https://web-production-34b51.up.railway.app/brief
echo.

echo.
echo ==========================================
echo Visual Design Checklist:
echo ==========================================
echo.
echo   [ ] Page loads without error (200 OK)
echo   [ ] Gradient bleu/violet visible in background
echo   [ ] Header with logo + date/time in French
echo   [ ] Score card with colored progress bar
echo.

echo.
echo ==========================================
echo Interactive Elements Checklist:
echo ==========================================
echo.
echo   [ ] Sections are clickable (expand/collapse toggle)
echo   [ ] Medals visible on altcoin rankings
echo   [ ] Tables display with proper styling
echo.

echo.
echo ==========================================
echo Layout Checklist:
echo ==========================================
echo.
echo   [ ] Fear ^& Greed index in 2-column layout
echo   [ ] All sections properly formatted
echo   [ ] Responsive design works on mobile
echo.

echo.
echo ==========================================
echo Browser Console Checklist:
echo ==========================================
echo.
echo   [ ] No JavaScript errors in console (F12)
echo   [ ] No 404 errors in network tab
echo.

echo.
echo ==========================================
echo Next Steps:
echo ==========================================
echo.
echo If all checks pass:
echo   Task 11 is COMPLETE!
echo.
echo If errors occur:
echo   1. Check Railway logs: railway logs
echo   2. Review morning_brief.py syntax
echo   3. Verify environment variables in Railway
echo.

pause
