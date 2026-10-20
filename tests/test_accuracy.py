import copy
import json
import pytest
import locator


def match():
    return json.loads((locator.DATA/'example_result.json').read_text())['address']


def response(**attrs):
    return {'spatialReference':{'wkid':4326},'features':[{'attributes':{
        'OBJECTID':7,'StrFullAdd':'100 SYNTHETIC TEST RD','Placement':'STRUCTURE','State':'GA','Unit':None,**attrs},
        'geometry':{'x':-83.5001,'y':33.5}}]}


def test_barrow_exact_address_option():
    calls=[]
    def fetch(url,params): calls.append(params); return response()
    result=locator.barrow_address_options(match(),fetch)
    assert result[0]['provider']=='Barrow County GIS address points'
    assert 'STRUCTURE' in result[0]['precision']
    assert result[0]['geocoder_offset_ft']>0
    assert calls[0]['where']=="State='GA' AND Add_Number=100"
    assert 'Comments' not in calls[0]['outFields']

@pytest.mark.parametrize('attrs',[{'StrFullAdd':'100 OTHER RD'},{'Unit':'2'},{'State':'AL'}])
def test_reject_wrong_address_or_unit(attrs):
    assert locator.barrow_address_options(match(),lambda *a:response(**attrs))==[]

@pytest.mark.parametrize('change',[{'exceededTransferLimit':True},{'spatialReference':{'wkid':3857}}])
def test_reject_incomplete_county_geocoder(change):
    with pytest.raises(locator.LookupError): locator.barrow_address_options(match(),lambda *a:{**response(),**change})


def test_outside_barrow_does_not_query():
    assert locator.barrow_address_options({**match(),'county_fips':'13135'},lambda *a:pytest.fail())==[]


def county_fetch(*a):
    return {'result':{'geographies':{'Counties':[{'GEOID':'13013','NAME':'Barrow County'}]}}}


def test_manual_correction_recalculates_and_preserves_original():
    m=match(); before=copy.deepcopy(m)
    x,y,_=locator.GEOD.fwd(m['lon'],m['lat'],90,30.48)
    corrected=locator.corrected_origin(m,x,y,county_fetch)
    assert locator.distance_feet(m['lon'],m['lat'],x,y)==pytest.approx(100)
    assert m==before and corrected['provider']=='User-selected map point'
    assert locator.distance_feet(corrected['lon'],corrected['lat'],x,y)==0

@pytest.mark.parametrize('lon,lat',[(-80,33.5),(-83.5,90),(float('nan'),33.5)])
def test_invalid_or_distant_manual_correction(lon,lat):
    with pytest.raises(locator.LookupError):locator.corrected_origin(match(),lon,lat,county_fetch)


def test_manual_point_must_be_verified_in_georgia():
    with pytest.raises(locator.LookupError):locator.corrected_origin(match(),-83.5,33.5,lambda *a:{'result':{'geographies':{}}})


def test_deduplicate_identity_only():
    a={'source_id':'a','source_url':'https://example.invalid/a','object_id':1,'lon':-83.5,'lat':33.5,'distance_ft':1}
    b={**a,'source_id':'b','source_url':'https://example.invalid/b'}
    assert len(locator.deduplicate([a,a,b]))==2
    namespaced=[{**p,'identity_namespace':'same-official-system','asset_identity':'hydrant-1'} for p in [a,b]]
    r=locator.deduplicate(namespaced)
    assert len(r)==1 and len(r[0]['also_reported_by'])==1
    namespaced[1]['lat']+=.000001
    assert len(locator.deduplicate(namespaced))==2


def test_resource_limit_before_feature_requests():
    def fetch(url,params=None):
        if params is None:return {'geometryType':'esriGeometryPoint','objectIdField':'OID'}
        assert params.get('returnIdsOnly')
        return {'objectIds':list(range(locator.MAX_RECORDS+1))}
    with pytest.raises(locator.LookupError):locator.query_source({'url':'https://example.invalid'},-83.5,33.5,5280,fetch)


def test_global_search_limit_released():
    assert locator.SEARCH_SLOTS.acquire(False)
    assert locator.SEARCH_SLOTS.acquire(False)
    try:
        with pytest.raises(locator.LookupError): locator.locate(match())
    finally:
        locator.SEARCH_SLOTS.release();locator.SEARCH_SLOTS.release()
    assert locator.locate(match(),sources=[])['complete']


def test_service_error_does_not_echo_sensitive_input(monkeypatch):
    import io
    monkeypatch.setattr(locator.urllib.request,'urlopen',lambda *a,**k:io.BytesIO(b'{"error":{"message":"private input should not leak"}}'))
    with pytest.raises(locator.LookupError) as exc:locator.get_json('https://example.invalid')
    assert 'private input' not in str(exc.value)
