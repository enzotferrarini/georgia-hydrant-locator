import html
import json
import math
import time
import folium
from folium.plugins import MarkerCluster
import streamlit as st
from streamlit_folium import st_folium
from locator import (DISCLAIMER, LookupError, geocode, load_coverage, load_sources, locate,
                     barrow_address_options, corrected_origin)

st.set_page_config(page_title='Georgia Hydrant Locator', page_icon='📍', layout='wide')
st.title('Georgia Fire Hydrant Locator')
st.caption('PUBLIC GOVERNMENT GIS · GEORGIA ADDRESSES · DISTANCES IN FEET')
st.info(DISCLAIMER)
sources, coverage = load_sources(), load_coverage()

REQUEST_COOLDOWN_SECONDS = 5


def throttle(action):
    current = time.monotonic()
    key = f'last_request_{action}'
    previous = st.session_state.get(key)
    if previous is not None:
        remaining = REQUEST_COOLDOWN_SECONDS - (current - previous)
        if remaining > 0:
            seconds = math.ceil(remaining)
            unit = 'second' if seconds == 1 else 'seconds'
            raise LookupError(f'Please wait {seconds} {unit} before repeating this action.')
    st.session_state[key] = current


def reset_search():
    for key in ('matches','result','origin','origin_key','pending_point','last_map_click',
                'edit_origin','finish_origin_edit'):
        st.session_state.pop(key, None)


with st.sidebar:
    st.header('Coverage at a glance')
    supported = [c for c in coverage if c['status'] == 'supported_partial']
    st.metric('Counties with an integrated source', f'{len(supported)} / {len(coverage)}')
    st.write(' · '.join('Cobb (Smyrna only)' if c['fips']=='13067' else c['county'].removesuffix(' County') for c in supported))
    st.caption('Partial published inventories. A successful search cannot establish the nearest actual hydrant.')
    st.caption('Addresses go to Census and, for Barrow matches, county GIS. Search coordinates go to GIS providers. OpenStreetMap receives map-tile requests. Inputs stay in this session; downloads contain your address and coordinates.')
    if st.button('Clear this session'):
        reset_search()
        st.session_state.address_input = ''
        st.rerun()

