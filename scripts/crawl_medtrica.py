#!/usr/bin/env python3
"""Inventory and cache public Medtrica pages. Requires beautifulsoup4; uses curl."""
import concurrent.futures as futures
import hashlib,json,subprocess,time
from pathlib import Path
from urllib.parse import urlparse,urljoin,urldefrag
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
CACHE=Path('/private/tmp/medtrica-crawl'); CACHE.mkdir(exist_ok=True)
BASE='https://medtrica.com/'

def fetch(url):
 p=CACHE/(hashlib.sha256(url.encode()).hexdigest()+'.body')
 meta=p.with_suffix('.json')
 if p.exists() and meta.exists():return json.loads(meta.read_text()),p
 r=subprocess.run(['curl','-sSL','--retry','1','--retry-delay','1','--max-time','25','--connect-timeout','15','-A','MedtricaContentMigration/1.0','-w','%{http_code}\n%{url_effective}\n%{content_type}','-o',str(p),url],capture_output=True,text=True)
 lines=r.stdout.splitlines()
 d=dict(url=url,status=int(lines[0]) if lines and lines[0].isdigit() else 0,final=lines[1] if len(lines)>1 else url,content_type=lines[2] if len(lines)>2 else '',error=r.stderr.strip())
 if d['status']==200:meta.write_text(json.dumps(d))
 return d,p

def normalize(href,base=BASE):
 u=urlparse(urljoin(base,href.strip()))
 if u.netloc.lower() not in ('medtrica.com','www.medtrica.com'):return None
 if u.query or any(u.path.startswith(x) for x in ['/wp-admin','/dev/','/old-web-bk/','/wp-json','/feed/','/wp-content/']):return None
 if any(u.path.lower().endswith(x) for x in ['.jpg','.jpeg','.png','.gif','.webp','.svg','.pdf','.zip','.doc','.docx','.mp4','.xml','.css','.js','.ico']):return None
 return 'https://medtrica.com'+(u.path or '/')

def main():
 d,p=fetch(BASE+'sitemap_index.xml')
 maps=[x.text for x in ET.fromstring(p.read_bytes()).iter() if x.tag.endswith('}loc')]
 entries={}; sitemap_report=[]
 with futures.ThreadPoolExecutor(max_workers=4) as ex:
  for url,(d,p) in zip(maps,ex.map(fetch,maps)):
   if d['status']!=200: sitemap_report.append(d);continue
   root=ET.fromstring(p.read_bytes()); n=0
   for entry in root:
    loc=next((x.text for x in entry if x.tag.endswith('}loc')),None)
    if loc:
     u=normalize(loc)
     if u:entries[u]=url.split('/')[-1];n+=1
   sitemap_report.append(dict(url=url,entries=n))
 print('Sitemaps:',json.dumps(sitemap_report),flush=True)
 # Attachment pages are inspected separately after canonical content.
 queue=sorted(entries); seen=set(); results=[]
 for round_no in range(12):
  todo=sorted(set(u for u in queue if u not in seen)); queue=[]
  if not todo:break
  print('Round',round_no,'pages',len(todo),flush=True)
  with futures.ThreadPoolExecutor(max_workers=4) as ex:
   for d,p in ex.map(fetch,todo):
    seen.add(d['url']); d['sitemap']=entries.get(d['url'],'linked');d['cache']=str(p);results.append(d)
    if d['status']==200 and 'html' in d['content_type']:
     s=BeautifulSoup(p.read_bytes(),'html.parser')
     for e in s.select('.commentdisplay,#comments,.comments-area,.comment-list,.commentlist,.comment-respond'):e.decompose()
     for a in s.find_all('a',href=True):
      u=normalize(a['href'],d['final'])
      if u and u not in seen:queue.append(u)
    if len(results)%25==0:print('Fetched',len(results),'failures',sum(x['status']!=200 for x in results),flush=True)
  (CACHE/'inventory.json').write_text(json.dumps(dict(sitemaps=sitemap_report,sitemap_entries=entries,pages=results),indent=2))
 # Record attachment URLs as inventory; canonical pages cover their parent content.
 (CACHE/'inventory.json').write_text(json.dumps(dict(sitemaps=sitemap_report,sitemap_entries=entries,pages=results),indent=2))
 api_url=BASE+'wp-json/wp/v2/posts?per_page=100&_fields=id,slug,link,title,content,date,excerpt'
 api_meta,api_path=fetch(api_url)
 if api_meta['status']==200:(CACHE/'posts-api.json').write_bytes(api_path.read_bytes())
 print('DONE',len(results),'pages',flush=True)
if __name__=='__main__':main()
