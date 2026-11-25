# Pokémon Set Tracker

A single-file web app for tracking a Pokémon TCG collection: tick off cards set by set, keep a wishlist, log a portfolio with condition and price paid, and watch what it's worth over time. Open `pokemon-set-tracker.html` in a browser. There is nothing to install.

> Unofficial fan project. Not affiliated with or endorsed by Nintendo, The Pokémon Company, TCGplayer, or any service named below. Pokémon and card names are trademarks of their owners.

## What it does

- **Sets tab:** a grid of cards for each set, with checkboxes, rarity filters, search, a wishlist, and a separate "1st Edition owned" toggle. Add any set from a built-in list of every TCGplayer set (a snapshot, see below).
- **Portfolio tab:** log cards with printing, condition, quantity and what you paid. Shows total value, profit/loss, top gainers and losers, and a value chart.
- **Unlimited by default:** prices and logging default to the Unlimited printing; 1st Edition is a separate choice. For Jungle, Fossil, Team Rocket, Gym and Neo sets, where TCGplayer only has 1st Edition pictures, the app loads Unlimited scans from Pokellector instead.
- **Condition links:** each card links to the live TCGplayer listings for a chosen condition and printing, so you can compare sellers and shipping there.
- **Storage:** everything is saved in your browser (localStorage). **Export** and **Import** back up your collection, wishlist and portfolio as a JSON file.

## Getting prices

A web page can't read TCGplayer directly, so there are three ways to get prices, from least to most setup:

1. **Nothing:** uses a free feed (pokemontcg.io) that updates rarely and has nothing for the newest sets.
2. **A free [JustTCG](https://justtcg.com) key:** paste it under ⚙ settings. The page then asks JustTCG for the cards you own, wishlist or hold, including a real price for each condition. The free plan allows 100 lookups a day, 20 cards each. *This was built from JustTCG's documented API and tested against a mock, not against the live service, so treat it as unproven until you try your key.* The key stays in your browser and is left out of exports.
3. **The optional local helper:** `python pokemon_tracker_server.py` (or `Start Pokemon Tracker.bat` on Windows) runs a small local server, using only Python's standard library. It fetches daily TCGplayer prices from [TCGCSV](https://tcgcsv.com), can backfill up to a year of price history, and can keep your data in a `tracker-data.json` file next to it. It only listens on your own machine. Keep the window open and reload the page; you can still open the HTML file directly.

## Data and credits

- **Set and card catalog:** a snapshot (dated inside the file) of TCGplayer's Pokémon sets, cards and product ids, taken from [TCGCSV](https://tcgcsv.com). Sets released after the snapshot need the helper, or an updated file.
- **Card pictures** are loaded from the web, not stored here: TCGplayer product images, [Scrydex](https://scrydex.com), the Pokémon TCG API, and, for the older sets above, [Pokellector](https://www.pokellector.com) (whose scans carry their watermark in the enlarged view). Please be considerate of their servers.
- **Prices:** TCGplayer market prices via TCGCSV, pokemontcg.io, or JustTCG. They are estimates, not offers to buy or sell, and condition values without a real price are rough percentages of Near Mint that you can adjust in ⚙.

## Limits

- It is a personal tool, written quickly and tested by hand in a browser; there is no automated test suite for the page.
- Price history only starts when you first load a card, unless you use the helper's backfill (which needs the `tar` that ships with Windows 10/11, or 7-Zip; a few days' archives can't be read and are skipped).
- Browser storage can be cleared. Use **Export** now and then.

## Files

| File | Purpose |
| --- | --- |
| `pokemon-set-tracker.html` | The whole app. |
| `pokemon_tracker_server.py` | Optional local helper (prices, history backfill, data file). |
| `Start Pokemon Tracker.bat` | Windows shortcut to start the helper. |
