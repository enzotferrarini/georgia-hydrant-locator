"""Read-only government GIS queries and WGS84 ellipsoidal distances."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import json
import math
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pyproj import Geod

DATA = Path(__file__).parent / 'data'
GEOD = Geod(ellps='WGS84')
SEARCH_SLOTS = threading.BoundedSemaphore(2)
HTTP_SLOTS = threading.BoundedSemaphore(8)
MAX_RECORDS = 10000
BARROW_ADDRESSES = 'https://services5.arcgis.com/OVFGXfRTCVcPwl55/arcgis/rest/services/BCGIS_Base_Layers/FeatureServer/112'
CENSUS = 'https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress'
DISCLAIMER = ('Map straight-line distance only; not underwriting-approved hydrant distance. '
              'The address point may be interpolated along a street. Confirm the building, '
              'accessible hose route, hydrant operation and insurer requirements with the relevant authority. '
              'An absence of mapped results is never proof that no hydrant exists.')

class LookupError(Exception):
    """An expected external-service or input failure safe to show to users."""

def now():
    return datetime.now(timezone.utc).isoformat()

def get_json(url, params=None):
    query = urllib.parse.urlencode({'f': 'json', **(params or {})})
    request = urllib.request.Request(url + '?' + query)
    for attempt in range(2):
        try:
            with HTTP_SLOTS, urllib.request.urlopen(request, timeout=15) as response:
                body = response.read(8_000_001)
                if len(body) > 8_000_000:
                    raise LookupError('Service response exceeded the safety limit. Reduce the radius.')
                data = json.loads(body)
            if not isinstance(data, dict):
                raise LookupError('The service returned an unexpected response.')
            if data.get('error') or data.get('errors'):
                raise LookupError('The government service rejected the request. It may be unavailable or require access permission.')
            return data
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < 1:
                time.sleep(attempt + 1)
                continue
            raise LookupError(f'Service unavailable (HTTP {exc.code}). Try again later.') from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt < 1:
                time.sleep(attempt + 1)
                continue
            raise LookupError('Could not reach the government service. Check connectivity and retry.') from exc
        except (ValueError, UnicodeError) as exc:
            raise LookupError('The government service returned invalid JSON.') from exc

def load_sources():
    return json.loads((DATA / 'sources.json').read_text(encoding='utf-8'))

def load_coverage():
    return json.loads((DATA / 'coverage.json').read_text(encoding='utf-8'))

def valid_point(lon, lat):
    return all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in (lon, lat)) and -180 <= lon <= 180 and -90 <= lat <= 90

def parse_matches(data):
    matches = data.get('result', {}).get('addressMatches')
    if not isinstance(matches, list):
        raise LookupError('Geocoder response is missing address matches.')
    accepted = []
    for match in matches:
        counties = match.get('geographies', {}).get('Counties', [])
        coord = match.get('coordinates', {})
        if match.get('addressComponents', {}).get('state') != 'GA':
            continue
        if len(counties) != 1 or not counties[0].get('GEOID', '').startswith('13'):
            continue
        if not valid_point(coord.get('x'), coord.get('y')):
            continue
        accepted.append({'address': match['matchedAddress'], 'lon': coord['x'], 'lat': coord['y'],
                         'county': counties[0]['NAME'], 'county_fips': counties[0]['GEOID'],
                         'provider': 'US Census Geocoder', 'precision': 'Street address-range interpolation; not rooftop',
                         'benchmark': data['result'].get('input', {}).get('benchmark'),
                         'vintage': data['result'].get('input', {}).get('vintage'),
                         'retrieved_at': now(), 'source_url': CENSUS})
    if not accepted:
        raise LookupError('No verified Georgia street-address match. Include the street number, street, city, GA and ZIP; check spelling. This says nothing about hydrants.')
    return accepted

def geocode(address):
    if len(address.strip()) < 8 or len(address) > 300 or not any(c.isdigit() for c in address):
        raise LookupError('Enter a full street address including a street number, Georgia city and ZIP.')
    return parse_matches(get_json(CENSUS, {'address': address.strip(), 'benchmark': 'Public_AR_Current',
                                         'vintage': 'Current_Current', 'format': 'json'}))

def distance_feet(lon1, lat1, lon2, lat2):
    if not valid_point(lon1, lat1) or not valid_point(lon2, lat2):
        raise LookupError('Invalid map coordinates.')
    return GEOD.inv(lon1, lat1, lon2, lat2)[2] / 0.3048

def search_envelope(lon, lat, radius_ft):
    # Conservative WGS84 envelope for Georgia (29–36 N), including all points
    # in the search circle. 110 km/degree is below local meridional scale.
    if not valid_point(lon, lat) or not 29 <= lat <= 36 or not -86 <= lon <= -80:
        raise LookupError('Search location is outside the Georgia region.')
    if not 0 < radius_ft <= 52800:
        raise LookupError('Search radius must be greater than zero and at most 10 miles.')
    dy = radius_ft * 0.3048 / 110000
    dx = dy / math.cos(math.radians(abs(lat) + dy))
    return {'xmin': lon-dx, 'ymin': lat-dy, 'xmax': lon+dx, 'ymax': lat+dy,
            'spatialReference': {'wkid': 4326}}

def timestamp(value):
    try:
        return datetime.fromtimestamp(value / 1000, timezone.utc).isoformat() if value is not None else None
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def status_rules(source):
    return ([source['status_filter']] if source.get('status_filter') else []) + source.get('status_filters', [])


def source_where(source):
    """Build a fixed registry status filter; user input never enters this SQL."""
    clauses = []
    for rule in status_rules(source):
        field = rule['field']
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', field):
            raise LookupError('Invalid configured status field.')
        mode = 'include' if 'include' in rule else 'exclude'
        values = rule.get(mode)
        if not isinstance(values,list) or not values or any(type(v) not in (str,int) for v in values):
            raise LookupError('Invalid configured status values.')
        literals = ','.join("'"+v.replace("'","''")+"'" if isinstance(v,str) else str(v) for v in values)
        clauses.append(f'{field} IN ({literals})' if mode=='include' else
                       f'({field} NOT IN ({literals}) OR {field} IS NULL)')
    return ' AND '.join(clauses) or '1=1'


def accepted_status(source,attributes):
    for rule in status_rules(source):
        if rule['field'] not in attributes:
            return False
        value = attributes[rule['field']]
        if not (value in rule['include'] if 'include' in rule else value not in rule['exclude']):
            return False
    return True

def query_source(source, lon, lat, radius_ft, fetch=get_json):
    if source.get('kind') == 'historical_map':
        from historical import query_historical
        return query_historical(source, lon, lat, radius_ft)
    url = source['url']
    meta = fetch(url)
    if meta.get('geometryType') != 'esriGeometryPoint':
        raise LookupError('Configured layer is no longer a point layer.')
    oid = meta.get('objectIdField') or next((f['name'] for f in meta.get('fields', []) if f['type'] == 'esriFieldTypeOID'), None)
    if not oid:
        raise LookupError('Layer has no object ID field; completeness cannot be verified.')
    rules = status_rules(source)
    available = {f['name'] for f in meta.get('fields', [])}
    if any(rule['field'] not in available for rule in rules):
        raise LookupError('Source status schema changed; this inventory cannot be verified.')
    spatial = {'where': source_where(source), 'geometry': json.dumps(search_envelope(lon, lat, radius_ft)),
                                  'geometryType': 'esriGeometryEnvelope', 'inSR': 4326,
                                  'spatialRel': 'esriSpatialRelIntersects'}
    found = fetch(url + '/query', {**spatial, 'returnIdsOnly': 'true'})
    ids = found.get('objectIds')
    # Some Enterprise services use null for an empty ID set. Verify with count.
    if 'objectIds' in found and ids is None and not found.get('exceededTransferLimit'):
        count = fetch(url + '/query', {**spatial, 'returnCountOnly': 'true'})
        if count.get('count') == 0:
            ids = []
    if not isinstance(ids, list) or any(not isinstance(i, int) for i in ids) or found.get('exceededTransferLimit'):
        raise LookupError('Incomplete ID response; nearest result cannot be determined.')
    ids = sorted(set(ids))
    if len(ids) > MAX_RECORDS:
        depth = source.get('_adaptive_depth', 0)
        if source.get('adaptive_radius') and depth < 5:
            inner = query_source({**source, '_adaptive_depth':depth+1}, lon, lat, radius_ft/2, fetch)
            # An inner-circle candidate is necessarily nearer than every omitted
            # outer-circle point. An empty inner circle cannot prove the outer empty.
            if inner['candidates']:
                inner['requested_radius_ft'] = radius_ft
                inner.setdefault('searched_radius_ft', radius_ft/2)
                inner['nearby_inventory_limited'] = True
                return inner
        raise LookupError('Too many records in this area. Reduce the search radius.')
    candidates, invalid = [], 0
    deadline = time.monotonic() + 60
    fields = [oid] + [f for f in (source.get('date_field'), source.get('identity_field')) if f and f in available]
    fields.extend(rule['field'] for rule in rules)
    batch_size = max(1, min(200, int(meta.get('maxRecordCount') or 200)))
    for start in range(0, len(ids), batch_size):
        if time.monotonic() > deadline:
            raise LookupError('Source query time limit reached. Reduce the radius and retry.')
        batch = ids[start:start+batch_size]
        response = fetch(url + '/query', {'objectIds': ','.join(map(str, batch)), 'outFields': ','.join(dict.fromkeys(fields)),
                                         'returnGeometry': 'true', 'outSR': 4326})
        sr = response.get('spatialReference', {})
        if sr.get('latestWkid', sr.get('wkid')) != 4326:
            raise LookupError('Service did not return WGS84 geometry; distance was not calculated.')
        features = response.get('features', [])
        returned = {f.get('attributes', {}).get(oid) for f in features}
        if response.get('exceededTransferLimit') or returned != set(batch) or len(features) != len(batch):
            raise LookupError('Incomplete feature batch or changing dataset. Retry; no nearest claim is available.')
        for feature in features:
            if not accepted_status(source,feature.get('attributes',{})):
                raise LookupError('Service returned an excluded or unknown status; nearest result cannot be verified.')
            geometry = feature.get('geometry') or {}
            x, y = geometry.get('x'), geometry.get('y')
            if not valid_point(x, y):
                invalid += 1
                continue
            distance = distance_feet(lon, lat, x, y)
            if distance <= radius_ft + 0.001:
                attrs = feature['attributes']
                candidates.append({'lon': x, 'lat': y, 'distance_ft': distance, 'object_id': attrs[oid],
                                   'source_id': source['id'], 'source_name': source['name'], 'source_url': url,
                                   'asset_identity': str(attrs.get(source.get('identity_field')) or ''), 'identity_namespace': source.get('identity_namespace'), 'feature_updated_at': timestamp(attrs.get(source.get('date_field')))})
    if invalid:
        raise LookupError(f'{invalid} records have missing or invalid geometry; nearest result cannot be verified.')
    return {'source_id': source['id'], 'name': source['name'], 'url': url, 'retrieved_at': now(),
            'source_data_updated_at': timestamp((meta.get('editingInfo') or {}).get('dataLastEditDate') or (meta.get('editingInfo') or {}).get('lastEditDate')),
            'ids_checked': len(ids), 'candidates': sorted(candidates, key=lambda x: x['distance_ft']),
            'inventory_filter': source_where(source),
            'inventory_filter_label': source.get('status_filter_label'), 'error': None}

def _locate(match, radius_ft=26400, sources=None, query=query_source):
    search_envelope(match['lon'], match['lat'], radius_ft)
    sources = sources if sources is not None else [s for s in load_sources() if not s.get('requires_opt_in')]
    def safe(source):
        try:
            return query(source, match['lon'], match['lat'], radius_ft)
        except LookupError as exc:
            if source['id'] == 'gwinnett':
                try:
                    from snapshots import query_snapshot
                    backup = query_snapshot(source, match['lon'], match['lat'], radius_ft)
                    backup['live_error'] = str(exc)
                    return backup
                except LookupError as fallback_error:
                    exc = LookupError(str(exc) + ' Backup: ' + str(fallback_error))
            return {'source_id': source['id'], 'name': source['name'], 'url': source['url'],
                    'retrieved_at': now(), 'error': str(exc), 'candidates': []}
    # Search every integrated layer: county boundaries must not truncate the search.
    with ThreadPoolExecutor(max_workers=4) as pool:
        reports = list(pool.map(safe, sources))
    candidates = sorted([c for r in reports for c in r['candidates']], key=lambda x: x['distance_ft'])
    candidates = deduplicate(candidates)
    errors = [r for r in reports if r['error']]
    backups = [r for r in reports if r.get('is_snapshot')]
    historical = [r for r in reports if r.get('is_historical')]
    partial = bool(errors or backups or historical)
    return {'address': match, 'radius_ft': radius_ft, 'queried_at': now(), 'complete': not partial,
            'status': 'partial' if partial else ('found' if candidates else 'no_mapped_result'),
            'nearest': candidates[0] if candidates else None, 'candidates': candidates[:250], 'candidate_count': len(candidates), 'display_limit': 250,
            'sources': [{k: v for k, v in r.items() if k != 'candidates'} for r in reports],
            'disclaimer': DISCLAIMER, 'scope': 'Nearest among selected public GIS sources within the selected radius; not all actual hydrants. Optional historical sources are identified separately.'}


def deduplicate(candidates):
    """Only merge same-source IDs or explicitly namespaced asset IDs at identical points.

    Nearby/even coincident records without shared identity remain separate.
    """
    result, seen = [], {}
    for point in candidates:
        identity = (point.get('identity_namespace'), point.get('asset_identity'))
        key = (('asset', *identity) if all(identity) else
               ('record', point.get('source_url', point.get('source_id')), point.get('object_id')))
        key += (point.get('lon'), point.get('lat'))
        provenance = {k: point.get(k) for k in ('source_id','source_name','source_url','object_id')}
        if key in seen:
            seen[key]['also_reported_by'].append(provenance)
        else:
            item = {**point, 'also_reported_by': []}
            seen[key] = item
            result.append(item)
    return result


def locate(match, radius_ft=26400, sources=None, query=query_source):
    if not SEARCH_SLOTS.acquire(blocking=False):
        raise LookupError('The server is busy with other searches. Please retry shortly.')
    try:
        return _locate(match, radius_ft, sources, query)
    finally:
        SEARCH_SLOTS.release()


def normalized_address(value):
    aliases = {'NORTH':'N','SOUTH':'S','EAST':'E','WEST':'W','STREET':'ST',
               'ROAD':'RD','AVENUE':'AVE','DRIVE':'DR','LANE':'LN','COURT':'CT',
               'BOULEVARD':'BLVD','HIGHWAY':'HWY','PARKWAY':'PKWY','TRAIL':'TRL'}
    return ' '.join(aliases.get(t,t) for t in re.findall(r"[A-Z0-9]+", value.upper()))


def barrow_address_options(match, fetch=get_json):
    """Conservative exact normalized address match; never assert rooftop precision."""
    if match['county_fips'] != '13013':
        return []
    street = match['address'].split(',')[0]
    number = re.match(r'^(\d+)\s', street)
    if not number:
        return []
    response = fetch(BARROW_ADDRESSES + '/query', {
        'where': "State='GA' AND Add_Number=" + number[1],
        'outFields':'OBJECTID,StrFullAdd,Placement,State,Unit,DateUpdate',
        'outSR':4326, 'returnGeometry':'true', 'resultRecordCount':100})
    if response.get('exceededTransferLimit'):
        raise LookupError('County address search was incomplete; use the Census point or correct it manually.')
    sr = response.get('spatialReference', {})
    if sr.get('latestWkid',sr.get('wkid')) != 4326:
        raise LookupError('County address service returned an unexpected coordinate system.')
    result = []
    for feature in response.get('features', []):
        a, g = feature.get('attributes',{}), feature.get('geometry') or {}
        if a.get('State') != 'GA' or a.get('Unit') or normalized_address(a.get('StrFullAdd','')) != normalized_address(street):
            continue
        if not valid_point(g.get('x'),g.get('y')) or distance_feet(match['lon'],match['lat'],g['x'],g['y']) > 5280:
            continue
        placement = a.get('Placement') or 'unspecified placement'
        result.append({**match, 'lon':g['x'], 'lat':g['y'],
            'provider':'Barrow County GIS address points',
            'precision':f'County address point — {placement}; positional accuracy not certified',
            'source_url':BARROW_ADDRESSES, 'record_id':a.get('OBJECTID'),
            'feature_updated_at':timestamp(a.get('DateUpdate')), 'retrieved_at':now(),
            'geocoder_offset_ft':distance_feet(match['lon'],match['lat'],g['x'],g['y'])})
    return result


def corrected_origin(original, lon, lat, fetch=get_json):
    search_envelope(lon, lat, 5280)
    if distance_feet(original['lon'],original['lat'],lon,lat) > 10560:
        raise LookupError('Correction must be within two miles of the matched address. Search again for a different property.')
    url = 'https://geocoding.geo.census.gov/geocoder/geographies/coordinates'
    data = fetch(url, {'x':lon,'y':lat,'benchmark':'Public_AR_Current','vintage':'Current_Current','format':'json'})
    counties = data.get('result',{}).get('geographies',{}).get('Counties',[])
    if len(counties) != 1 or not counties[0].get('GEOID','').startswith('13'):
        raise LookupError('The corrected point could not be verified inside Georgia.')
    origin = {k:v for k,v in original.items() if k not in ('geocoder_offset_ft', 'record_id', 'feature_updated_at')}
    return {**origin, 'lon':lon, 'lat':lat, 'county':counties[0]['NAME'],
            'county_fips':counties[0]['GEOID'], 'provider':'User-selected map point',
            'precision':'Manually selected; not surveyed or underwriting-approved',
            'source_url':url, 'retrieved_at':now(), 'original_provider':original['provider']}
