import json
import pytest
import locator

SOURCE={'id':'synthetic','name':'Synthetic','url':'https://example.invalid/0',
        'status_filter':{'field':'STATE','include':['Active']}}


def test_new_registry_sources_and_coverage_scope():
    sources={s['id']:s for s in locator.load_sources()}
    coverage={c['fips']:c for c in locator.load_coverage()}
    assert {'fulton_water','atlanta','forsyth','smyrna'}<=sources.keys()
    assert 'atlanta' in coverage['13121']['source_ids']
    assert 'fulton_water' in coverage['13121']['source_ids']
    assert coverage['13067']['source_ids']=='smyrna'
    assert 'Smyrna' in coverage['13067']['scope']
    assert 'only' in coverage['13067']['scope']
    assert coverage['13117']['source_ids']=='forsyth'
    assert sources['forsyth']['status_filter']['include']==['Active']
    assert sources['atlanta']['status_filter']['include']==['INSRV']
    assert 'A' in sources['fulton_water']['status_filter']['exclude']
    assert len([s for s in sources.values() if 'WaterResources' in s['url']])==1


def test_filter_sql_and_null_handling():
    assert locator.source_where(SOURCE)=="STATE IN ('Active')"
    excluded={**SOURCE,'status_filter':{'field':'STATE','exclude':['Abandoned']}}
    assert 'IS NULL' in locator.source_where(excluded)
    assert locator.accepted_status(excluded,{'STATE':None})
    assert not locator.accepted_status(excluded,{'STATE':'Abandoned'})
    assert not locator.accepted_status(SOURCE,{'STATE':None})
    assert not locator.accepted_status(excluded,{})


def test_missing_filter_field_rejected_before_query():
    def fetch(url,params=None):
        assert params is None
        return {'geometryType':'esriGeometryPoint','objectIdField':'OID','fields':[]}
    with pytest.raises(locator.LookupError,match='schema changed'):
        locator.query_source(SOURCE,-83,34,5280,fetch)


@pytest.mark.parametrize('state',['Inactive',None])
def test_service_must_honor_status_filter(state):
    def fetch(url,params=None):
        if params is None:return {'geometryType':'esriGeometryPoint','objectIdField':'OID','fields':[{'name':'STATE'}]}
        if params.get('returnIdsOnly'):
            assert params['where']=="STATE IN ('Active')"
            return {'objectIds':[1]}
        assert 'STATE' in params['outFields'] and '*' not in params['outFields']
        return {'spatialReference':{'wkid':4326},'features':[{'attributes':{'OID':1,'STATE':state},'geometry':{'x':-83,'y':34}}]}
    with pytest.raises(locator.LookupError,match='status'):
        locator.query_source(SOURCE,-83,34,5280,fetch)


@pytest.mark.parametrize('has_inner_candidate',[True,False])
def test_dense_query_preserves_nearest_proof(monkeypatch,has_inner_candidate):
    monkeypatch.setattr(locator,'MAX_RECORDS',2)
    source={k:v for k,v in SOURCE.items() if k!='status_filter'}
    source['adaptive_radius']=True
    calls=[]
    def fetch(url,params=None):
        if params is None:return {'geometryType':'esriGeometryPoint','objectIdField':'OID'}
        if params.get('returnIdsOnly'):
            e=json.loads(params['geometry']);width=e['xmax']-e['xmin'];calls.append(width)
            return {'objectIds':[1,2,3] if len(calls)==1 else [1] if has_inner_candidate else []}
        x,y,_=locator.GEOD.fwd(-83,34,90,30.48)
        return {'spatialReference':{'wkid':4326},'features':[{'attributes':{'OID':1},'geometry':{'x':x,'y':y}}]}
    if has_inner_candidate:
        r=locator.query_source(source,-83,34,5280,fetch)
        assert r['candidates'][0]['distance_ft']==pytest.approx(100)
        assert r['nearby_inventory_limited'] and r['requested_radius_ft']==5280
        assert r['searched_radius_ft']==2640 and calls[1]<calls[0]
    else:
        with pytest.raises(locator.LookupError,match='Too many records'):
            locator.query_source(source,-83,34,5280,fetch)


def test_dense_query_recursion_is_bounded(monkeypatch):
    monkeypatch.setattr(locator,'MAX_RECORDS',1)
    source={'id':'synthetic','name':'Synthetic','url':'https://example.invalid/0','adaptive_radius':True}
    calls=[]
    def fetch(url,params=None):
        if params is None:return {'geometryType':'esriGeometryPoint','objectIdField':'OID'}
        calls.append(params)
        return {'objectIds':[1,2]}
    with pytest.raises(locator.LookupError):locator.query_source(source,-83,34,5280,fetch)
    assert len(calls)==6
