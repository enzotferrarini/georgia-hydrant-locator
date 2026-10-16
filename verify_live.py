"""Live GIS health check using a published hydrant as origin; no address storage."""
import argparse
import json
from locator import get_json, load_sources, query_source, LookupError


def check(source):
    meta=get_json(source['url'])
    oid=meta.get('objectIdField') or next(f['name'] for f in meta['fields'] if f['type']=='esriFieldTypeOID')
    response=get_json(source['url']+'/query',{'where':'1=1','returnIdsOnly':'true'})
    ids=response.get('objectIds')
    if not isinstance(ids,list) or not ids or response.get('exceededTransferLimit'):
        raise LookupError('No complete nonempty source ID list.')
    row=get_json(source['url']+'/query',{'objectIds':min(ids),'outFields':oid,'returnGeometry':'true','outSR':4326})
    sr=row.get('spatialReference',{})
    if sr.get('latestWkid',sr.get('wkid')) != 4326: raise LookupError('Unexpected spatial reference')
    g=row['features'][0]['geometry']
    result=query_source(source,g['x'],g['y'],5280)
    if not result['candidates'] or result['candidates'][0]['distance_ft'] > .01:
        raise LookupError('Known mapped point was not recovered at zero distance.')
    return {'source':source['id'],'records':len(ids),'spatial_records':result['ids_checked'],
            'nearest_feet':round(result['candidates'][0]['distance_ft'],3),'checked_at':result['retrieved_at']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',help='Optional configured source ID')
    args=parser.parse_args()
    sources=[s for s in load_sources() if not args.source or s['id']==args.source]
    if not sources: parser.error('Unknown source')
    failed=False
    for source in sources:
        try: print(json.dumps(check(source)))
        except (LookupError,KeyError,ValueError,StopIteration,IndexError):
            failed=True
            print(json.dumps({'source':source['id'],'error':'Source verification failed; retry or inspect its public metadata.'}))
    raise SystemExit(1 if failed else 0)
