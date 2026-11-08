# Sources

Use the sources in this order. A higher source wins a conflict.

| Rank | Source | Use it for | Not for |
|---|---|---|---|
| 1 | Manufacturer datasheet (PDF) | specs, ordering codes, package drawing, bins | stock, price |
| 2 | Manufacturer product page | lifecycle status, variants, errata, app notes, CAD models | price |
| 3 | Manufacturer EOL / PCN / NRND notices | lifecycle changes | — |
| 4 | Authorized distributor page | price breaks, stock, factory lead time, packaging options | specs that conflict with rank 1 |
| 5 | Aggregator (Octopart, FindChips) | stock and price across distributors on one page | final prices (open the distributor page to confirm) |
| 6 | CAD libraries (SnapEDA, Ultra Librarian, KiCad libs, vendor GitHub) | footprints, symbols, 3D models | proof of pinout or package |
| — | Brokers, marketplaces, forums | signal only: "someone has stock", "people hit this bug" | any number in the BOM |

## Authorized distributors

| Distributor | Search URL pattern | Notes |
|---|---|---|
| DigiKey | `https://www.digikey.com/en/products/result?keywords=<MPN>` | price breaks, "Product Status", factory lead time, packaging variants (Cut Tape, Tape & Reel, Digi-Reel) |
| Mouser | `https://www.mouser.com/c/?q=<MPN>` | often times out for automated fetches; try the reader proxy |
| Arrow | `https://www.arrow.com/en/products/search?q=<MPN>` | good for large reels |
| Newark / Farnell | `https://www.newark.com/search?st=<MPN>` | EU and UK pricing through Farnell |
| LCSC | `https://www.lcsc.com/search?q=<MPN>` | needed when JLCPCB assembles: "basic" vs "extended" parts change the assembly fee |
| TI store and other maker stores | e.g. `https://www.ti.com/product/<base-part>` | the maker's own price and stock, often the best at 1k |

## Aggregators

- Octopart: `https://octopart.com/search?q=<MPN>`. Shows authorized and non-authorized sellers separately. Only the authorized column counts as orderable stock.
- FindChips: `https://www.findchips.com/search/<MPN>`.

## Manufacturer lifecycle pages

Most manufacturers show the status on the product page, for example "Mass production", "Early sampling", "Preview", "NRND", "Obsolete". Many also publish an EOL or "products not for new design" list. Search the maker's site for `<MPN> PCN` and `<family> end of life`.

## When pages block automated fetches

Search engines often show CAPTCHAs or unrelated results to agents, and maker and distributor sites return 403, 404 or time out. Try these in order:

1. **Fetch the known URL directly.** Use the distributor search URLs above, the maker's product URL (`<maker>.com/products/<part>`), or the datasheet PDF URL.
2. **Use a reader proxy for pages that are heavy on JavaScript or blocked:** `https://r.jina.ai/<full-url>` returns the page as text. It often works for maker pages, distributor pages and Octopart.
3. **Use a datasheet mirror.** Distributors host datasheet PDFs (DigiKey `mm.digikey.com/...`, Mouser `mouser.com/datasheet/...`). They work when the maker's site blocks you. Check the revision and date on the PDF.
4. **Use a Wayback snapshot:** `https://web.archive.org/web/<YYYY>/<url>`. Record the snapshot date. Do not use it for current stock or price.
5. **Use GitHub.** Many makers publish SDKs, board files, KiCad libraries and errata. Third-party symbols are fine for drawing, never as proof.

Record every failure in the dossier's Sources section, for example "mouser.com: timeout, 2026-01-15". The gap then stays visible.

## Trust

- Recommend only established manufacturers and authorized distributors.
- A part available only through brokers cannot be ordered. Say so.
- A price from memory is not a price. With no live source, write `[estimate: <basis>]` and add an RFQ.
