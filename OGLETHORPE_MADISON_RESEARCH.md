# Oglethorpe and Madison source review — 2026-10-23

Review timestamp (UTC): 2026-10-23T16:42:28+00:00. This records the research date, not an asset-update date. No source has been integrated and no local asset freshness has been established.

## Decision

Both counties are `researched_unverified`, with empty source IDs. No official public hydrant point inventory was verified. Counts remain **14 sources in 12 partially supported counties**, within the 159-county register. No county is certified complete. Existing cross-county searches continue; nearby records from Clarke, Jackson or other configured sources do not establish coverage of Oglethorpe or Madison.

## Oglethorpe County — FIPS 13221

- The [official assessor page](https://www.oglethorpecountyga.gov/tax-assessor) links the Georgia GIS Clearinghouse for GIS/WinGAP downloads. Property records and zoning are not hydrant inventories. The [official planning page](https://www.oglethorpecountyga.gov/planning) also links zoning and Fire & Rescue resources.
- The public [county ArcGIS service directory](https://services1.arcgis.com/IX9GvidKl201KteW/arcgis/rest/services?f=pjson) lists county, parcel and zoning services. The [county-named service](https://services1.arcgis.com/IX9GvidKl201KteW/arcgis/rest/services/oglethorpe_county/FeatureServer?f=pjson) returned ArcGIS **499 Token Required**. Its contents were not inspected, and it is not established to contain hydrants. No access control was bypassed.
- The [zoning web map data](https://www.arcgis.com/sharing/rest/content/items/27c083b7686b482babc63e4099a91e0a/data?f=pjson) returned **403 Subscription is disabled**. This failure is not evidence about whether hydrant records exist.
- Public searches found fire-station districts/service-area buffers, parcels, trails and zoning. Fire-station buffers are not hydrant points. Historical planning documents describing dry hydrants do not supply a current coordinate inventory and were not used as search data.
- The Fire & Rescue website linked from the county site, [oglethorpefirerescue.org](https://oglethorpefirerescue.org/), showed a hosting-unavailable placeholder during review.

## Madison County — FIPS 13195

- Reviewed the [county website](https://www.madisoncountyga.us/), [water department](https://www.mcgawaterdepartment.com/) and [Industrial Development and Building Authority](https://mcidba.com/). Public property, water-service/customer information and lead-service-line resources did not establish a hydrant point layer.
- ArcGIS search hits for Madison County, Georgia included roadway-rating and city-boundary services. The public [Madison County Georgia web map](https://www.arcgis.com/sharing/rest/content/items/21caeb29ce114d6584d4b9e17340c18c/data?f=pjson) contained no operational layers.
- The [Madison, GA Hydrant Flowing web map](https://www.arcgis.com/home/item.html?id=db925042aa2d4f258bb2c96414045bde) refers to **Madison city in Morgan County**, with extent approximately -83.58/33.53 to -83.36/33.71. It was rejected for this request. Other-state Madison County datasets were also not accepted.

## Regional checks and next step

Reviewed public ArcGIS catalog results for Oglethorpe, Madison/Georgia, hydrants and regional/municipal mapping, including remaining search-result pages for Oglethorpe and NEGRC. Inspected relevant public service directories and map contents. The shared [regional service directory](https://services1.arcgis.com/Ug5xGQbHsD8zuZzM/arcgis/rest/services?f=pjson) includes many jurisdictions: the existing Fire_Hydrants service has only the already-integrated Monroe layer /12. Another service named Hydrants has a western-Georgia extent (roughly -85.06,32.67), not the requested counties. A name match alone was not accepted.

This is a bounded public-source review, not proof that no public inventory exists. Request a current publicly shareable or explicitly authorized hydrant GIS export (GeoJSON, shapefile, GeoPackage, CSV with coordinates and coordinate system) or anonymous queryable point-layer URL from Oglethorpe Fire & Rescue/municipal water utilities and Madison County Water Department/municipal utilities. Retain publisher, geographic scope, record IDs, coordinate reference system, export/edit timestamps, status definitions and permission to use/redistribute. Verify geometry, completeness and a known-point spatial query before enabling a source. Do not scrape restricted maps or infer asset coordinates from historical illustrations.

Any future distance remains approximate map straight-line distance, not an underwriting-approved measurement. Missing public points never prove no actual hydrant exists.
