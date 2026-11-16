"""Record HTTP observations; a 200 response does not prove source content."""
import concurrent.futures
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
pages = [ROOT / 'README.md', * (ROOT / 'docs').glob('*.md')]
urls = sorted({u.split('#')[0] for p in pages for u in re.findall(r'\]\((https?://[^\s)]+)\)', p.read_text(encoding='utf-8'))})
def check(url):
    try:
        with urlopen(Request(url, headers={'User-Agent': 'IS373-research-link-check/1.0'}), timeout=15) as r:
            final = r.url
            if 'login.njit.edu' in final:
                parts = urlsplit(final)
                final = urlunsplit((parts.scheme, parts.netloc, parts.path, '', ''))
            return {'url': url, 'status': r.status, 'final_url': final}
    except HTTPError as e:
        return {'url': url, 'status': e.code, 'final_url': e.url}
    except Exception as e:
        return {'url': url, 'error': str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(check, urls))
output = ROOT / 'docs/checks/external-links.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'method': 'GET, redirects followed, 15 second timeout; availability only', 'results': results}, indent=2), encoding='utf-8')
print(f'Checked {len(results)} distinct external URLs')
for r in results:
    if r.get('status') != 200 or r.get('final_url') != r['url']:
        print(json.dumps(r))
