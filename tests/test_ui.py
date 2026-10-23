import copy
import json
import time
from pathlib import Path
import pytest
import locator
from streamlit.testing.v1 import AppTest
APP=str(Path(__file__).parents[1]/'app.py')

def click(app,label):
    next(b for b in app.button if b.label==label).click().run(timeout=30)
    assert not app.exception
    return app

@pytest.fixture
def setup(monkeypatch):
    result=json.loads((locator.DATA/'example_result.json').read_text())
    monkeypatch.setattr(locator,'geocode',lambda _:[copy.deepcopy(result['address'])])
    monkeypatch.setattr(locator,'barrow_address_options',lambda _:[])
    monkeypatch.setattr(locator,'locate',lambda match,radius:{**copy.deepcopy(result),'address':copy.deepcopy(match),'radius_ft':radius})
    app=AppTest.from_file(APP).run(timeout=30)
    app.text_input(key='address_input').set_value('100 SYNTHETIC TEST RD, TESTVILLE, GA, 00000')
    click(app,'Locate address')
    app.select_slider[0].set_value(result['radius_ft']//5280).run(timeout=30)
    return app,result


def test_initial_ui_blank():
    app=AppTest.from_file(APP).run(timeout=30)
    assert not app.exception
    assert app.text_input(key='address_input').value==''
    assert app.text_input(key='address_input').placeholder=='Enter a Georgia street address'
    assert app.metric[0].value=='14 / 159'

@pytest.mark.parametrize('fips, county', [('13195', 'Madison County'), ('13221', 'Oglethorpe County')])
def test_unverified_county_search_explains_local_gap(monkeypatch, fips, county):
    match = json.loads((locator.DATA/'example_result.json').read_text())['address']
    match.update(county_fips=fips, county=county)
    monkeypatch.setattr(locator, 'geocode', lambda _: [copy.deepcopy(match)])
    monkeypatch.setattr(locator, 'barrow_address_options', lambda _: [])
    app = AppTest.from_file(APP).run(timeout=30)
    app.text_input(key='address_input').set_value('100 SYNTHETIC TEST RD, TESTVILLE, GA, 00000')
    click(app, 'Locate address')
    assert any('No local source is integrated' in w.value for w in app.warning)
    assert any('no official public hydrant point inventory verified' in c.value.lower() and 'Last reviewed:' in c.value for c in app.caption)
    assert app.metric[0].value == '14 / 159'


def test_blank_submit_rejected_without_network(monkeypatch):
    monkeypatch.setattr(locator,'get_json',lambda *a:pytest.fail('No network for blank input'))
    app=AppTest.from_file(APP).run(timeout=30)
    click(app,'Locate address')
    assert any('full street address' in x.value for x in app.error)


def test_found_and_clear_session(setup):
    app,result=setup
    app.select_slider[0].set_value(1)
    click(app,'Search near this address')
    assert any(m.value=='100 ft' for m in app.metric)
    assert any('county-owned' in w.value for w in app.warning)
    click(app,'Clear this session')
    assert app.text_input(key='address_input').value==''
    assert not any(m.value=='100 ft' for m in app.metric)


def test_no_result_is_not_absence(setup,monkeypatch):
    app,result=setup
    result.update(nearest=None,candidates=[])
    monkeypatch.setattr(locator,'locate',lambda *args:result)
    click(app,'Search near this address')
    assert any('not proof' in x.value for x in app.warning)


def test_backup_date_and_partial_warning_visible(setup,monkeypatch):
    app,result=setup
    result.update(complete=False,status='partial')
    report={'name':'Synthetic source','url':'https://example.invalid','error':None,
            'ids_checked':2,'source_data_updated_at':None,'retrieved_at':'2026-10-20'}
    result['sources']=[report]
    report.update(is_snapshot=True,snapshot_downloaded_at='2026-10-20T00:00:00+00:00',
                  snapshot_age_days=1,live_error='Service unavailable')
    monkeypatch.setattr(locator,'locate',lambda *args:result)
    click(app,'Search near this address')
    assert any('dated backup' in w.value for w in app.warning)
    assert any('2026-10-20' in w.value and 'backup downloaded' in w.value for w in app.warning)


def test_manual_map_correction_previews_and_recalculates(setup,monkeypatch):
    import streamlit_folium
    app,result=setup
    click(app,'Search near this address')
    maps=[]
    def map_click(*a,**kwargs):
        maps.append(kwargs)
        return {'last_clicked':{'lat':33.5001,'lng':-83.5}}
    monkeypatch.setattr(streamlit_folium,'st_folium',map_click)
    seen=[]
    def correction(original,lon,lat):
        seen.append((lon,lat)); return {**original,'lon':lon,'lat':lat,'provider':'User-selected map point'}
    monkeypatch.setattr(locator,'corrected_origin',correction)
    app.checkbox[0].check().run(timeout=30)
    assert any('previous distance is hidden' in w.value for w in app.warning)
    assert not any(m.value=='100 ft' for m in app.metric)
    assert maps[-1]['key']==maps[-2]['key']
    marker=next(iter(maps[-1]['feature_group_to_add']._children.values()))
    assert marker.location==[33.5001,-83.5]
    queried=[]
    monkeypatch.setattr(locator,'locate',lambda match,radius:queried.append((match,radius)) or {**result,'address':match})
    click(app,'Use this point and recalculate')
    assert seen==[(-83.5,33.5001)]
    assert app.session_state['origin']['lat']==33.5001
    assert queried[0][0]['lat']==33.5001
    assert queried[0][1]==5280
    assert app.session_state['result']['address']==app.session_state['origin']
    assert 'pending_point' not in app.session_state
    assert not app.checkbox[0].value
    assert any(m.value=='100 ft' for m in app.metric)
    assert any('your selected starting point' in s.value for s in app.success)


def test_move_button_requires_map_selection(setup):
    app,_=setup
    app.checkbox[0].check().run(timeout=30)
    button=next(b for b in app.button if b.label=='Use this point and recalculate')
    assert button.disabled


def test_cancel_point_restores_current_distance(setup,monkeypatch):
    import streamlit_folium
    app,result=setup
    click(app,'Search near this address')
    monkeypatch.setattr(streamlit_folium,'st_folium',lambda *a,**k:{'last_clicked':{'lat':33.5001,'lng':-83.5}})
    app.checkbox[0].check().run(timeout=30)
    assert not any(m.value=='100 ft' for m in app.metric)
    monkeypatch.setattr(locator,'locate',lambda *a:pytest.fail('Cancel must not query'))
    click(app,'Cancel selected point')
    assert app.session_state['result']==result
    assert 'pending_point' not in app.session_state
    assert any(m.value=='100 ft' for m in app.metric)


@pytest.mark.parametrize('failure',['validation','search'])
def test_failed_point_recalculation_keeps_original_state(setup,monkeypatch,failure):
    import streamlit_folium
    app,result=setup
    click(app,'Search near this address')
    original=copy.deepcopy(app.session_state['origin'])
    monkeypatch.setattr(streamlit_folium,'st_folium',lambda *a,**k:{'last_clicked':{'lat':33.5001,'lng':-83.5}})
    app.checkbox[0].check().run(timeout=30)
    def reject(*a): raise locator.LookupError('Synthetic point check failed')
    if failure=='validation':
        monkeypatch.setattr(locator,'corrected_origin',reject)
        monkeypatch.setattr(locator,'locate',lambda *a:pytest.fail('Invalid point must not query'))
    else:
        monkeypatch.setattr(locator,'corrected_origin',lambda m,x,y:{**m,'lon':x,'lat':y})
        monkeypatch.setattr(locator,'locate',reject)
    click(app,'Use this point and recalculate')
    assert app.session_state['origin']==original
    assert app.session_state['result']==result
    assert app.session_state['pending_point']
    assert not any(m.value=='100 ft' for m in app.metric)
    assert any('Synthetic point check failed' in e.value for e in app.error)


def test_point_move_can_change_which_hydrant_is_nearest(setup,monkeypatch):
    import streamlit_folium
    app,result=setup
    origin=result['address']
    a=locator.GEOD.fwd(origin['lon'],origin['lat'],0,50*.3048)
    b=locator.GEOD.fwd(origin['lon'],origin['lat'],180,100*.3048)
    moved=locator.GEOD.fwd(origin['lon'],origin['lat'],180,110*.3048)
    queried=[]
    def rank(match,radius):
        queried.append(match.copy())
        points=[{**result['nearest'],'object_id':oid,'lon':x,'lat':y,
                 'distance_ft':locator.distance_feet(match['lon'],match['lat'],x,y)}
                for oid,(x,y,_) in [('SYNTHETIC-A',a),('SYNTHETIC-B',b)]]
        points.sort(key=lambda p:p['distance_ft'])
        return {**result,'address':match,'radius_ft':radius,'nearest':points[0],'candidates':points,'candidate_count':2}
    monkeypatch.setattr(locator,'locate',rank)
    click(app,'Search near this address')
    assert app.session_state['result']['nearest']['object_id']=='SYNTHETIC-A'
    monkeypatch.setattr(streamlit_folium,'st_folium',lambda *a,**k:{'last_clicked':{'lat':moved[1],'lng':moved[0]}})
    monkeypatch.setattr(locator,'corrected_origin',lambda m,x,y:{**m,'lon':x,'lat':y,'provider':'User-selected map point'})
    app.checkbox[0].check().run(timeout=30)
    click(app,'Use this point and recalculate')
    assert len(queried)==2
    assert app.session_state['result']['nearest']['object_id']=='SYNTHETIC-B'
    assert app.session_state['result']['nearest']['distance_ft']==pytest.approx(10)
    assert any(m.value=='10 ft' for m in app.metric)


def test_address_then_hydrant_search_needs_no_wait(setup):
    app,_=setup
    click(app,'Search near this address')
    assert not app.error
    assert any(m.value=='100 ft' for m in app.metric)


def test_throttle_prevents_repeated_query_and_preserves_result(setup,monkeypatch):
    app,result=setup
    click(app,'Search near this address')
    app.session_state['last_request_hydrants']=time.monotonic()
    monkeypatch.setattr(locator,'locate',lambda *a:pytest.fail('Repeated network lookup'))
    click(app,'Search near this address')
    assert any('5 seconds' in x.value for x in app.error)
    assert app.session_state['result']==result
    assert any(m.value=='100 ft' for m in app.metric)


def test_query_allowed_after_five_seconds(setup,monkeypatch):
    app,result=setup
    app.session_state['last_request_hydrants']=time.monotonic()-5
    queried=[]
    monkeypatch.setattr(locator,'locate',lambda *a:queried.append(a) or result)
    click(app,'Search near this address')
    assert len(queried)==1
    assert not app.error


def test_throttled_address_keeps_match_and_result(setup,monkeypatch):
    app,result=setup
    click(app,'Search near this address')
    app.session_state['last_request_address']=time.monotonic()
    monkeypatch.setattr(locator,'geocode',lambda *a:pytest.fail('Repeated address lookup'))
    click(app,'Locate address')
    assert any('5 seconds' in x.value for x in app.error)
    assert app.session_state['result']==result
    assert app.session_state['matches']
    assert any(m.value=='100 ft' for m in app.metric)


def test_new_failed_search_clears_old_result(setup,monkeypatch):
    app,_=setup
    click(app,'Search near this address')
    def fail(_): raise locator.LookupError('No Georgia match')
    monkeypatch.setattr(locator,'geocode',fail)
    app.session_state['last_request_address']=-100
    click(app,'Locate address')
    assert 'result' not in app.session_state
    assert any('No Georgia match' in x.value for x in app.error)


@pytest.mark.parametrize('fips,county,phrase',[
    ('13121','Fulton County','North Fulton'),
    ('13067','Cobb County','Smyrna'),
    ('13117','Forsyth County','Existing/Active')])
def test_new_county_scope_messages(setup,monkeypatch,fips,county,phrase):
    app,result=setup
    match={**result['address'],'county_fips':fips,'county':county}
    monkeypatch.setattr(locator,'geocode',lambda _:[match])
    app.session_state['last_request_address']=-100
    click(app,'Locate address')
    assert any(phrase in w.value for w in list(app.warning)+list(app.caption))