search_tab, coverage_tab, about_tab = st.tabs(['Find a hydrant', '159-county coverage', 'Sources & method'])
with search_tab:
    with st.form('address_form'):
        address = st.text_input('Georgia street address', value='', placeholder='Enter a Georgia street address', key='address_input', max_chars=300)
        submitted = st.form_submit_button('Locate address', type='primary')
    if submitted:
        try:
            throttle('address')
            reset_search()
            with st.spinner('Checking Georgia address locations…'):
                matches = geocode(address)
                options = []
                for match in matches:
                    try:
                        options.extend(barrow_address_options(match))
                    except LookupError:
                        st.warning('County address points could not be checked. Census street interpolation is available; verify or correct the pin.')
                    options.append(match)
                st.session_state.matches = options
        except LookupError as exc:
            st.error(str(exc))
    matches = st.session_state.get('matches', [])
    if matches:
        selected = st.selectbox('Matched location — verify before searching', range(len(matches)),
                                format_func=lambda i: f"{matches[i]['address']} · {matches[i]['provider']}")
        original = matches[selected]
        identity = (selected, original['lon'], original['lat'], original['address'])
        if st.session_state.get('origin_key') != identity:
            st.session_state.origin_key = identity
            st.session_state.origin = original.copy()
            st.session_state.pop('result',None)
            st.session_state.pop('pending_point',None)
            st.session_state.pop('last_map_click',None)
            st.session_state.edit_origin = False
        match = st.session_state.origin
        st.write(f"**{match['county']}** · Property point: {match['lat']:.7f}, {match['lon']:.7f}")
        st.caption(f"{match['provider']} — {match['precision']}")
        if match['provider'] == 'US Census Geocoder':
            st.warning('The address pin is estimated along the street, not placed on the building. Check the blue pin; move it to the building before relying on the distance.')
        elif match['provider'] == 'User-selected map point':
            st.success('Distances are measured from your selected starting point.')
        st.markdown(f"[Location source]({match['source_url']})")
        if 'geocoder_offset_ft' in match:
            st.caption(f"County point is {match['geocoder_offset_ft']:,.0f} ft from the Census street position. This is a difference between sources, not a measured error bound.")
        entry = next((c for c in coverage if c['fips']==match['county_fips']),None)
        if not entry or entry['status'] != 'supported_partial':
            st.warning('No local source is integrated for this county. Only nearby records from configured layers can be found.')
        if match['county_fips']=='13013':
            st.warning('Barrow coverage primarily represents county-owned utility hydrants, not every municipal system. Winder, Auburn, Statham, Bethlehem and Braselton may have additional unmapped hydrants. Confirm with the serving water utility.')
        elif match['county_fips']=='13121':
            st.warning('Fulton combines Roswell, North Fulton county-water and Atlanta water-system inventories. Separate municipal/private systems may be missing; countywide completeness is not certified.')
        elif match['county_fips']=='13067':
            st.warning('Cobb coverage currently includes Smyrna’s public inventory only. County-owned and other municipal systems are not comprehensively represented.')
        elif match['county_fips']=='13117':
            st.caption('Forsyth searches published Existing/Active records; construction, removed and inactive records are excluded. Operation and countywide completeness are not certified.')
        radius = st.select_slider('Search radius (miles)', options=[1,2,5,10],value=5)
        result = st.session_state.get('result')
        if result and (result['address'] != match or result['radius_ft'] != radius*5280):
            st.session_state.pop('result',None)
            result = None
        if st.button('Search near this address',type='primary'):
            try:
                throttle('hydrants')
                result = None
                st.session_state.pop('result', None)
                with st.spinner('Checking public hydrant layers…'):
                    result = locate(match,radius*5280)
                st.session_state.result = result
            except LookupError as exc:
                st.error(str(exc))
        if st.session_state.pop('finish_origin_edit',False):
            st.session_state.edit_origin = False
        edit = st.checkbox('Move starting point to the building',key='edit_origin')
        if not edit:
            st.session_state.pop('pending_point',None)
            st.session_state.pop('last_map_click',None)
        pending = st.session_state.get('pending_point')
        if edit:
            st.info('Click directly on the building or measurement start point. An orange pin will preview your choice. Then select Use this point and recalculate. Points must be within two miles of the matched address and verified inside Georgia; they are not surveyed positions.')
            if pending:
                st.warning('New starting point selected. The previous distance is hidden until you recalculate.')
            apply_col,cancel_col = st.columns([2,1])
            apply = apply_col.button('Use this point and recalculate',type='primary',disabled=not pending)
            cancel = cancel_col.button('Cancel selected point',disabled=not pending)
            if cancel:
                st.session_state.pop('pending_point',None)
                st.rerun()
            if apply:
                try:
                    throttle('correction')
                    with st.spinner('Checking your point and recalculating nearby hydrants…'):
                        new_origin = corrected_origin(original,pending['lng'],pending['lat'])
                        new_result = locate(new_origin,radius*5280)
                    st.session_state.origin = new_origin
                    st.session_state.result = new_result
                    st.session_state.pop('pending_point',None)
                    st.session_state.pop('last_map_click',None)
                    st.session_state.finish_origin_edit = True
                    st.rerun()
                except LookupError as exc:
                    st.error(str(exc))
        if result and not pending:
            if not result['complete']:
                st.warning('Some live sources could not be fully checked. This candidate may use a dated backup; review source status below.')
            nearest = result['nearest']
            if nearest:
                st.metric('Approximate map straight-line distance', f"{nearest['distance_ft']:,.0f} ft")
                st.markdown(f"**{nearest['source_name']}** · Record {nearest['object_id']} · [GIS layer]({nearest['source_url']})")
                st.write(f"Hydrant: {nearest['lat']:.7f}, {nearest['lon']:.7f}")
                st.caption('Closest mapped point in the checked layers; closest actual hydrant is not verified. No road or hose-lay distance is calculated.')
                source = next(s for s in sources if s['id']==nearest['source_id'])
                if source.get('result_caution'): st.warning(source['result_caution'])
                st.caption('Mapped equipment is not proof of active, accessible fire protection. Confirm operational status with the utility.')
            else:
                st.warning(f'No mapped result within {radius} miles. This is not proof that no hydrant exists.')
            with st.expander('Source timestamps and query status', expanded=not result['complete']):
                for report in result['sources']:
                    st.markdown(f"**[{report['name']}]({report['url']})**")
                    if report['error']: st.warning(report['error'])
                    else:
                        if report.get('nearby_inventory_limited'):
                            st.caption(f"Dense inventory: nearest verified using a {report['searched_radius_ft']/5280:g}-mile inner search. Outer records within the selected maximum radius were not loaded for map display.")
                        if report.get('inventory_filter') and report['inventory_filter'] != '1=1':
                            st.caption(report.get('inventory_filter_label') or 'Published status exclusions applied; see source notes.')
                        if report.get('is_snapshot'):
                            st.warning(f"Using saved {report['name']} backup downloaded {report['snapshot_downloaded_at']} ({report['snapshot_age_days']} days old). Live query failed: {report['live_error']} Locations may have changed since download.")
                        st.caption(f"Records checked: {report['ids_checked']} · Publisher edit: {report['source_data_updated_at'] or 'Not supplied'} · Retrieved UTC: {report['retrieved_at']}")
            st.download_button('Download this result (contains address)',json.dumps(result,indent=2),'hydrant-result.json','application/json')
        m = folium.Map(location=[match['lat'],match['lon']],zoom_start=16,tiles='OpenStreetMap')
        folium.Marker([match['lat'],match['lon']],tooltip='Current measurement starting point',icon=folium.Icon(color='blue',icon='home')).add_to(m)
        if result and result['nearest']:
            n=result['nearest']
            if not edit:
                folium.Marker([n['lat'],n['lon']],tooltip=f"Nearest mapped hydrant: {n['distance_ft']:,.0f} ft",icon=folium.Icon(color='red',icon='fire')).add_to(m)
            cluster=MarkerCluster(name='Other nearby hydrants',options={'chunkedLoading':True}).add_to(m)
            for point in result['candidates'] if edit else result['candidates'][1:]:
                label=html.escape(f"{point['source_name']} · record {point['object_id']}" if edit else f"{point['distance_ft']:,.0f} ft · {point['source_name']} · record {point['object_id']}")
                folium.Marker([point['lat'],point['lon']],tooltip=label,popup=label,icon=folium.Icon(color='green',icon='tint')).add_to(cluster)
            if not edit:
                folium.PolyLine([[match['lat'],match['lon']],[n['lat'],n['lon']]],color='#c52f22',dash_array='6,6',tooltip='Straight-line connection; not a route').add_to(m)
                m.fit_bounds([[match['lat'],match['lon']],[n['lat'],n['lon']]],padding=(60,60),max_zoom=18)
            st.caption(f"Showing {len(result['candidates'])} of {result.get('candidate_count',len(result['candidates']))} retrieved matching records (nearest 250 maximum). Dense-source searches may load a smaller inner area; see source status. Click clusters to inspect nearby hydrants.")
        preview = folium.FeatureGroup(name='Selected starting point')
        if edit and pending:
            folium.Marker([pending['lat'],pending['lng']],tooltip='Selected starting point — not applied yet',icon=folium.Icon(color='orange',icon='home')).add_to(preview)
        map_data = st_folium(m,height=480,use_container_width=True,returned_objects=['last_clicked'] if edit else [],feature_group_to_add=preview,key=f"map_{identity}_{match['lon']}_{match['lat']}_{edit}_{bool(result)}")
        if edit:
            st.caption('Blue house: current starting point · Orange house: your selected point, not applied yet · Green markers/clusters: mapped hydrants. Select Use this point and recalculate above the map to update the nearest hydrant. Map © OpenStreetMap contributors; hydrants from listed government sources.')
        else:
            st.caption('Blue house: property point · Red flame: nearest mapped hydrant · Green markers/clusters: nearby records · Dashed red line: straight-line distance. Map © OpenStreetMap contributors; hydrants from listed government sources.')
        if edit:
            click=(map_data or {}).get('last_clicked')
            if click and click != st.session_state.get('last_map_click'):
                st.session_state.last_map_click=click
                st.session_state.pending_point=click
                st.rerun()

