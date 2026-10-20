from datetime import datetime, timezone, timedelta
import gzip
import hashlib
import json
import pytest
import locator
import snapshots
from refresh_snapshot import download

SOURCE={'id':'gwinnett','name':'Synthetic source','url':'https://example.invalid/0','scope':'Synthetic only'}
ORIGIN={'lon':-83.5,'lat':33.5,'address':'SYNTHETIC','provider':'Synthetic'}


def write_snapshot(folder,age=0,rows=None):
    rows=rows if rows is not None else [[1,-83.5,33.5,None],[2,-83.501,33.5,None]]
    payload=gzip.compress(json.dumps(rows).encode())
    (folder/'gwinnett.json.gz').write_bytes(payload)
    meta={'schema_version':1,'source_id':SOURCE['id'],'source_url':SOURCE['url'],
          'downloaded_at':(datetime.now(timezone.utc)-timedelta(days=age)).isoformat(),
          'sha256':hashlib.sha256(payload).hexdigest(),'record_count':len(rows),
          'complete_published_id_set':True}
    (folder/'gwinnett.manifest.json').write_text(json.dumps(meta))


def test_snapshot_correct_distance_and_radius(tmp_path):
    write_snapshot(tmp_path)
    r=snapshots.query_snapshot(SOURCE,-83.5,33.5,100,folder=tmp_path)
    assert r['is_snapshot'] and r['snapshot_record_count']==2
    assert len(r['candidates'])==1 and r['candidates'][0]['distance_ft']==0
    assert r['error'] is None


@pytest.mark.parametrize('case',['missing','checksum','stale','duplicate','geometry','wrong_source'])
def test_invalid_snapshots_fail_closed(tmp_path,case):
    if case!='missing':write_snapshot(tmp_path,age=91 if case=='stale' else 0,
        rows=[[1,-83.5,33.5,None]]*2 if case=='duplicate' else [[1,0,0,None]] if case=='geometry' else None)
    if case=='checksum':(tmp_path/'gwinnett.json.gz').write_bytes(b'corrupt')
    source={**SOURCE,'url':'https://example.invalid/other'} if case=='wrong_source' else SOURCE
    with pytest.raises(locator.LookupError):snapshots.query_snapshot(source,-83.5,33.5,5280,folder=tmp_path)


def test_live_failure_uses_backup_and_stays_partial(tmp_path,monkeypatch):
    write_snapshot(tmp_path)
    real=snapshots.query_snapshot
    monkeypatch.setattr(snapshots,'query_snapshot',lambda s,x,y,r:real(s,x,y,r,folder=tmp_path))
    def fail(*a):raise locator.LookupError('Service unavailable')
    r=locator.locate(ORIGIN,5280,sources=[SOURCE],query=fail)
    assert r['status']=='partial' and not r['complete']
    assert r['nearest']['distance_ft']==0
    assert r['sources'][0]['live_error']=='Service unavailable'


def test_live_success_does_not_read_backup(monkeypatch):
    monkeypatch.setattr(snapshots,'query_snapshot',lambda *a:pytest.fail('Backup must not override live success'))
    def query(*a):return {'source_id':'gwinnett','error':None,'candidates':[]}
    r=locator.locate(ORIGIN,5280,sources=[SOURCE],query=query)
    assert r['complete'] and r['nearest'] is None


def test_packaged_inventory_validates_and_recovers_known_point():
    source=next(s for s in locator.load_sources() if s['id']=='gwinnett')
    folder=locator.DATA/'snapshots'
    meta=json.loads((folder/'gwinnett.manifest.json').read_text())
    rows=json.loads(gzip.decompress(b''.join((folder/name).read_bytes() for name in meta['parts'])))
    r=snapshots.query_snapshot(source,rows[0][1],rows[0][2],5280)
    assert r['snapshot_record_count']==len(rows)
    assert r['candidates'][0]['distance_ft']==0


def test_download_rejects_incomplete_batch():
    def fetch(url,params=None):
        if params is None:return {'geometryType':'esriGeometryPoint','objectIdField':'OID'}
        if params.get('returnIdsOnly'):return {'objectIds':[1,2]}
        return {'spatialReference':{'wkid':4326},'features':[{'attributes':{'OID':1},'geometry':{'x':-83.5,'y':33.5}}]}
    with pytest.raises(locator.LookupError):download(SOURCE,fetch)
