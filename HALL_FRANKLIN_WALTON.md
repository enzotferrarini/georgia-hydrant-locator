# Hall, Franklin and Walton source review

Checked October 23, 2026. No complete county inventory or active-equipment guarantee is claimed.

## Hall — partial verified government coverage

The [Hall County GIS directory](https://www.hallcounty.org/652/County-Service-Maps) links Experience Builder app `07c9cfa0f6a94be0b7a24ad4e0b084fa`. Its public configuration references `https://hallgis.hallcounty.org/arcgis/rest/services/UtilityTab/MapServer` and its constituent hydrant layers /1 Flowery Branch, /2 Gainesville, /3 Lula. Only these point layers are integrated; duplicate PublicSafety copies and group layers are excluded.

Anonymous IDs, selected batches, WGS84 conversion and spatial retrieval passed. Gainesville has 13,194 raw records, with 12,191 matching the active/enabled/operable flags all set to 1. Flowery Branch has 155 and Lula 158. Feature edits are not a comprehensive field-survey date; Gainesville exposes LASTUPDATE, Flowery Branch last_edited_date, and Lula has no update field. Status rules are included in both server queries and client-side checks, and a missing required field fails closed.

## Franklin — Carnesville only

The public `CarnesvilleWebMapWater_WFL1/FeatureServer/3` Water Structures layer belongs to the Georgia Association of Regional Commissions organization. Owner `bcarlock_garc` corresponds to Brandon Carlock, GIS Analyst on the [GMRC staff page](https://www.gmrc.ga.gov/staffdirectory). App `288283c0c491407587f48c974b2de798` credits GPS collection and maps to Georgia Mountains Regional Commission in 2026. Its public app configuration references the Carnesville maps.

The integration restricts `Type` to `Hydrant`: 88 records. Hydrant Valve, Water Valve, meters, wells and other structures are excluded. Dataset edit July 6, 2026 is not an asset inspection guarantee. Franklin county-water, Lavonia, Royston and other separate utility systems are not represented as complete coverage.

## Walton — explicit historical exception, not verified government data

[Map 7234164215134678b48a5dd117ef884f](https://www.arcgis.com/home/item.html?id=7234164215134678b48a5dd117ef884f) contains a June 2022 embedded point collection, last modified June 2, 2022. It claims WCFR jurisdiction and WCWSA/MUN/SCWD input sources. Its owner `cleague1402` has no public identifying name or government-organization membership. The county's staff page lists Craig League, but that similarity alone does not authenticate this account.

The requested source is therefore exposed only as an optional historical-map toggle, off by default. Both the source and county register identify this uncertainty. The coordinates-only copy contains 3,776 unique source IDs and 3,775 distinct coordinate pairs. Exact coincident records with different IDs are retained; counts are not asserted to be distinct assets. Downloading the map does not update its 2022 field currency. The checksum, expected source URL and original date are validated before querying. Corruption or provenance mismatch fails closed. A result including this map is always partial; neither retrieval success nor an empty historical radius proves current coverage or absence of hydrants.

## Checks

`data/hall_franklin_walton_validation.json` records production-query known-point tests: zero-distance recovery for all four new live layers and the saved historical collection. Automated tests cover compound numeric status rules, missing/incorrect status values, hydrant-versus-valve classification, historical coordinate distances/radius, corrupt/duplicate/invalid records, provenance mismatch, default exclusion, and UI result invalidation when the source selection changes. No private addresses are included in this evidence.