with coverage_tab:
    st.subheader('All 159 Georgia counties')
    st.write('Supported — partial: some verified layers are integrated. Researched — unverified: a candidate was not accepted. Not researched: no source integrated yet. None of these labels establishes absence of hydrants.')
    needle=st.text_input('Filter counties')
    st.dataframe([c for c in coverage if needle.lower() in c['county'].lower()],hide_index=True,width='stretch')
    st.download_button('Download coverage register',json.dumps(coverage,indent=2),'georgia-159-county-coverage.json','application/json')
with about_tab:
    for source in sources:
        st.markdown(f"**[{source['name']}]({source['url']})** — {source['scope']}")
        st.markdown(f"[Government evidence]({source['evidence_url']}) · Verified {source['verified_at']}")
        st.caption(source['notes'])
    st.write('Distances use WGS84 ellipsoidal geometry, converted at 0.3048 metres per foot. Every configured layer is searched across county boundaries. All candidate IDs and feature batches must agree. No municipal completeness, field survey accuracy, operational status or underwriting approval is implied.')
    st.write('Inputs are session-only, with no disk storage or cross-user address cache. Providers and the hosting platform may retain request/security logs. Download only if you want a local copy of the address and coordinates. Public repositories contain synthetic test fixtures, never submitted searches.')
