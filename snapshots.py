"""Validated, dated public GIS fallback. Contains no user-entered locations."""
from datetime import datetime, timezone
from functools import lru_cache
import gzip
import hashlib
import json
import zlib
import io
from locator import DATA, LookupError, valid_point, distance_feet, timestamp, now


@lru_cache(maxsize=2)
def _read(path, manifest_path, archive_mtime, manifest_mtime):
    meta=json.loads(manifest_path.read_text(encoding='utf-8'))
    if not isinstance(meta,dict):
        raise ValueError('Invalid snapshot manifest')
    if meta.get('parts'):
        parts=meta['parts']
        if (not isinstance(parts,list) or len(parts)>500 or len(parts)!=len(set(parts))
                or any(name!=f'gwinnett.part{i:03d}' for i,name in enumerate(parts))):
            raise ValueError('Invalid snapshot parts')
        raw=b''.join((manifest_path.parent/name).read_bytes() for name in parts)
    else:
        raw=path.read_bytes()
    if len(raw)>8_000_000 or hashlib.sha256(raw).hexdigest()!=meta.get('sha256'):
        raise ValueError('Snapshot integrity check failed')
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:
        decoded=f.read(16_000_001)
    if len(decoded)>16_000_000:
        raise ValueError('Snapshot exceeds decoded size limit')
    rows=json.loads(decoded)
    if (meta.get('schema_version')!=1 or meta.get('complete_published_id_set') is not True
            or not isinstance(rows,list) or not rows or len(rows)!=meta.get('record_count') or len(rows)>100000):
        raise ValueError('Snapshot inventory validation failed')
    ids=set()
    for row in rows:
        if (not isinstance(row,list) or len(row)!=4 or type(row[0]) is not int or row[0] in ids
                or not valid_point(row[1],row[2]) or not (-86<=row[1]<=-80 and 29<=row[2]<=36)):
            raise ValueError('Snapshot record validation failed')
        ids.add(row[0])
    return meta,rows


def query_snapshot(source,lon,lat,radius_ft,folder=None):
    if source['id']!='gwinnett':
        raise LookupError('No verified backup is configured for this source.')
    folder=folder or DATA/'snapshots'
    archive,manifest=folder/'gwinnett.json.gz',folder/'gwinnett.manifest.json'
    try:
        meta,rows=_read(archive,manifest,archive.stat().st_mtime_ns if archive.exists() else 0,manifest.stat().st_mtime_ns)
        downloaded=datetime.fromisoformat(meta['downloaded_at'])
        age=(datetime.now(timezone.utc)-downloaded).total_seconds()/86400
        if downloaded.tzinfo is None or not 0<=age<=90 or meta['source_id']!=source['id'] or meta['source_url']!=source['url']:
            raise ValueError('Snapshot provenance or freshness check failed')
    except (OSError,ValueError,TypeError,KeyError,EOFError,OverflowError,zlib.error) as exc:
        raise LookupError('The saved backup is missing, invalid, or more than 90 days old.') from exc
    candidates=[]
    for oid,x,y,updated in rows:
        distance=distance_feet(lon,lat,x,y)
        if distance<=radius_ft+0.001:
            candidates.append({'object_id':oid,'lon':x,'lat':y,'distance_ft':distance,
                               'source_id':source['id'],'source_name':source['name'],'source_url':source['url'],
                               'feature_updated_at':timestamp(updated),'snapshot_downloaded_at':meta['downloaded_at']})
    return {'source_id':source['id'],'name':source['name'],'url':source['url'],'retrieved_at':now(),
            'source_data_updated_at':meta.get('source_data_updated_at'),'ids_checked':len(rows),
            'candidates':sorted(candidates,key=lambda p:p['distance_ft']),'error':None,
            'is_snapshot':True,'snapshot_downloaded_at':meta['downloaded_at'],
            'snapshot_age_days':round(age,1),'snapshot_record_count':len(rows)}
