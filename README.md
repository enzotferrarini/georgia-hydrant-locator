# Georgia Fire Hydrant Locator

A local Python + Streamlit app that locates a Georgia street address and calculates the nearest mapped hydrant in **ten verified public government ArcGIS layers**, within a selectable 1, 2, 5 or 10 mile radius. Includes an interactive map, source health, UTC timestamps, downloadable results, and an explicit register of all 159 counties.

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

Open the local URL printed in the terminal (normally http://localhost:8501). No API key is needed. Internet access is required. Stop the app with Ctrl+C. The included `start.ps1` automates Windows setup and launch. Do not change your PowerShell execution policy just to run it; the commands above also work directly.

1. Enter a complete Georgia street address and choose **Locate address**.
2. Verify the normalized address, county and blue map pin. If multiple matches appear, choose the correct one. A single match is not a guarantee that the intended building was identified.
3. Choose a radius and **Search near this address**.
4. Review the orange hydrant, distance, GIS record, source timestamps and any source failures. Download the JSON to keep the calculation's provenance.

## What the number means

**Map straight-line distance, not underwriting-approved hydrant distance.** Distance is measured from the Census geocoded street position to the published hydrant geometry. Census interpolates along an address range; it does not establish the building, driveway or entrance position. Geocoder error may materially change short distances. The result is not a hose-route, road, parcel-edge, three-dimensional or fire-response distance. Verify the origin, route, equipment condition and required measurement with the appropriate authority and insurer.

**No result never establishes that no hydrant exists.** Public layers can omit municipal, private, recently installed or otherwise unpublished hydrants. The app reports mapped records regardless of operational status and exposes the source's raw attributes; a mapped point is not proof of active equipment or access. No statewide completeness is claimed.

## Verified coverage

Verified on 2026-10-15–16 using anonymous metadata, full record-ID queries and sample geometry queries:

| Source | County register | Published records observed | Scope |
|---|---|---:|---|
| [Barrow County utility hydrants](https://services5.arcgis.com/OVFGXfRTCVcPwl55/ArcGIS/rest/services/BCGIS_Utility_Layers/FeatureServer/17) | Barrow | 1,639 | Public utility mapping; completeness not certified |
| [Cherokee County Hydrants2026](https://gis.cherokeecountyga.gov/arcgis/rest/services/Hydrants2026/FeatureServer/0) | Cherokee | 12,073 | Published county layer; completeness not certified |
| [Glynn County Fire Hydrants](https://gis-web.glynncounty-ga.gov/gis-server/rest/services/Fire_Hydrants/FeatureServer/0) | Glynn | 5,126 | Published county layer; completeness not certified |
| [City of Roswell Fire Hydrants](https://gisweb.ci.roswell.ga.us/arcgis/rest/services/PublicViewer/FirePublic/MapServer/1) | Fulton | 5,175 | Roswell only; other Fulton jurisdictions not integrated |
| [Gwinnett County Water Hydrant](https://dwrarcgis.gwinnettcounty.com/server/rest/services/Hosted/Water_Hydrant/FeatureServer/0) | Gwinnett | 46,889 | DWR utility mapping; completeness not certified |
| [Athens–Clarke Public Utilities Hydrants](https://enigma.accgov.com/server/rest/services/Public_Utilities/MapServer/2) | Clarke | 6,251 | Government utility layer; approximate positions |
| [MGRC Monroe County Fire Hydrants](https://services1.arcgis.com/Ug5xGQbHsD8zuZzM/arcgis/rest/services/Fire_Hydrants/FeatureServer/12) | Monroe | 1,307 | Regional commission publication; approximate positions, unverified field currency |
| [Jackson County — Hydrants](https://services8.arcgis.com/bcbi4lYRFOsss0F5/arcgis/rest/services/hydrants/FeatureServer/1) | Jackson | 8,062 | Partial public inventory; see source cautions |
| [Oconee County — Public Water Hydrants](https://utility.arcgis.com/usrsvcs/servers/e59a525183fe4767887ea33941b7e1f7/rest/services/Services_Public/Water_Resources_Water_Data_Public/FeatureServer/1) | Oconee | 2,882 | Partial public inventory; see source cautions |
| [DeKalb County — Hydrants All](https://dcgis.dekalbcountyga.gov/mapping/rest/services/Hydrants/MapServer/2) | Dekalb | 27,230 | Partial public inventory; see source cautions |

Ten counties are `supported_partial`; Walton is `researched_unverified`. The other **148 counties are `not_researched`**, not asserted to lack a public source. See `data/coverage.json`. Names and five-digit FIPS codes come from the [US Census TIGERweb county layer](https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1), queried with `STATE='13'`; the returned 159-row inventory is preserved in `data/counties.json`.

Barrow ownership was established through the [county GIS page](https://www.barrowga.org/526/GIS), its linked Experience Builder app, the app's referenced web map, and that map's actual hydrant layer URL. That full chain is in `data/sources.json`. Hosted ArcGIS sources include Barrow, Jackson, Oconee and MGRC; their government publisher evidence is recorded in the source registry. Other services use government GIS domains. Layer metadata snapshots are included for review, not used as live hydrant data.

## Added Gwinnett, Monroe and Clarke coverage

All three additions passed anonymous full-ID queries, WGS84 feature retrieval and one-mile spatial queries centered on a published feature. Each returned the feature at zero distance. Evidence is in `data/source_validation.json`; per-layer metadata and verification timestamps are preserved alongside it.

Athens–Clarke uses the working `enigma.accgov.com` Public Utilities service, rather than the unresponsive older `athensclarkecounty.com` hostname or a separate hosted copy. The [official utility map page](https://accgov.com/7342/Water-Maps-GIS) says utility positions are approximate.

Monroe uses a [public hosted layer](https://www.arcgis.com/home/item.html?id=9a13c7491b124c988573206dc61af984) published in October 2025 by `nwilliams_MGRC` (Nicole Williams), a GIS analyst listed on the [official MGRC staff page](https://www.middlegeorgiarc.org/about-us/staff/). Publisher evidence is in `data/monroe_publisher_evidence.json`. The older EMS map references an unresponsive `mgrcmaps.org` service and is not used. Publication/edit dates do not establish field-survey currency. Sample geometry corresponds to coordinates rounded to 0.001 degrees, so distances may have substantial position uncertainty; a Monroe result displays an additional accuracy caution. The dataset extent includes points outside Monroe County, which are not silently clipped or represented as necessarily within the county.

## McCarty Road validation

The live check on 2026-10-16, across all ten sources, returned:

- Matched address: **558 MCCARTY RD, STATHAM, GA, 30666**, Barrow County.
- Census origin: latitude **33.956920962905**, longitude **-83.617097912197**.
- Closest mapped point among the configured sources within 5 miles: Barrow record **628**, FacilityID **wh00628**.
- Hydrant geometry: latitude **33.95123601732712**, longitude **-83.62331950596656**.
- Calculated distance: **2,800.006 feet**, displayed as **2,800 ft**.
- Barrow layer's publisher data edit timestamp: **2026-09-30 13:46:22.811 UTC**. This is a GIS edit timestamp, not a field inspection date.

`data/example_result.json` preserves the live result and source responses' provenance. It is a dated example, never a fallback for new searches. Some providers do not expose a layer-wide data edit date through their metadata responses; the UI explicitly identifies missing dates. Record-level update timestamps are included where available.

## Calculation and completeness

- Census `geographies/onelineaddress` uses `Public_AR_Current` and `Current_Current`. Both the matched state and county FIPS must identify Georgia. No city/ZIP centroid fallback is used. Returned benchmark/vintage and retrieval time are recorded.
- Every integrated source is searched, regardless of the origin county, so a county boundary cannot exclude a closer point in an integrated neighboring source.
- A conservative geographic envelope contains the entire radius for Georgia. The app asks for all IDs inside it, retrieves bounded batches of at most 200, and compares every returned ID set. It rejects transfer-limit flags, missing records, invalid geometry and unexpected coordinate systems. ArcGIS's null empty-ID response is accepted only after a separate count query confirms zero.
- ArcGIS projects geometry to WGS84 (`outSR=4326`). `pyproj.Geod(ellps='WGS84')` computes the shortest ellipsoidal surface distance. Metres are converted using exactly **0.3048 metres per international foot**. The app does not treat Web Mercator coordinates as ground distances or use potentially stale latitude/longitude attribute columns.
- Points outside the exact radius are discarded and all remaining candidates are ranked. Up to 20 are retained in the JSON, with up to 10 shown on the map. Complete means all **configured queries** succeeded, not that the underlying inventory is complete.
- A failed or incomplete source makes the overall result `partial`. A successful source may still provide a candidate, explicitly labeled as unverified across the complete configured source set. Empty and unavailable results are kept distinct.
- Read requests have timeouts and bounded retries for temporary HTTP/network failures. GIS records can change during queries; missing IDs fail closed. New records inserted after the initial ID query are not detectable without a transactional snapshot. No persistent hydrant cache is used.

## Tests and live checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe verify_live.py
```

The offline suite covers distance correctness, coordinate validation, full-radius envelopes, all 159 unique county codes, Georgia geocoding checks, batch completeness, missing geometry, wrong projections, empty responses, partial source failures and Streamlit interaction flows. The live check explicitly contacts the government services and updates `data/example_result.json`; it exits unsuccessfully if the configured search is partial or returns no candidate.

## Add a source

1. Verify a government page or government-domain service establishes ownership. An ArcGIS title alone is insufficient.
2. Confirm anonymous point-layer metadata and queries, actual Georgia geometry and the coverage scope. Do not bypass access controls or integrate private layers.
3. Add its URL, scope, government evidence URL, county FIPS, verification time and optional record update field to `data/sources.json`. Preserve municipal scope; never promote a city layer to complete county coverage.
4. Update the matching county entries in `data/coverage.json`, add fixtures/tests, and run a live spatial query near a known mapped feature.
5. Update these documentation counts when sources change. The UI coverage summary is generated from the registry.

## Privacy and operation

Addresses are transmitted to the US Census Geocoder; search envelopes go to the configured GIS providers. OpenStreetMap receives tile requests when the map is displayed. The app holds results in the current Streamlit session and writes no user address log. Downloaded JSON includes the address and coordinates. Government providers may keep their own request logs. Streamlit usage telemetry is disabled in the included configuration. Keep the server local unless you deliberately configure access controls for a deployment.

Sources remain owned by their publishers. Public query access does not establish a redistribution license; check publisher terms before bulk redistribution or commercial deployment.

Technical references: [Census Geocoding API](https://geocoding.geo.census.gov/geocoder/Geocoding_Services_API.html), [Esri query API](https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer/).

## Shared website deployment

This folder is the portable cloud version. It excludes the Windows background launcher and local runtime logs.

1. Upload the contents of this folder to a private GitHub repository.
2. Sign into Streamlit Community Cloud and authorize access to that repository.
3. Create an app using branch `main` and entrypoint `app.py`.
4. Select Python 3.14 in Advanced settings. No secrets or API keys are required.
5. Keep sharing restricted to specific people, and add your coworker as a viewer.
6. Test a real address on the deployed website before sharing the final URL.

Hosting is not yet verified until the deployed app has passed its live check. Free Community Cloud apps can sleep after inactivity; viewers can wake them from the website. Government GIS availability remains outside this app's control.

Versions are pinned to the locally tested environment. All 25 offline tests passed locally before cloud deployment; Linux cloud installation still needs verification.
