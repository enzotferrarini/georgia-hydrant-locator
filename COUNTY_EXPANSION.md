# Cobb, Forsyth and Fulton source review — 2026-10-20

## Integrated sources

| Addition | Full published IDs | Eligible search IDs | Treatment |
|---|---:|---:|---|
| [North Fulton county-water hydrants](https://gismaps.fultoncountyga.gov/arcgispub/rest/services/WaterResources/WR_Public_Map_Viewer/MapServer/9) | 14,211 | 14,208 | Excludes three explicit Abandoned records. Also excludes Does Not Exist and Model codes if encountered later. Other/unknown statuses are not certified operational. |
| [Atlanta water-system hydrants](https://egis.atlantaga.gov/ags/rest/services/OpMap/assets/MapServer/0) | 24,687 | 23,682 | Only SERVSTAT=INSRV. Excludes 805 Out of Service, 199 null and one other-coded record. |
| [Forsyth public water hydrants](https://geo.forsythco.com/gis2/rest/services/Public/Water_Hydrants_Public/FeatureServer/0) | 13,711 | 13,302 | Only LIFECYCLESTATUS=Active (Existing). Excludes 80 Removed, 12 Construction, 293 Inactive, 22 Other and two Abandoned In Place records. |
| [Smyrna municipal fire hydrants](https://services2.arcgis.com/hE9igMm8RoNeQRbh/arcgis/rest/services/Water_Database/FeatureServer/1) | 2,723 | 2,723 | Published municipal mapping; no operational status is inferred from undocumented/free-text fields. |

All four passed anonymous full eligible-ID queries, WGS84 feature retrieval and one-mile spatial recovery of a published point at zero feet. Exact timestamps and observed counts are in `data/county_expansion_validation.json`; metadata snapshots are included. These are source-record counts, not a guaranteed unique physical-asset total or certified comprehensive inventory.

## Authority and scope

Fulton's [official Public Works page](https://www.fultoncountyga.gov/publicworks) links its public water/sewer mapping. The [county service description](https://www.fultoncountyga.gov/services/water-services/start-your-water-service) says it serves North Fulton and does not directly provide water service to Atlanta. The selected public viewer /9 and WaterResourcesSewer /15 returned identical full ID lists and extents; only /9 is integrated to avoid adding the same county dataset twice. Roswell remains a separate source.

Atlanta's current government-hosted OpMap/assets service exposes a Water Hydrant point layer. The older indexed MapWF/WaterDistributionTst endpoint returned service-not-found and was rejected. Atlanta water-system coverage extends outside city limits, but does not imply that every municipal/private system is included. [Sandy Springs](https://www.sandyspringsga.gov/fire-hydrant-inspections/) identifies Atlanta Watershed Management as owner of its public hydrants. All configured layers are searched across county boundaries.

Forsyth's government GIS domain attributes the public point layer to the GIS and Water Departments. Its lifecycle domain explicitly distinguishes Existing, removed, inactive and construction records. Neither an Existing label nor Atlanta's In Service label substitutes for a current inspection.

Smyrna ownership was verified through the [official mayor's city article](https://www.smyrnaga.gov/Home/Components/News/News/2007/149?arch=1&npage=3), which links a staff-created SMYGIS app. ArcGIS item `33d02249b29c48c7b2db0242b7aa3465` identifies its owner as `Smyrna_GA`; that same account owns public Water Database item `76a9393d49fd4eae920eb1c759e5366f`. The linked service's hydrant geometry is in Smyrna, Georgia. The full chain is retained in `data/sources.json`.

## Remaining gaps and rejected candidates

- **Cobb is Smyrna-only in this app.** The [official Cobb GIS page](https://www.cobbcounty.gov/information-technology-services/cobb-county-gis) links its GIS Hub. The county Fire folder returned token-required (499); no access controls were bypassed. Public water/open-data folders contained reference, project, service-line and civic data but no verified county hydrant inventory. Portal hydrant search hits were Esri templates, not Cobb asset records. Marietta public-indexed water endpoints returned HTTP 403 and were not integrated. Cobb Water Engineering & Records lists GIS Mapping & As-Builts as a responsibility on the [official leadership page](https://www.cobbcounty.gov/water/our-story/leadership-team); seek a public/authorized export there for countywide expansion.
- **Fulton remains partial.** The [Fairburn official GIS link](https://www.fairburn.com/QuickLinks.aspx?CID=15) led to a city organization whose public water-outage map exposed city limits and outage reports, not hydrant locations. Union City's public viewer exposed addressing, civic/planning and environmental layers rather than a hydrant inventory. Separate municipal/private inventories, including systems around Fairburn, Union City, East Point, College Park, Hapeville and Palmetto, have not been certified complete by this review. Obtain a current authorized utility export before asserting their coverage.
- Hosted `Hydrants_Public` service under organization `Yx1h0qHJ9wIpQWuU` was outside Georgia and rejected. `maps.cob.org` search results refer to a different jurisdiction, not Cobb County. Similar names alone are insufficient evidence.
- Statham/Barrow municipal gaps and Walton's unverified status remain as previously documented; these additions do not fill those gaps.

## Before and after

Before: 10 partially supported counties, 10 sources, Fulton represented by Roswell only, no integrated Cobb/Forsyth sources.

After: 12 partially supported counties, 14 sources. Fulton adds North Fulton county-water and Atlanta water-system records; Forsyth adds the public Existing inventory; Cobb adds Smyrna municipal records. No county is promoted to complete coverage. Source failures remain partial results and no mapped result never proves no actual hydrant exists.

Dense-area radius reduction preserves the nearest-point conclusion only when a candidate is inside the smaller verified circle; otherwise the source fails closed. Omitted outer records are disclosed and are not counted as displayed inventory. The Gwinnett dated backup is unchanged.
