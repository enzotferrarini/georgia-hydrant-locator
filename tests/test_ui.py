import copy
import json
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
    monkeypatch.setattr(locator,'locate',lambda *args:copy.deepcopy(result))
    app=AppTest.from_file(APP).run(timeout=30)
    app.text_input(key='address_input').set_value('100 SYNTHETIC TEST RD, TESTVILLE, GA, 00000')
    click(app,'Locate address')
    app.session_state['last_request']=-100
    return app,result


def test_initial_ui_blank():
    app=AppTest.from_file(APP).run(timeout=30)
    assert not app.exception
    assert app.text_input(key='address_input').value==''
    assert app.text_input(key='address_input').placeholder=='Enter a Georgia street address'
    assert app.metric[0].value=='10 / 159'


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


def test_manual_map_correction_clears_result(setup,monkeypatch):
    import streamlit_folium
    app,result=setup
    click(app,'Search near this address')
    monkeypatch.setattr(streamlit_folium,'st_folium',lambda *a,**k:{'last_clicked':{'lat':33.5001,'lng':-83.5}})
    seen=[]
    def correction(original,lon,lat):
        seen.append((lon,lat)); return {**original,'lon':lon,'lat':lat,'provider':'User-selected map point'}
    monkeypatch.setattr(locator,'corrected_origin',correction)
    app.checkbox[0].check().run(timeout=30)
    app.session_state['last_request']=-100
    click(app,'Apply corrected point')
    assert seen==[(-83.5,33.5001)]
    assert app.session_state['origin']['lat']==33.5001
    assert 'result' not in app.session_state
    assert not any(m.value=='100 ft' for m in app.metric)
    queried=[]
    monkeypatch.setattr(locator,'locate',lambda match,*a:queried.append(match) or {**result,'address':match})
    app.session_state['last_request']=-100
    click(app,'Search near this address')
    assert queried[0]['lat']==33.5001


def test_throttle_prevents_repeated_query(setup,monkeypatch):
    app,result=setup
    app.session_state['last_request']=__import__('time').monotonic()
    monkeypatch.setattr(locator,'locate',lambda *a:pytest.fail('Repeated network lookup'))
    click(app,'Search near this address')
    assert any('10 seconds' in x.value for x in app.error)


def test_new_failed_search_clears_old_result(setup,monkeypatch):
    app,_=setup
    click(app,'Search near this address')
    def fail(_): raise locator.LookupError('No Georgia match')
    monkeypatch.setattr(locator,'geocode',fail)
    app.session_state['last_request']=-100
    click(app,'Locate address')
    assert 'result' not in app.session_state
    assert any('No Georgia match' in x.value for x in app.error)
