# Pokémon Set Tracker

**Download one file, open it, start tracking.** No installs, no accounts, no code.

> Unofficial fan project. Not affiliated with or endorsed by Nintendo, The Pokémon Company, TCGplayer, or any service named below. Pokémon and card names are trademarks of their owners.

## Get started

1. **[Download pokemon-set-tracker.html](https://github.com/Prisonmike1108/pokemon-set-tracker/releases/latest/download/pokemon-set-tracker.html)**
2. **Double-click it.** It opens in your web browser. I tested it in Chrome-style browsers (Chrome, Edge); others should work but I haven't tried them.
3. **Tick off cards.** Open the **Sets** tab, pick a set (Base Set, Jungle and Fossil are ready; press **+ Add set** for any other), and check the cards you own. Use the **Portfolio** tab to log cards with condition and what you paid.

Keep the file somewhere you'll find it, such as your Desktop. Your collection is saved inside your browser on that computer, so use the same browser each time, and press **Export** now and then to save a backup file. **Import** puts it back, or moves it to another computer.

## What you get

- **Set checklists:** every card with its picture, rarity, a search box and filters, plus a wishlist and a separate "1st Edition" toggle.
- **Unlimited by default:** prices and logging assume the Unlimited printing, with 1st Edition as its own choice. For Jungle, Fossil, Team Rocket, Gym and Neo, where TCGplayer only has 1st Edition pictures, the app shows Unlimited scans instead.
- **Portfolio:** total value, profit and loss, top gainers and losers, and a chart over time.
- **Buy links:** each card links to the live TCGplayer listings for the condition and printing you pick, so you can compare sellers and shipping there.

## Getting fresh prices (optional)

Out of the box prices come from a free feed that updates rarely and has nothing for the newest sets. To get fresh TCGplayer prices, including a real price for each condition:

1. Create a free account at [justtcg.com](https://justtcg.com) and choose the **Free** plan (100 lookups a day).
2. Copy your API key from their dashboard.
3. In the tracker, click the **⚙** button, paste the key and press **Save & test**.

The key stays in your browser and is left out of your backup files. *This feature was built from JustTCG's documented interface and tested against a stand-in, not the live service, so treat it as unproven until you try your key.*

## Good to know

- It's a personal tool, tested by hand in a browser. There is no automated test suite for the page.
- The list of sets is a snapshot (its date is shown in **+ Add set**). Sets released later will arrive in a newer version of the file.
- Card pictures load from the internet, so you need to be online to see them: TCGplayer, [Scrydex](https://scrydex.com), the Pokémon TCG API, and for the older sets above, [Pokellector](https://www.pokellector.com), whose scans carry their watermark in the enlarged view. Please be considerate of their servers.
- Prices are estimates, not offers to buy or sell. A condition without a real price is valued as a percentage of Near Mint, which you can adjust under ⚙.
- Browsers can clear saved data (for example when you clear browsing data), so keep an Export backup.

## Credits

Set and card catalog snapshot from [TCGCSV](https://tcgcsv.com) (TCGplayer data). Prices from TCGplayer via TCGCSV, pokemontcg.io, or [JustTCG](https://justtcg.com).

## For power users (optional)

The [`extras`](extras) folder has a small Python helper that fetches daily prices for whole sets, can backfill up to a year of price history, and can keep your data in a file. You do not need it for anything above.
