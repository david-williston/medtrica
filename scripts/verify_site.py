#!/usr/bin/env python3
"""Verify generated routes, local links/media, catalog coverage and search URLs."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse,unquote
import json,sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'public')
prefix=sys.argv[2] if len(sys.argv)>2 else '/medtrica/'
errors=[];links=0;images=0
class Check(HTMLParser):
 def __init__(self,path):super().__init__();self.path=path
 def handle_starttag(self,tag,attrs):
  global links,images
  d=dict(attrs)
  for key in ('href','src','poster'):
   value=d.get(key)
   if not value:continue
   links+=1
   if tag=='img' and key=='src':images+=1
   if '{{' in value or '&lt;' in value:errors.append((str(self.path),'unexpanded template',value));continue
   u=urlparse(value)
   if u.scheme in ('mailto','tel','data','javascript'):continue
   if u.netloc:
    if u.netloc in ('medtrica.com','www.medtrica.com'):errors.append((str(self.path),'legacy network link',value))
    if u.netloc!='david-williston.github.io':continue
   path=unquote(u.path)
   if not path:continue
   if path.startswith('/'):
    if not path.startswith(prefix):errors.append((str(self.path),'wrong prefix',value));continue
    target=root/path[len(prefix):]
   else:target=self.path.parent/path
   if not target.exists() and not (target/'index.html').exists():errors.append((str(self.path),'missing',value))
for p in root.rglob('*.html'):Check(p).feed(p.read_text())
index=json.loads((root/'index.json').read_text())
for entry in index:
 if not entry['permalink'].startswith(prefix):errors.append(('search index','nonlocal URL',entry['permalink']))
manifest=json.loads(Path('migration/pages.json').read_text())
for page in manifest:
 p=root/page['path'].strip('/')/'index.html'
 if not p.exists():errors.append(('manifest','missing page',page['path']))
products=[p for p in manifest if p['kind']=='product']
for p in products:
 if not p['images']:errors.append(('product','missing photo',p['path']))
 if p['textCharacters']<50:errors.append(('product','empty description',p['path']))
print(f'Checked {len(list(root.rglob("*.html")))} HTML files, {links} links/media, {images} images, {len(products)} products, {len(index)} search records.')
print('Errors:',len(errors))
for e in errors[:100]:print(e)
Path('/private/tmp/medtrica-link-errors.json').write_text(json.dumps(errors,indent=2))
raise SystemExit(bool(errors))
