@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Publish SensMatch to GitHub

rem ---- tools -----------------------------------------------------------
where git >nul 2>nul || (
  echo Installing Git...
  winget install --id Git.Git -e --silent --accept-package-agreements --accept-source-agreements
  echo.
  echo Git installed. Close this window and double-click publish.bat again.
  goto fail
)
where gh >nul 2>nul || (
  echo Installing GitHub CLI...
  winget install --id GitHub.cli -e --silent --accept-package-agreements --accept-source-agreements
  echo.
  echo GitHub CLI installed. Close this window and double-click publish.bat again.
  goto fail
)
gh auth status >nul 2>nul || (
  echo Sign in to GitHub in the browser window that opens...
  gh auth login --web --git-protocol https || goto fail
)
gh auth setup-git >nul 2>nul

if not exist "SensMatch.exe" (
  echo SensMatch.exe isn't in this folder. Run build.bat first.
  goto fail
)

rem ---- which repository (asked once) -----------------------------------
set "REPO=thelionzmusic/SensMatch"
if exist ".publish-repo" set /p REPO=<".publish-repo"
if defined REPO goto have_repo
echo.
set /p REPO=Your repository, like yourname/SensMatch: 
if not defined REPO goto fail
>".publish-repo" echo %REPO%
:have_repo
echo Repository: %REPO%

rem ---- version from sensmatch.py -----------------------------------------
for /f "tokens=2 delims==" %%v in ('findstr /b /c:"VERSION =" sensmatch.py') do set "V=%%v"
set "V=%V: =%"
set "V=%V:"=%"
if not defined V (
  echo Couldn't read VERSION from sensmatch.py.
  goto fail
)
echo Version: %V%
echo.

rem ---- link this folder to the repository (first run only) --------------
if exist ".git" goto have_git
git init -q -b main || goto fail
git remote add origin https://github.com/%REPO%.git || goto fail
git fetch -q origin || goto fail
git reset -q origin/main || goto fail
for /f "delims=" %%f in ('git ls-files -d') do git checkout -q -- "%%f"
:have_git

rem ---- commit identity (uses GitHub's private no-reply address) ---------
git config user.email >nul 2>nul && goto have_id
for /f %%i in ('gh api user --jq .id') do set "GHID=%%i"
for /f %%l in ('gh api user --jq .login') do set "GHLOGIN=%%l"
git config user.name "%GHLOGIN%"
git config user.email "%GHID%+%GHLOGIN%@users.noreply.github.com"
:have_id

if not exist ".gitignore" (
  >".gitignore" (
    echo SensMatch.exe
    echo build/
    echo dist/
    echo *.spec
    echo baked.json
    echo __pycache__/
    echo .publish-repo
  )
)

rem ---- upload the code ---------------------------------------------------
echo Uploading code...
git add sensmatch.py build.bat publish.bat sensmatch.ico .gitignore
if exist README.md git add README.md
if exist release-notes.txt git add release-notes.txt
git commit -q -m "SensMatch %V%" || echo (No code changes since last time.)
git pull -q --rebase --autostash origin main || goto fail
git push -q -u origin main || goto fail

rem ---- upload the exe as a release ---------------------------------------
echo Uploading SensMatch.exe...
gh release view v%V% --repo %REPO% >nul 2>nul && goto update_release
if exist release-notes.txt (
  gh release create v%V% SensMatch.exe --repo %REPO% --title "SensMatch %V%" --notes-file release-notes.txt || goto fail
) else (
  gh release create v%V% SensMatch.exe --repo %REPO% --title "SensMatch %V%" --generate-notes || goto fail
)
goto done

:update_release
echo Release v%V% already exists, replacing its SensMatch.exe...
gh release upload v%V% SensMatch.exe --repo %REPO% --clobber || goto fail

:done
echo.
echo Done. Your download link:
echo https://github.com/%REPO%/releases/latest
start "" "https://github.com/%REPO%/releases/latest"
pause
exit /b 0

:fail
echo.
echo Stopped. Scroll up to see what went wrong.
pause
exit /b 1
