import copy
import hashlib
import json
import pytest
import locator
import historical
from streamlit.testing.v1 import AppTest


def walton():
    return next(s for s in locator.load_sources() if s['id']=='walton_historical')


def test_historical_saved_point_uses_geodesic_radius_and_stays_partial():
    source=walton()
    row=json.loads((locator.DATA/'historical/walton-historical.json').read_text())[0]
    result=locator.locate({'lon':row[1],'lat':row[2]},1,sources=[source])
    assert result['nearest']['distance_ft']==0
    assert result['nearest']['publisher_verified'] is False
    assert result['status']=='partial' and not result['complete']
    assert result['sources'][0]['source_data_updated_at'].startswith('2022-06-02')
    assert result['sources'][0]['historical_record_count']==3776
    x,y,_=locator.GEOD.fwd(row[1],row[2],90,30.48)
    assert historical.query_historical(source,x,y,101)['candidates'][0]['distance_ft']==pytest.approx(100,abs=.001)
    assert not historical.query_historical(source,-85,34,1)['candidates']


@pytest.mark.parametrize('case',['corrupt','missing','duplicate','bad_geometry','wrong_source','wrong_date'])
def test_historical_corruption_and_provenance_fail_closed(tmp_path,case):
    source=copy.deepcopy(walton())
    rows=[[1,-83.7,33.8]]
    if case=='duplicate':rows*=2
    if case=='bad_geometry':rows[0][1]=0
    raw=json.dumps(rows).encode()
    source['sha256']=hashlib.sha256(raw).hexdigest()
    meta={'schema_version':1,'publisher_verified':False,'complete_embedded_collection':True,
          'record_count':len(rows),'sha256':source['sha256'],'source_id':source['id'],
          'source_url':source['url'],'source_data_updated_at':source['source_data_updated_at'],'downloaded_at':'2026-10-23T00:00:00+00:00'}
    if case=='wrong_source':meta['source_url']='https://example.invalid'
    if case=='wrong_date':meta['source_data_updated_at']='2026-10-23'
    if case!='missing':(tmp_path/'walton-historical.json').write_bytes(b'corrupt' if case=='corrupt' else raw)
    (tmp_path/'walton-historical.manifest.json').write_text(json.dumps(meta))
    with pytest.raises(locator.LookupError):historical.query_historical(source,-83.7,33.8,5280,tmp_path)


@pytest.mark.parametrize('bad_field',['ACTIVEFLAG','ENABLED','OPERABLE'])
def test_compound_hall_filter_enforced_by_client_and_sql(bad_field):
    source=next(s for s in locator.load_sources() if s['id']=='hall_gainesville')
    expected='ACTIVEFLAG IN (1) AND ENABLED IN (1) AND OPERABLE IN (1)'
    assert locator.source_where(source)==expected
    attrs={'OID':1,'ACTIVEFLAG':1,'ENABLED':1,'OPERABLE':1};attrs[bad_field]=0
    def fetch(url,params=None):
        if params is None:return {'geometryType':'esriGeometryPoint','objectIdField':'OID','fields':[{'name':k} for k in attrs]}
        if params.get('returnIdsOnly'):
            assert params['where']==expected
            return {'objectIds':[1]}
        assert all(k in params['outFields'] for k in attrs)
        return {'spatialReference':{'wkid':4326},'features':[{'attributes':attrs,'geometry':{'x':-83.8,'y':34.2}}]}
    with pytest.raises(locator.LookupError,match='status'):locator.query_source(source,-83.8,34.2,5280,fetch)


def test_carnesville_excludes_hydrant_valves():
    source=next(s for s in locator.load_sources() if s['id']=='franklin_carnesville')
    assert locator.accepted_status(source,{'Type':'Hydrant'})
    assert not locator.accepted_status(source,{'Type':'Hydrant Valve'})


def test_optional_toggle_clears_previous_results_and_changes_selected_sources(monkeypatch):
    match=json.loads((locator.DATA/'example_result.json').read_text())['address']
    match.update(county_fips='13297',county='Walton County')
    monkeypatch.setattr(locator,'geocode',lambda _:[match])
    monkeypatch.setattr(locator,'barrow_address_options',lambda _:[])
    calls=[]
    def locate(m,r,sources=None):
        calls.append(sources)
        return {'address':m,'radius_ft':r,'complete':True,'nearest':None,'candidates':[],'sources':[]}
    monkeypatch.setattr(locator,'locate',locate)
    app=AppTest.from_file(str(locator.DATA.parent/'app.py')).run(timeout=30)
    assert not app.toggle(key='include_historical_walton').value
    app.text_input(key='address_input').set_value('100 SYNTHETIC TEST RD, TESTVILLE, GA, 00000')
    next(b for b in app.button if b.label=='Locate address').click().run(timeout=30)
    assert any('optional June 2022' in w.value for w in app.warning)
    next(b for b in app.button if b.label=='Search near this address').click().run(timeout=30)
    assert calls==[None] and 'result' in app.session_state
    app.toggle(key='include_historical_walton').set_value(True).run(timeout=30)
    assert 'result' not in app.session_state
    app.session_state['last_request_hydrants']=-100
    next(b for b in app.button if b.label=='Search near this address').click().run(timeout=30)
    assert any(s['id']=='walton_historical' for s in calls[-1])
    assert not app.exception
