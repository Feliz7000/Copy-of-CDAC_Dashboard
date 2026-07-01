@echo off
echo Fixing npm dependencies...
echo.
echo Step 1: Removing node_modules...
rmdir /s /q node_modules >nul 2>&1
echo Done.
echo.
echo Step 2: Removing package-lock.json...
del package-lock.json >nul 2>&1
echo Done.
echo.
echo Step 3: Installing dependencies (this may take 2-3 minutes)...
npm install
echo.
echo Step 4: Running npm audit fix...
npm audit fix
echo.
echo ✓ All done! Dependencies fixed.
echo.
pause
