import html
import json
import folium
import streamlit as st
from streamlit_folium import st_folium
from locator import DISCLAIMER, LookupError, geocode, load_coverage, load_sources, locate

st.set_page_config(page_title='Georgia Hydrant Locator', page_icon='📍', layout='wide')
st.title('Georgia Fire Hydrant Locator')
st.caption('PUBLIC GOVERNMENT GIS · GEORGIA ADDRESSES · DISTANCES IN FEET')
st.info(DISCLAIMER)
sources, coverage = load_sources(), load_coverage()
with st.sidebar:
    st.header('Coverage at a glance')
    supported = [c for c in coverage if c['status'] == 'supported_partial']
    st.metric('Counties with an integrated source', f'{len(supported)} / {len(coverage)}')
    st.write(' · '.join('Fulton (Roswell only)' if c['fips'] == '13121' else 'Athens–Clarke' if c['fips'] == '13059' else c['county'].removesuffix(' County') for c in supported))
    st.caption('Mapped coverage is partial and does not certify every hydrant in any county.')
    st.markdown('**How it works**\n\n1. Locate a Georgia street address.\n2. Check the matched address and map pin.\n3. Search integrated government layers.')
    st.caption('Addresses are sent to the US Census Geocoder. Search coordinates are sent to the listed GIS providers. Map tiles are provided by OpenStreetMap. No API key is required.')

search_tab, coverage_tab, about_tab = st.tabs(['Find a hydrant', '159-county coverage', 'Sources & method'])
with search_tab:
    with st.form('address_form'):
        address = st.text_input('Georgia street address', value='')
        submitted = st.form_submit_button('Locate address', type='primary')
    if submitted:
        for key in ('matches', 'result'):
            st.session_state.pop(key, None)
        try:
            with st.spinner('Checking the address with the US Census Geocoder…'):
                st.session_state.matches = geocode(address)
        except LookupError as exc:
            st.error(str(exc))
    matches = st.session_state.get('matches', [])
    if matches:
        selected = st.selectbox('Matched address — verify before searching', range(len(matches)),
                                format_func=lambda i: matches[i]['address'])
        match = matches[selected]
        st.write(f"**{match['county']}** · {match['lat']:.6f}, {match['lon']:.6f}")
        st.caption('Census street interpolation. The pin may be on the road rather than the building. This affects the measured distance.')
        entry = next((c for c in coverage if c['fips'] == match['county_fips']), None)
        if not entry or entry['status'] != 'supported_partial':
            st.warning('No local source is integrated for this county. Searches can only find nearby features in the configured government layers.')
        elif match['county_fips'] == '13121':
            st.warning('Fulton coverage is limited to Roswell’s published layer. Other Fulton jurisdictions are not integrated.')
        radius = st.select_slider('Search radius (miles)', options=[1, 2, 5, 10], value=5)
        result = st.session_state.get('result')
        if result and (result['address'] != match or result['radius_ft'] != radius*5280):
            result = None
        if st.button('Search near this address', type='primary'):
            with st.spinner(f'Querying all {len(sources)} government layers and checking complete responses…'):
                result = locate(match, radius*5280)
            st.session_state.result = result
        if result:
            if not result['complete']:
                st.warning('One or more GIS sources could not be fully checked. Any displayed distance is only a candidate from the responding layers, not a verified nearest result across the configured sources.')
            nearest = result['nearest']
            if nearest:
                a, b = st.columns([1, 2])
                a.metric('Map straight-line distance' if result['complete'] else 'Available candidate distance', f"{nearest['distance_ft']:,.0f} ft")
                b.markdown(f"**{nearest['source_name']}** · Record {nearest['object_id']}\n\n[Open government GIS layer]({nearest['source_url']})")
                st.caption(result['scope'])
                st.write(f"Hydrant coordinates: {nearest['lat']:.7f}, {nearest['lon']:.7f}")
                source = next(s for s in sources if s['id'] == nearest['source_id'])
                if source.get('result_caution'):
                    st.warning(source['result_caution'])
                with st.expander('Hydrant record and reported condition'):
                    st.write('Mapped records can include inactive, private or unverified equipment. No operational-status filter has been applied. Raw status codes follow the source layer’s field domains.')
                    st.json(nearest['attributes'])
            else:
                st.warning(f'No mapped hydrant result was returned within {radius} miles from the responding layers. This is not proof that no hydrant exists. Contact the local fire department or water utility.')
            with st.expander('Query provenance and source health', expanded=not result['complete']):
                for report in result['sources']:
                    st.markdown(f"**[{report['name']}]({report['url']})**")
                    if report['error']:
                        st.error(report['error'])
                    else:
                        st.write(f"Records checked in search envelope: {report['ids_checked']}")
                        st.write('Publisher data edit timestamp: ' + (report['source_data_updated_at'] or 'Not exposed by this layer'))
                    st.caption('Retrieved (UTC): ' + report['retrieved_at'])
            st.download_button('Download result & provenance (JSON)', json.dumps(result, indent=2), 'hydrant-result.json', 'application/json')
        m = folium.Map(location=[match['lat'], match['lon']], zoom_start=16, tiles='OpenStreetMap')
        folium.Marker([match['lat'], match['lon']], tooltip='Geocoded address',
                      popup=html.escape(match['address']), icon=folium.Icon(color='blue', icon='home')).add_to(m)
        if result and result['nearest']:
            n = result['nearest']
            for i, point in enumerate(result['candidates'][:10]):
                folium.CircleMarker([point['lat'], point['lon']], radius=9 if i == 0 else 5,
                                    color='#d85632' if i == 0 else '#007F7A', fill=True,
                                    tooltip=html.escape(f"{point['distance_ft']:,.0f} ft · {point['source_name']} · {point['object_id']}")).add_to(m)
            folium.PolyLine([[match['lat'], match['lon']], [n['lat'], n['lon']]], color='#d85632', dash_array='6,6', tooltip='Straight-line connection').add_to(m)
            m.fit_bounds([[match['lat'], match['lon']], [n['lat'], n['lon']]], padding=(60, 60), max_zoom=18)
        st_folium(m, height=480, use_container_width=True, returned_objects=[], key=f"map_{selected}_{bool(result)}")
        st.caption('Blue marker: estimated address position · Orange marker: closest returned hydrant · Dashed line: straight-line connection, not a route.')

