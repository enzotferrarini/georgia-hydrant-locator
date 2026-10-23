"""Optional dated public-map points, distinct from verified government layers."""
from functools import lru_cache
import hashlib
import json
from locator import DATA, LookupError, distance_feet, now, search_envelope, valid_point


@lru_cache(maxsize=2)
def _read(folder, sha256, rows_mtime, manifest_mtime):
    raw = (folder/'walton-historical.json').read_bytes()
    meta = json.loads((folder/'walton-historical.manifest.json').read_text(encoding='utf-8'))
    if len(raw)>1_000_000 or hashlib.sha256(raw).hexdigest()!=sha256 or meta.get('sha256')!=sha256:
        raise ValueError('Historical map integrity check failed')
    rows = json.loads(raw)
    if (meta.get('schema_version')!=1 or meta.get('publisher_verified') is not False
            or meta.get('complete_embedded_collection') is not True
            or not isinstance(rows,list) or not rows or len(rows)!=meta.get('record_count')):
        raise ValueError('Invalid historical map inventory')
    ids = set()
    for row in rows:
        if (not isinstance(row,list) or len(row)!=3 or type(row[0]) is not int or row[0] in ids
                or not valid_point(row[1],row[2]) or not (-86<row[1]<-80 and 29<row[2]<36)):
            raise ValueError('Invalid historical map point')
        ids.add(row[0])
    return meta, rows


def query_historical(source, lon, lat, radius_ft, folder=None):
    search_envelope(lon,lat,radius_ft)
    if source.get('id')!='walton_historical' or source.get('publisher_verified') is not False:
        raise LookupError('Unknown historical map source.')
    folder = folder or DATA/'historical'
    try:
        meta, rows = _read(folder,source['sha256'],(folder/'walton-historical.json').stat().st_mtime_ns,
                           (folder/'walton-historical.manifest.json').stat().st_mtime_ns)
        if (meta['source_id']!=source['id'] or meta['source_url']!=source['url']
                or meta['source_data_updated_at']!=source['source_data_updated_at']):
            raise ValueError('Historical map provenance mismatch')
    except (OSError,ValueError,TypeError,KeyError) as exc:
        raise LookupError('The optional historical map copy is missing or invalid.') from exc
    candidates = []
    for oid,x,y in rows:
        distance = distance_feet(lon,lat,x,y)
        if distance<=radius_ft+0.001:
            candidates.append({'object_id':oid,'lon':x,'lat':y,'distance_ft':distance,
                               'source_id':source['id'],'source_name':source['name'],'source_url':source['url'],
                               'feature_updated_at':None,'is_historical':True,'publisher_verified':False,
                               'source_data_updated_at':meta['source_data_updated_at'],
                               'dataset_downloaded_at':meta['downloaded_at']})
    return {'source_id':source['id'],'name':source['name'],'url':source['url'],'retrieved_at':now(),
            'source_data_updated_at':meta['source_data_updated_at'],'ids_checked':len(rows),
            'candidates':sorted(candidates,key=lambda p:p['distance_ft']),'error':None,
            'is_historical':True,'publisher_verified':False,'dataset_downloaded_at':meta['downloaded_at'],
            'historical_record_count':len(rows),'historical_caution':source['result_caution']}
