# Optional local helper

You do **not** need anything in this folder to use the tracker. It is for people comfortable running a small Python script.

`pokemon_tracker_server.py` is a tiny local server (Python's standard library only, nothing to install). Run it, leave its window open, and reload the tracker page. It then:

- fetches **daily TCGplayer prices for whole sets** from [TCGCSV](https://tcgcsv.com), which browsers can't read directly;
- can **backfill past prices** (up to a year) so the Portfolio chart shows real history. This uses the `tar` that ships with Windows 10/11, or 7-Zip; a few days' archives can't be read and are skipped;
- can **keep your data in `tracker-data.json`** next to the script, when you open the tracker through the helper's own address, `http://localhost:8765`.

Start it with `python pokemon_tracker_server.py`, or double-click `Start Pokemon Tracker.bat` on Windows. Stop it with Ctrl+C. It only listens on your own computer, and only your own pages can read from it.

The tracker file is expected one folder up (the main folder of the project) or next to the script.
