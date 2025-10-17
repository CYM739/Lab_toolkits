@echo off
REM This script adds all changes, commits them with a user-provided message,
REM and pushes them to the 'main' branch on GitHub.

echo --- Staging all new and modified files...
git add .

echo.
REM Prompt the user for a commit message
set /p commit_message="Enter a description for your changes: "

IF "%commit_message%"=="" (
    echo No commit message entered. Aborting commit.
    pause
    exit /b
)

echo.
echo --- Committing changes...
git commit -m "%commit_message%"

echo.
echo --- Pushing updates to GitHub...
git push origin main

echo.
echo --- ✅ Update complete! ---
pause