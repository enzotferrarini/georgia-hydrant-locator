"""Download a complete public Gwinnett point snapshot; never stores user searches."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import gzip
import hashlib
import json
from locator import get_json, load_sources, valid_point, now, timestamp, LookupError

TARGET = Path(__file__).parent / 'data' / 'snapshots'


def download(source, fetch=get_json):
    meta = fetch(source['url'])
    if meta.get('geometryType') != 'esriGeometryPoint':
        raise LookupError('Snapshot source must be a point layer.')
    oid = meta['objectIdField']
    query = source['url'] + '/query'
    ids_response = fetch(query, {'where':'1=1', 'returnIdsOnly':'true'})
    ids = ids_response.get('objectIds')
    if (not isinstance(ids, list) or not ids or len(ids) != len(set(ids))
            or any(type(i) is not int for i in ids) or ids_response.get('exceededTransferLimit')):
        raise LookupError('Snapshot ID list is incomplete.')
    if len(ids) > 100000:
        raise LookupError('Snapshot exceeds record safety limit.')
    ids.sort()
    size = max(1, min(1000, int(meta.get('maxRecordCount') or 200)))
    date = source.get('date_field')
    fields = oid + (',' + date if date else '')

    def batch(part):
        data = fetch(query, {'objectIds':','.join(map(str,part)), 'outFields':fields,
                             'returnGeometry':'true','outSR':4326})
        sr = data.get('spatialReference', {})
        features = data.get('features', [])
        if (sr.get('latestWkid',sr.get('wkid')) != 4326 or data.get('exceededTransferLimit')
                or len(features) != len(part)
                or {f.get('attributes',{}).get(oid) for f in features} != set(part)):
            raise LookupError('Incomplete snapshot feature batch.')
        rows=[]
        for f in features:
            g=f.get('geometry') or {}; a=f['attributes']
            if not valid_point(g.get('x'),g.get('y')) or not (-86 <= g['x'] <= -80 and 29 <= g['y'] <= 36):
                raise LookupError('Invalid snapshot geometry.')
            rows.append([a[oid],g['x'],g['y'],a.get(date)])
        return rows

    with ThreadPoolExecutor(max_workers=4) as pool:
        rows=[row for part in pool.map(batch,[ids[i:i+size] for i in range(0,len(ids),size)]) for row in part]
    final=fetch(query, {'where':'1=1','returnIdsOnly':'true'})
    final_meta=fetch(source['url'])
    if (final.get('exceededTransferLimit') or sorted(final.get('objectIds') or []) != ids
            or final_meta.get('editingInfo') != meta.get('editingInfo')):
        raise LookupError('Source changed during snapshot download; retry.')
    rows.sort(key=lambda r:r[0])
    payload=gzip.compress(json.dumps(rows,separators=(',',':')).encode(),mtime=0)
    edited=meta.get('editingInfo') or {}
    manifest={'schema_version':1,'source_id':source['id'],'source_url':source['url'],
              'downloaded_at':now(),'source_data_updated_at':timestamp(edited.get('dataLastEditDate') or edited.get('lastEditDate')),
              'record_count':len(rows),'sha256':hashlib.sha256(payload).hexdigest(),
              'columns':['object_id','longitude','latitude','feature_updated_ms'],
              'scope':source['scope'],'complete_published_id_set':True}
    return payload,manifest


if __name__ == '__main__':
    source=next(s for s in load_sources() if s['id']=='gwinnett')
    payload,manifest=download(source)
    TARGET.mkdir(exist_ok=True)
    # All remote retrieval/validation finishes before replacing the last good copy.
    parts=[]
    for index,start in enumerate(range(0,len(payload),16000)):
        name=f'gwinnett.part{index:03d}'
        (TARGET/name).write_bytes(payload[start:start+16000])
        parts.append(name)
    manifest['parts']=parts
    (TARGET/'gwinnett.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    for old in TARGET.glob('gwinnett.part*'):
        if old.name not in parts:old.unlink()
    print(json.dumps({'source':'gwinnett','records':manifest['record_count'],'downloaded_at':manifest['downloaded_at'],'bytes':len(payload)}))
