import copy
import json
from pathlib import Path
import pytest
from locator import (DATA, GEOD, LookupError, distance_feet, get_json, load_coverage,
                     load_sources, locate, parse_matches, query_source, search_envelope)

def test_geodesic_known_equatorial_distance_and_zero():
    assert distance_feet(0, 0, 1, 0) == pytest.approx(111319.49079327357 / .3048)
    assert distance_feet(-83.6, 34, -83.6, 34) == 0

@pytest.mark.parametrize('lon,lat', [(float('nan'), 34), (181, 34), (-83, 91)])
def test_bad_coordinates(lon, lat):
    with pytest.raises(LookupError): distance_feet(lon, lat, -83, 34)

@pytest.mark.parametrize('lat', [30, 33, 35])
def test_envelope_contains_entire_ten_mile_circle(lat):
    envelope = search_envelope(-83, lat, 52800)
    for bearing in range(360):
        x, y, _ = GEOD.fwd(-83, lat, bearing, 52800*.3048)
        assert envelope['xmin'] <= x <= envelope['xmax']
        assert envelope['ymin'] <= y <= envelope['ymax']

def test_county_registry():
    counties = load_coverage()
    assert len(counties) == len({c['fips'] for c in counties}) == 159
    assert sum(c['status']=='supported_partial' for c in counties) == 14
    assert all(c['fips'].startswith('13') for c in counties)
    assert len(load_sources()) == 19
    by_fips = {c['fips']:c for c in counties}
    for fips, sid in [('13135','gwinnett'),('13059','clarke'),('13207','monroe'),('13157','jackson'),('13219','oconee'),('13089','dekalb')]:
        assert by_fips[fips]['source_ids'] == sid
        assert by_fips[fips]['status'] == 'supported_partial'

def test_example_geocode():
    data = json.loads((DATA/'geocode.json').read_text())
    match = parse_matches(data)[0]
    assert match['county_fips'] == '13013'
    assert 'SYNTHETIC' in match['address']
    assert -84 < match['lon'] < -83
    data['result']['addressMatches'][0]['addressComponents']['state'] = 'AL'
    with pytest.raises(LookupError): parse_matches(data)

def test_empty_and_malformed_geocode():
    for data in ({}, {'result': {'addressMatches': []}}):
        with pytest.raises(LookupError): parse_matches(data)

SOURCE = {'id': 'test', 'name': 'Test Government', 'url': 'https://example.gov/0', 'date_field':'edited'}
def fixture_fetch(mode='normal'):
    calls = []
    def fetch(url, params=None):
        calls.append(params)
        if params is None:
            return {'geometryType':'esriGeometryPoint','objectIdField':'OBJECTID','maxRecordCount':1}
        if params.get('returnIdsOnly'):
            return {'objectIds': [] if mode == 'empty' else [2,1]}
        oid = int(params['objectIds'])
        x, y, _ = GEOD.fwd(-83, 34, 90, (100 if oid == 2 else 9000))
        return {'spatialReference':{'wkid':3857 if mode=='wrong_crs' else 4326},
                'exceededTransferLimit': mode=='truncated',
                'features': [] if mode=='missing' else [{'attributes':{'OBJECTID':oid},
                 'geometry':None if mode=='null' else {'x':x,'y':y}}]}
    return fetch, calls

def test_batches_radius_and_ranking():
    fetch, calls = fixture_fetch()
    result = query_source(SOURCE, -83,34,5280,fetch)
    assert result['ids_checked'] == 2
    assert len(result['candidates']) == 1
    assert result['candidates'][0]['object_id'] == 2
    assert result['candidates'][0]['distance_ft'] == pytest.approx(100/.3048)
    assert len(calls) == 4

@pytest.mark.parametrize('mode',['wrong_crs','truncated','missing','null'])
def test_fail_closed_for_incomplete_or_invalid_features(mode):
    fetch,_ = fixture_fetch(mode)
    with pytest.raises(LookupError): query_source(SOURCE,-83,34,5280,fetch)

def test_empty_source_is_successful_but_not_absence_proof():
    fetch,_ = fixture_fetch('empty')
    assert query_source(SOURCE,-83,34,5280,fetch)['candidates']==[]

@pytest.mark.parametrize('count',[0,1])
def test_null_ids_require_zero_count(count):
    def fetch(url,params=None):
        if params is None: return {'geometryType':'esriGeometryPoint','objectIdField':'OID'}
        if params.get('returnIdsOnly'): return {'objectIds':None}
        return {'count':count}
    if count==0:
        assert query_source(SOURCE,-83,34,5280,fetch)['ids_checked']==0
    else:
        with pytest.raises(LookupError): query_source(SOURCE,-83,34,5280,fetch)

def test_partial_failure_and_cross_county_queries():
    seen=[]
    def query(source,*args):
        seen.append(source['id'])
        if source['id']=='broken': raise LookupError('timeout')
        return {'source_id':source['id'],'candidates':[{'distance_ft':42}], 'error':None}
    result=locate({'lon':-83,'lat':34,'county_fips':'13013'}, sources=[SOURCE,{**SOURCE,'id':'broken'}],query=query)
    assert set(seen)=={'test','broken'}
    assert result['status']=='partial' and not result['complete']
    assert result['nearest']['distance_ft']==42

def test_service_error_and_invalid_json(monkeypatch):
    import io
    import urllib.request
    for body in [b'{"error":{"code":498}}',b'<html>not json</html>']:
        monkeypatch.setattr(urllib.request,'urlopen',lambda *a,**k:io.BytesIO(body))
        with pytest.raises(LookupError): get_json('https://example.gov')


def test_walton_is_historical_and_never_automatic_official_coverage():
    assert next(c for c in load_coverage() if c['fips']=='13297')['status']=='supported_historical'
    source=next(s for s in load_sources() if s['id']=='walton_historical')
    assert source['requires_opt_in'] and source['publisher_verified'] is False
    seen=[]
    locate({'lon':-83.7,'lat':33.8},5280,query=lambda s,*a:seen.append(s['id']) or {'error':None,'candidates':[]})
    assert 'walton_historical' not in seen and 'franklin_carnesville' in seen

@pytest.mark.parametrize('fips', ['13195', '13221'])
def test_unverified_eastern_counties_do_not_claim_coverage(fips):
    entry = next(c for c in load_coverage() if c['fips'] == fips)
    assert entry['status'] == 'researched_unverified'
    assert not entry['source_ids']
    assert entry['last_verified'] and 'no official public hydrant point inventory verified' in entry['scope'].lower()
    assert not any(fips in source['county_fips'] for source in load_sources())

def test_oconee_generalization_caution():
    assert 'generalized' in next(s for s in load_sources() if s['id']=='oconee')['result_caution']
