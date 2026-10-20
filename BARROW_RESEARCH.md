# Barrow coverage investigation — 2026-10-16

## Finding

The integrated county layer is principally a county-owned utility inventory, not an exhaustive countywide fire-protection inventory. No additional hydrant layer met both official-publisher verification and anonymous query requirements during this review. Coverage is unchanged; the app now explains the limitation explicitly.

The [county Water Division](https://www.barrowga.org/327/Water-Division) describes retail service in three distinct unincorporated areas and wholesale supply to municipal/neighboring systems. The [official GIS page](https://www.barrowga.org/526/GIS) links the county viewer and Winder portal. The utility service also publishes water-provider polygons (layer 153), which must not be mistaken for hydrant points.

## Source decisions

| System | Evidence investigated | Decision |
|---|---|---|
| Barrow | [Utility hydrants layer 17](https://services5.arcgis.com/OVFGXfRTCVcPwl55/ArcGIS/rest/services/BCGIS_Utility_Layers/FeatureServer/17), linked from the official county viewer | Retained; 1,639 accessible records. County GIS: gis@barrowga.org; Water Division: 770-307-3014. Ask for municipal gaps and authoritative field currency. |
| Winder | [Official GIS portal](https://gis.cityofwinder.com/portal/home/index.html) and [REST catalog](https://gis.cityofwinder.com/arcgis/rest/services) | Infrastructure, Hosted, HiperWeb, Iworq, Hydrology, RoseHill and test folders returned token-required responses. Administrative/InteractiveMap also required authentication. PublicInfoMap and root iWorQ maps expose other civic layers, not hydrants. No access controls bypassed. Contact city GIS or [Water Department](https://www.cityofwinder.com/government/departments/utilities/water/index.php). |
| Braselton | [Public Works](https://www.braselton.gov/government/departments/public_works/index.php); [candidate wHydrant_2023 layer](https://services3.arcgis.com/KToZF1P7XLzh9uQx/arcgis/rest/services/Braselton_Water_Sewer_Reuse_Map_2024/FeatureServer/3) | Candidate metadata was public, but owner pelamemi could not be tied authoritatively to the town. Not integrated or counted as confirmed coverage. Contact town engineer/Public Works (706-654-3915 ext. 1027) for official publication authorization/link. |
| Statham | [Official Water and Wastewater page](https://www.cityofstatham.com/WaterAndWastewater.aspx) | Separate municipal supply/distribution; no verified anonymous hydrant layer located. Contact 770-725-5455. |
| Auburn | [Official Public Works](https://www.cityofauburn-ga.org/public-works) | Separate distribution system supplied from Barrow/Gwinnett. No verified public hydrant layer located; similarly named out-of-state datasets rejected. Contact 770-963-4002. |
| Bethlehem | County water-provider polygons and searches for municipal GIS; town website did not respond during review | No verified hydrant layer located. Seek the serving system and official dataset from Barrow GIS. This does not establish that no dataset or hydrants exist. |
| Neighboring utilities | Existing Jackson and Gwinnett integrations | Already searched across county boundaries; no additional coverage credited in this update. |

## Full layer audit

All 1,639 IDs were retrieved and all corresponding features fetched in batches of 200 with WGS84 output. Batch IDs agreed with requested IDs; no missing geometry or truncation was observed. There is no layer definition expression. The advertised limit is 2,000 per response; the client does not rely on retrieving all features in one response. Ownership is BARROW for 1,637 records and null for two. All 1,639 have an Active label, which is not an independent field inspection. Publisher last-edit timestamp: 2026-09-30; retrieval timestamp and aggregate evidence are in `data/barrow_audit.json`.

Two surplus records share exact coordinates with other records. They have distinct source identities and are retained: coincidence alone cannot prove duplication. The app applies no ownership or lifecycle filter. It uses returned geometry, not stored latitude/longitude attribute columns. No pagination or coordinate-projection defect explaining municipal gaps was found.

The supplied screenshot shows a northwest cluster, eastern/southeastern clusters and a central Winder/Auburn gap. That pattern is consistent with the county utility inventory and its documented service territories. This is a qualitative comparison, not a georeferenced pixel-level reconciliation or proof that every screenshot point exists in this layer.

## Before and after

| Measure | Before | After |
|---|---|---|
| Barrow published hydrants | 1,639 | 1,639; no unsupported expansion claim |
| Integrated counties | 10 partial / 159 | 10 partial / 159 |
| Property origin | Census street interpolation | Exact-match official Barrow address points when available, Census fallback, or user-corrected point |
| Visible map points | Up to 10 | Up to 250 nearest, clustered; total count disclosed |
| Nearest ranking | All retrieved candidates | All retrieved candidates; conservative identity-based deduplication |
| County source caveat | General partial-data warning | Explicit municipal-system limitation |

The [official county address-point layer 112](https://services5.arcgis.com/OVFGXfRTCVcPwl55/arcgis/rest/services/BCGIS_Base_Layers/FeatureServer/112) supplies placement classifications. Exact normalized street/number matches are accepted only for a Census-confirmed Barrow address, within one mile of that match, with Georgia state and no unit ambiguity. Truncated address responses are rejected. A Winder address locator tested through the official portal required authentication and was not used.

Live comparison at the public historic courthouse, 30 N Broad St, Winder (not a residential fixture): Census and county STRUCTURE points differed by **315.27 ft** on 2026-10-16. The nearest point in the **Barrow layer alone** measured **10,114.64 ft** from Census versus **10,426.01 ft** from the county point. This demonstrates sensitivity to the origin, not a certified accuracy gain or the nearest actual hydrant. Large distances in central Winder are compatible with missing municipal inventory. No residential coordinates are stored in this example.

Live source verification recovered a known Barrow hydrant at **0.000 ft**, checking 112 records in its one-mile envelope (2026-10-16T17:51:59Z). Synthetic regression tests independently verify a 100-foot origin adjustment and recalculation to zero when the adjusted point equals the test hydrant. Neither test certifies real-world positional accuracy.

Map distances remain WGS84 ellipsoidal straight-line distances, not road, hose-lay or underwriting-approved distances. The closest actual hydrant, operating condition, access and required measurement origin must be confirmed with the serving utility and insurer.
