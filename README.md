# Georgia Fire Hydrant Locator

A public Python + Streamlit app that locates a Georgia street address and calculates the nearest mapped hydrant in **fourteen verified public government ArcGIS layers across twelve partially supported counties**, within a selectable 1, 2, 5 or 10 mile radius. Includes an interactive map, source health, UTC timestamps, downloadable results, and an explicit register of all 159 counties.

## Start

Install Python 3.11 or newer (tested with Python 3.12 and 3.14). From this project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

On macOS/Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Open the local URL printed in the terminal (normally http://localhost:8501). No API key is needed. Internet access is required. Stop the app with Ctrl+C. The cloud deployment runs independently of your computer or terminal.

1. Enter a complete Georgia street address and choose **Locate address**.
2. Verify the normalized address, county and blue map pin. If multiple matches appear, choose the correct one. A single match is not a guarantee that the intended building was identified.
3. Choose a radius and **Search near this address**.
4. Review the red hydrant, distance, GIS record, source timestamps and any source failures. Download the JSON to keep the calculation's provenance.

## What the number means

**Map straight-line distance, not underwriting-approved hydrant distance.** Distance is measured from the selected property point to the published hydrant geometry. Exact-match Barrow County address points are offered before the Census fallback, with their STRUCTURE, PARCEL, SITE or other published placement label. None is certified as a surveyed rooftop. You can enable **Adjust property point on the map**, click the building or starting point, apply the correction, then search again. Corrections are checked to be in Georgia and within two miles of the original match; the old distance is cleared. Census interpolates along an address range; it does not establish the building, driveway or entrance position. Geocoder error may materially change short distances. The result is not a hose-route, road, parcel-edge, three-dimensional or fire-response distance. Verify the origin, route, equipment condition and required measurement with the appropriate authority and insurer.

**No result never establishes that no hydrant exists.** Public layers can omit municipal, private, recently installed or otherwise unpublished hydrants. Some sources contain records with unknown or inactive status. The new Atlanta and Forsyth sources apply explicit published-status filters, and North Fulton excludes explicit abandoned/nonexistent/model records. The app returns only selected provenance fields; a mapped point is not proof of active equipment or access. No statewide completeness is claimed.

## Verified coverage

Source counts were observed on 2026-10-15â€“20 using anonymous metadata, complete record-ID queries and sample geometry/spatial queries. See per-source validation timestamps:

| Source | County register | Published records observed | Scope |
|---|---|---:|---|
| [Barrow County utility hydrants](https://services5.arcgis.com/OVFGXfRTCVcPwl55/ArcGIS/rest/services/BCGIS_Utility_Layers/FeatureServer/17) | Barrow | 1,639 | Primarily county-owned utility hydrants; municipal completeness not certified |
| [Cherokee County Hydrants2026](https://gis.cherokeecountyga.gov/arcgis/rest/services/Hydrants2026/FeatureServer/0) | Cherokee | 12,086 | Published county layer; completeness not certified |
| [Glynn County Fire Hydrants](https://gis-web.glynncounty-ga.gov/gis-server/rest/services/Fire_Hydrants/FeatureServer/0) | Glynn | 5,126 | Published county layer; completeness not certified |
| [City of Roswell Fire Hydrants](https://gisweb.ci.roswell.ga.us/arcgis/rest/services/PublicViewer/FirePublic/MapServer/1) | Fulton | 5,175 | Roswell municipal inventory; complements the North Fulton and Atlanta sources below |
| [Gwinnett County Water Hydrant](https://dwrarcgis.gwinnettcounty.com/server/rest/services/Hosted/Water_Hydrant/FeatureServer/0) | Gwinnett | 46,889 | DWR utility mapping; completeness not certified |
| [Athensâ€“Clarke Public Utilities Hydrants](https://enigma.accgov.com/server/rest/services/Public_Utilities/MapServer/2) | Clarke | 6,251 | Government utility layer; approximate positions |
| [MGRC Monroe County Fire Hydrants](https://services1.arcgis.com/Ug5xGQbHsD8zuZzM/arcgis/rest/services/Fire_Hydrants/FeatureServer/12) | Monroe | 1,307 | Regional commission publication; approximate positions, unverified field currency |
| [Jackson County â€” Hydrants](https://services8.arcgis.com/bcbi4lYRFOsss0F5/arcgis/rest/services/hydrants/FeatureServer/1) | Jackson | 8,062 | Partial public inventory; see source cautions |
| [Oconee County â€” Public Water Hydrants](https://utility.arcgis.com/usrsvcs/servers/e59a525183fe4767887ea33941b7e1f7/rest/services/Services_Public/Water_Resources_Water_Data_Public/FeatureServer/1) | Oconee | 2,882 | Partial public inventory; see source cautions |
| [DeKalb County â€” Hydrants All](https://dcgis.dekalbcountyga.gov/mapping/rest/services/Hydrants/MapServer/2) | Dekalb | 27,261 | Partial public inventory; see source cautions |

| [Fulton County â€” North Fulton Water Hydrants](https://gismaps.fultoncountyga.gov/arcgispub/rest/services/WaterResources/WR_Public_Map_Viewer/MapServer/9) | Fulton | 14,211 published; 14,208 eligible | North Fulton county water-system inventory; complements Roswell and Atlanta. Not complete Fulton County coverage. |
| [City of Atlanta â€” In-service Water Hydrants](https://egis.atlantaga.gov/ags/rest/services/OpMap/assets/MapServer/0) | Fulton | 24,687 published; 23,682 eligible | Atlanta water-system published hydrants labeled IN SERVICE, including portions outside city limits; partial inventory. |
| [Forsyth County â€” Existing Water Hydrants](https://geo.forsythco.com/gis2/rest/services/Public/Water_Hydrants_Public/FeatureServer/0) | Forsyth | 13,711 published; 13,302 eligible | Official public water hydrants labeled Existing (Active); partial inventory, not certified countywide completeness. |
| [City of Smyrna â€” Fire Hydrants](https://services2.arcgis.com/hE9igMm8RoNeQRbh/arcgis/rest/services/Water_Database/FeatureServer/1) | Cobb (Smyrna only) | 2,723 published; 2,723 eligible | Smyrna municipal water mapping only; partial Cobb coverage. Countywide and other municipal inventories are not integrated. |

Twelve counties are `supported_partial`; Walton is `researched_unverified`. The other **146 counties are `not_researched`**, not asserted to lack a public source. See `data/coverage.json`. Names and five-digit FIPS codes come from the [US Census TIGERweb county layer](https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1), queried with `STATE='13'`; the returned 159-row inventory is preserved in `data/counties.json`.

Barrow ownership was established through the [county GIS page](https://www.barrowga.org/526/GIS), its linked Experience Builder app, the app's referenced web map, and that map's actual hydrant layer URL. That full chain is in `data/sources.json`. Hosted ArcGIS sources include Barrow, Jackson, Oconee and MGRC; their government publisher evidence is recorded in the source registry. Other services use government GIS domains. Layer metadata snapshots are included for review, not used as live hydrant data.

## Added Gwinnett, Monroe and Clarke coverage

All three additions passed anonymous full-ID queries, WGS84 feature retrieval and one-mile spatial queries centered on a published feature. Each returned the feature at zero distance. Evidence is in `data/source_validation.json`; per-layer metadata and verification timestamps are preserved alongside it.

Athensâ€“Clarke uses the working `enigma.accgov.com` Public Utilities service, rather than the unresponsive older `athensclarkecounty.com` hostname or a separate hosted copy. The [official utility map page](https://accgov.com/7342/Water-Maps-GIS) says utility positions are approximate.

Monroe uses a [public hosted layer](https://www.arcgis.com/home/item.html?id=9a13c7491b124c988573206dc61af984) published in October 2025 by `nwilliams_MGRC` (Nicole Williams), a GIS analyst listed on the [official MGRC staff page](https://www.middlegeorgiarc.org/about-us/staff/). Publisher evidence is in `data/monroe_publisher_evidence.json`. The older EMS map references an unresponsive `mgrcmaps.org` service and is not used. Publication/edit dates do not establish field-survey currency. Sample geometry corresponds to coordinates rounded to 0.001 degrees, so distances may have substantial position uncertainty; a Monroe result displays an additional accuracy caution. The dataset extent includes points outside Monroe County, which are not silently clipped or represented as necessarily within the county.

## Calculation and completeness

- Census `geographies/onelineaddress` uses `Public_AR_Current` and `Current_Current`. Both the matched state and county FIPS must identify Georgia. No city/ZIP centroid fallback is used. Returned benchmark/vintage and retrieval time are recorded.
- Every integrated source is searched, regardless of the origin county, so a county boundary cannot exclude a closer point in an integrated neighboring source.
- A conservative geographic envelope contains the entire radius for Georgia. The app asks for all IDs inside it, retrieves bounded batches of at most 200, and compares every returned ID set. It rejects transfer-limit flags, missing records, invalid geometry and unexpected coordinate systems. ArcGIS's null empty-ID response is accepted only after a separate count query confirms zero.
- ArcGIS projects geometry to WGS84 (`outSR=4326`). `pyproj.Geod(ellps='WGS84')` computes the shortest ellipsoidal surface distance. Metres are converted using exactly **0.3048 metres per international foot**. The app does not treat Web Mercator coordinates as ground distances or use potentially stale latitude/longitude attribute columns.
- Points outside the exact radius are discarded and all remaining candidates are ranked. Up to 250 nearest candidates are retained in JSON and shown using marker clusters; the retrieved matching count is displayed. The nearest calculation uses all retrieved candidates before this display cap. Duplicate records merge only when an identical point shares a source record ID or explicitly configured authoritative asset identity; nearby or coincident points alone are not merged. Complete means all **configured queries** succeeded, not that the underlying inventory is complete.
- A failed or incomplete source makes the overall result `partial`. A successful source may still provide a candidate, explicitly labeled as unverified across the complete configured source set. Empty and unavailable results are kept distinct.
- Read requests have timeouts and bounded retries for temporary HTTP/network failures. GIS records can change during queries; missing IDs fail closed. New records inserted after the initial ID query are not detectable without a transactional snapshot. A dated, validated public Gwinnett snapshot is available as an outage fallback; other layers use live queries.

## Tests and live checks

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe verify_live.py
```

The offline suite covers distance correctness, coordinate validation, full-radius envelopes, all 159 unique county codes, Georgia geocoding checks, batch completeness, missing geometry, wrong projections, empty responses, partial source failures and Streamlit interaction flows. The live check contacts government services using a published hydrant as its origin, verifies zero-distance recovery, prints only source counts/status and timestamps, and writes no files or addresses. Use `--source barrow` to check one layer. Example fixtures are synthetic and must never be submitted to live geocoders.

## Add a source

1. Verify a government page or government-domain service establishes ownership. An ArcGIS title alone is insufficient.
2. Confirm anonymous point-layer metadata and queries, actual Georgia geometry and the coverage scope. Do not bypass access controls or integrate private layers.
3. Add its URL, scope, government evidence URL, county FIPS, verification time and optional record update field to `data/sources.json`. Preserve municipal scope; never promote a city layer to complete county coverage.
4. Update the matching county entries in `data/coverage.json`, add fixtures/tests, and run a live spatial query near a known mapped feature.
5. Update these documentation counts when sources change. The UI coverage summary is generated from the registry.

## Privacy and operation

Addresses are transmitted to the US Census Geocoder; Barrow house numbers are also queried against the county address layer; search envelopes go to the configured GIS providers. OpenStreetMap receives tile requests when the map is displayed. The app holds results in the current Streamlit session and writes no user address log. Downloaded JSON includes the address and coordinates. Government providers may keep their own request logs. Streamlit usage telemetry is disabled in the included configuration. The deployed site is public. Do not enter confidential customer data unless your organization permits sharing it with these providers. The app does not add request-address logs or persistent address caches; provider/hosting logs are outside its control.

Sources remain owned by their publishers. Public query access does not establish a redistribution license; check publisher terms before bulk redistribution or commercial deployment.

Technical references: [Census Geocoding API](https://geocoding.geo.census.gov/geocoder/Geocoding_Services_API.html), [Esri query API](https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer/).

## Shared website deployment

The public app is https://georgia-hydrant-locator.streamlit.app/ and the public repository is https://github.com/enzotferrarini/georgia-hydrant-locator.

Streamlit Community Cloud should deploy branch `main`, entrypoint `app.py`, Python 3.14, using `requirements.txt`. No secrets or paid API keys are required. Commit reviewed changes to main to trigger redeployment. Share the website URL with coworkers; their computers do not need Python and your terminal does not need to remain open. Free hosting may sleep after inactivity and government services can be unavailable.

Install `requirements-dev.txt` for pytest. Tests use synthetic fixtures and mocked services; `verify_live.py` is the separate opt-in network check. Production packages are pinned. Deployment verification must check the actual running UI after each release; local tests alone do not establish a successful cloud deployment.

## October 2026 review

See [Barrow investigation and before/after evidence](BARROW_RESEARCH.md) and [privacy and security review](SECURITY_REVIEW.md). Barrow remains **1,639 published records before and after**: no additional authoritative public hydrant layer was verified. The new county address-point integration improves the choice of starting point, not hydrant inventory completeness. Map display increased from 10 to 250 records without changing the ranking-before-display rule.

Requests are limited to 10-mile radii, 10,000 records per source, 200-record batches, 8 MB responses, 15-second network timeouts and bounded retries. A 60-second batch deadline is checked between requests (not a hard wall-clock deadline). There are two simultaneous searches and eight simultaneous HTTP requests per process, plus separate five-second session cooldowns for repeated address lookups, hydrant searches and map corrections. Moving from address lookup to hydrant search does not require waiting. Blocked repeat clicks preserve the current match and result. These are resource safeguards, not a distributed abuse-prevention system.

## Gwinnett outage backup

The app first queries the official live Gwinnett layer. On a live-query failure it can search the packaged public snapshot in `data/snapshots/`, using the same WGS84 distance method. The initial 2026-10-20 download contains **46,889** published records. Only record ID, geometry and feature update date are stored; no submitted addresses or administrative attributes are included. The JSON result and source-status panel disclose the backup download date, age and live-service error. Any backup use keeps the overall result **partial**, including an empty snapshot search. It does not prove absence of hydrants. Backups older than 90 days or with invalid checksums, provenance, geometry, IDs or counts are rejected.

`python refresh_snapshot.py` downloads all published IDs and bounded feature batches, verifies exact ID agreement, rechecks the full ID list and publisher edit metadata, then replaces the backup. A failed download leaves the last committed copy intact. The included **Refresh Gwinnett backup** GitHub workflow runs weekly on Mondays at 09:17 UTC or manually from Actions. Its updates are committed only after the tests pass. Scheduled runs depend on GitHub Actions being enabled and may be delayed or disabled by GitHub; inspect the visible backup date. A failed refresh cannot create fresh data during a county outage.

The published layer supports anonymous Query access. Its portal item supplied no explicit license text on 2026-10-20. Retain county provenance and verify publisher terms for redistribution/commercial use. Public mapping is approximate and may omit private, new or otherwise unpublished equipment. A saved hydrant inventory removes that county-server dependency for the distance calculation, but address geocoding, map tiles and website hosting still need their own services. This does not make the entire app fully offline or guarantee continuous availability.

## Cobb, Forsyth and expanded Fulton coverage â€” 2026-10-20

See [investigation, source decisions and limitations](COUNTY_EXPANSION.md). Four new sources bring the app to 14 sources in 12 partially supported counties. Fulton now combines Roswell, county-water mapping in North Fulton and Atlanta water-system mapping. Cobb currently has Smyrna municipal coverage only; it is not a countywide inventory. No county has been certified complete.

The new source status filters are applied to ID queries and rechecked on returned records. Missing status fields or a service ignoring the filter fail closed. Forsyth searches only Existing/Active records; Atlanta only In Service records; North Fulton excludes explicit Abandoned, Does Not Exist and Model statuses. Unknown records excluded by a source filter may still represent real equipment. Publisher labels do not certify operation or access.

Dense new-source inventories may exceed 10,000 live records within the selected maximum radius. For those sources the query can halve its radius, at most five times. It reports success only if the smaller exact circle contains a candidate: every omitted outer point is necessarily farther away, so the nearest result remains valid. An empty inner circle never establishes absence in the outer area and fails closed. Reports disclose the smaller searched radius, and map counts describe retrieved records rather than all records within the maximum radius. Existing source behavior and the Gwinnett backup remain intact.

After code changes to imported Python modules, use Community Cloud's Manage app > Reboot app to load the new module versions; a browser refresh alone may retain old imports when file watching is disabled. A reboot briefly disconnects active viewers.
