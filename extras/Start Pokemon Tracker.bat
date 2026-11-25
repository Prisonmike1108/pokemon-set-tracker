@echo off
cd /d "%~dp0"
echo Pokemon Tracker helper - leave this window open, then open pokemon-set-tracker.html as usual.
echo (Close this window, or press Ctrl+C, to stop it.)
echo.
where py >nul 2>nul && (py pokemon_tracker_server.py --no-browser & goto :eof)
python pokemon_tracker_server.py --no-browser
pause
