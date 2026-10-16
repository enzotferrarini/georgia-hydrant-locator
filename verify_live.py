"""Explicit network integration check; not run by the offline test suite."""
import json
from pathlib import Path
from locator import geocode, locate

if __name__ == '__main__':
    match=geocode('558 McCarty Rd, Statham, GA 30666')[0]
    result=locate(match)
    target=Path(__file__).parent/'data'/'example_result.json'
    target.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('candidates',)},indent=2))
    if not result['complete'] or not result['nearest']:
        raise SystemExit('Integration check did not obtain a complete mapped result. See source health above.')