with coverage_tab:
    st.subheader('Every Georgia county, with an explicit coverage status')
    st.write('“Supported — partial” means a public government source has been verified and integrated. “Not researched” means no source is integrated yet; it does not mean data or hydrants are absent.')
    needle = st.text_input('Filter counties')
    st.dataframe([c for c in coverage if needle.lower() in c['county'].lower()], hide_index=True, width='stretch')
    st.download_button('Download coverage register', json.dumps(coverage, indent=2), 'georgia-159-county-coverage.json', 'application/json')
with about_tab:
    st.subheader('Government sources, with a visible audit trail')
    for source in sources:
        st.markdown(f"**[{source['name']}]({source['url']})** — {source['scope']}")
        st.markdown(f"[Official ownership evidence]({source['evidence_url']}) · Verified {source['verified_at']}")
        st.caption(source['notes'])
    st.write('The app asks each layer for every record ID in a conservative search envelope, retrieves those records in bounded batches, checks IDs and response limits, and requests WGS84 geometry. It ranks points by the WGS84 ellipsoidal surface distance converted with exactly 0.3048 metres per international foot. Elevation and travel routes are excluded.')
    st.write('All integrated layers are searched, including across county boundaries. Search radius is limited to 10 miles. The result is the nearest mapped point in these layers within that radius, never a statewide completeness claim. Dates shown as unavailable are not inferred from the layer name or retrieval date.')
    st.markdown('[Census geocoding documentation](https://geocoding.geo.census.gov/geocoder/Geocoding_Services_API.html) · [ArcGIS query documentation](https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer/)')
