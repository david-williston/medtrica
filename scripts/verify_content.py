#!/usr/bin/env python3
"""Audit imported product paragraphs, table rows and option values against source HTML."""
import json,re
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse
crawl=json.loads(Path('/private/tmp/medtrica-crawl/inventory.json').read_text())
manifest=json.loads(Path('migration/pages.json').read_text())
by_source={p['url']:p for p in manifest if p['kind']=='product'}
errors=[];paragraphs=0;options=0;checked=set()
def norm(t):return re.sub(r'\s+',' ',t).strip()
for d in crawl['pages']:
 if d.get('sitemap')!='product-sitemap.xml' or d['status']!=200:continue
 s=BeautifulSoup(Path(d['cache']).read_bytes(),'html.parser');product=s.select_one('.type-product')
 if not product or not s.body or 'single-product' not in s.body.get('class',[]):continue
 c=s.select_one('link[rel=canonical]');u=c['href'] if c else d['final']
 if u in checked:continue
 checked.add(u);r=by_source.get(u)
 if not r:errors.append((u,'missing product'));continue
 rendered=BeautifulSoup((Path('public')/r['path'].strip('/')/'index.html').read_text(),'html.parser')
 text=norm(rendered.get_text(' ',strip=True))
 for panel in product.select('.woocommerce-product-details__short-description,.woocommerce-Tabs-panel,.procode'):
  for x in panel.select('script,.jp-relatedposts'):x.decompose()
  for p in panel.select('p,tr'):
   value=norm(p.get_text(' ',strip=True))
   if value:
    paragraphs+=1
    if value not in text:errors.append((u,'missing paragraph or table row',value[:200]))
 for p in product.select('form.cart select option'):
  if p.get('value'):
   options+=1;value=norm(p.get_text(' ',strip=True))
   if value not in text:errors.append((u,'missing option',value))
print(f'Compared {len(checked)} products, {paragraphs} paragraphs/table rows and {options} option values against the source.')
print('Errors:',len(errors))
for error in errors[:30]:print(error)
Path('/private/tmp/medtrica-content-errors.json').write_text(json.dumps(errors,indent=2))
raise SystemExit(bool(errors))
