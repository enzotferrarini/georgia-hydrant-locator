from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_initial_ui():
    app=AppTest.from_file(str(Path(__file__).parents[1]/'app.py')).run(timeout=30)
    assert not app.exception
    assert app.title[0].value=='Georgia Fire Hydrant Locator'
    assert app.text_input[0].value==''
    assert len(app.tabs)==3
    assert app.metric[0].value=='10 / 159'

def test_lookup_flow(monkeypatch):
    import locator
    import json
    matches=locator.parse_matches(json.loads((locator.DATA/'geocode.json').read_text()))
    monkeypatch.setattr(locator,'geocode',lambda _:matches)
    result={'address':matches[0],'radius_ft':26400,'complete':True,'nearest':None,'candidates':[],
            'sources':[], 'scope':'test','status':'no_mapped_result'}
    monkeypatch.setattr(locator,'locate',lambda *args:result)
    app=AppTest.from_file(str(Path(__file__).parents[1]/'app.py')).run(timeout=30)
    app.button[0].click().run(timeout=30)
    assert not app.exception
    next(b for b in app.button if b.label=='Search near this address').click().run(timeout=30)
    assert not app.exception
    assert any('not proof' in w.value for w in app.warning)

def test_found_result_and_new_search_clear_stale_result(monkeypatch):
    import locator
    import json
    result=json.loads((locator.DATA/'example_result.json').read_text())
    monkeypatch.setattr(locator,'geocode',lambda _:[result['address']])
    monkeypatch.setattr(locator,'locate',lambda *args:result)
    app=AppTest.from_file(str(Path(__file__).parents[1]/'app.py')).run(timeout=30)
    app.button[0].click().run(timeout=30)
    next(b for b in app.button if b.label=='Search near this address').click().run(timeout=30)
    assert not app.exception
    assert any(m.value=='2,800 ft' for m in app.metric)
    def fail(_): raise locator.LookupError('No Georgia match')
    monkeypatch.setattr(locator,'geocode',fail)
    app.button[0].click().run(timeout=30)
    assert not app.exception
    assert app.error[0].value=='No Georgia match'
    assert not any(m.value=='2,800 ft' for m in app.metric)
