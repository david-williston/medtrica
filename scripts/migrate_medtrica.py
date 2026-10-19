#!/usr/bin/env python3
"""Rebuild Hugo content from the public crawl; preserve original text and local media."""
import concurrent.futures as futures
import hashlib,html,json,re,subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin,urlparse,unquote
from bs4 import BeautifulSoup
from crawl_medtrica import CACHE,BASE,fetch
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'migration';REPORT.mkdir(exist_ok=True)
REFERENCE_URLS={
 'health-canada1.html':'https://www.canada.ca/en/health-canada.html',
 'index1.aspx':'https://www.tssa.org/en/index.aspx',
 'www.fda1.gov':'https://www.fda.gov/',
 'mattress-firmness-guide':'https://www.mattressadvisor.com/mattress-firmness-guide/',
 'best-sleep-position':'https://www.sleep.org/best-sleep-position/',
 'best_sleeping_positions_sleep':'https://www.onhealth.com/content/1/best_sleeping_positions_sleep',
 'Intensive_Care_Unit':'https://greysanatomy.fandom.com/wiki/Intensive_Care_Unit',
 'Back-Pain-Facts-and-Statistics':'https://www.acatoday.org/Patients/Health-Wellness-Information/Back-Pain-Facts-and-Statistics'}
ASSETS={}; RECORDS={}; URLS={}; FAILURES=[]
PREVIOUS_ASSETS={d['url']:d for d in json.loads((REPORT/'assets.json').read_text())} if (REPORT/'assets.json').exists() else {}

def pathof(u):return unquote(urlparse(urljoin(BASE,u)).path or '/')
def canonical(u):
 p=urlparse(urljoin(BASE,u));return BASE.rstrip('/')+(p.path or '/')
def internal(u):return urlparse(urljoin(BASE,u)).netloc.lower() in ('medtrica.com','www.medtrica.com')
def media(u):
 u=urljoin(BASE,u)
 if not internal(u):return u
 if u not in ASSETS:
  name=re.sub(r'[^a-zA-Z0-9_.-]','-',unquote(urlparse(u).path.rsplit('/',1)[-1]))
  ASSETS[u]='media/'+hashlib.sha256(u.encode()).hexdigest()[:12]+'-'+name
 return ASSETS[u]
def sitepath(p):return '{{< sitepath '+json.dumps(p.lstrip('/'))+' >}}'
def link(u,base):
 u=urljoin(base,u);p=urlparse(u)
 if p.scheme not in ('http','https'):return u
 if not internal(u):return u
 if '/wp-content/' in p.path:
  if p.path.rsplit('/',1)[-1] in REFERENCE_URLS:return REFERENCE_URLS[p.path.rsplit('/',1)[-1]]
  fixes={'www.fda.gov':'https://www.fda.gov/','health-canada.html':'https://www.canada.ca/en/health-canada.html','index.aspx':'https://www.tssa.org/'}
  if p.path.rsplit('/',1)[-1] in fixes:return fixes[p.path.rsplit('/',1)[-1]]
  local_media=media(u)
  return '' if u in PREVIOUS_ASSETS and PREVIOUS_ASSETS[u]['status']!=200 else sitepath(local_media)
 dest=URLS.get(canonical(u))
 if dest:return sitepath(dest)+(('#'+p.fragment) if p.fragment else '')
 # Unknown original URLs are recorded and resolved after migration.
 FAILURES.append(dict(type='unresolved_internal_link',url=u,source=base))
 return ''

def clean(fragment,base):
 s=BeautifulSoup(str(fragment),'html.parser')
 for e in s.select('script,style,form,noscript,.jp-relatedposts,.sharedaddy,.addtoany_share_save_container,.post-info,.post-cat,.woocommerce-product-rating,.social-share,.comment-respond,.comments-area,.commentdisplay,.post-share'):
  e.decompose()
 for picture in s.find_all('picture'):
  img=picture.find('img');picture.replace_with(img if img else '')
 for e in s.find_all('source'):e.decompose()
 for e in s.find_all(['input','button','select','textarea']):e.decompose()
 for e in s.find_all('iframe'):
  u=e.get('src') or e.get('data-src')
  if u and u.startswith(('http:','https:','//')):
   a=s.new_tag('a',href=u);a.string='Watch the original video';e.replace_with(a)
  else:e.decompose()
 for e in s.find_all('img'):
  src=e.get('data-hq') or e.get('data-src') or e.get('src')
  if not src or src.startswith(('data:','about:')):e.decompose();continue
  fullsrc=urljoin(base,src)
  if fullsrc in PREVIOUS_ASSETS and PREVIOUS_ASSETS[fullsrc]['status']!=200:
   media(fullsrc)
   caption=s.new_tag('span',attrs={'class':'unavailable-media'})
   caption.string=(e.get('alt') or 'Original image')+' — image unavailable on the source website.'
   e.replace_with(caption);continue
  e.attrs={'src':sitepath(media(urljoin(base,src))),'alt':e.get('alt',''),'loading':'lazy','decoding':'async'}
 for e in s.find_all('a',href=True):
  href=link(e['href'],base)
  if not href:e.unwrap()
  else:e['href']=href
 for e in s.find_all(True):
  keep={'href','src','alt','title','id','colspan','rowspan','scope','loading','decoding','width','height'}
  e.attrs={k:v for k,v in e.attrs.items() if k in keep}
 for e in s.find_all(['p','div','span']):
  if not e.get_text(strip=True) and not e.find(['img','table','a','br']):e.decompose()
 return re.sub(r'\{\{(?:&lt;|<) sitepath .*?(?:&gt;|>)\}\}', lambda m:html.unescape(m[0]), str(s))

def read_records():
 inventory=json.loads((CACHE/'inventory.json').read_text())
 for d in inventory['pages']:
  if d['status']!=200 or 'html' not in d.get('content_type',''):continue
  p=Path(d['cache'])
  if not p.exists() or p.stat().st_size==0:FAILURES.append(dict(type='empty_page',url=d['url']));continue
  s=BeautifulSoup(p.read_bytes(),'html.parser')
  if not s.body:FAILURES.append(dict(type='invalid_html',url=d['url']));continue
  c=s.select_one('link[rel=canonical]');u=canonical(c['href'] if c and c.get('href') else d['final'])
  URLS[d['url']]=pathof(u)
  if u in RECORDS:
   RECORDS[u]['sources'].append(d['url']);continue
  cls=s.body.get('class',[])
  kind='product' if 'single-product' in cls else 'product-category' if 'tax-product_cat' in cls else 'article' if 'single-post' in cls else 'archive' if any(x in cls for x in ['category','author','tax-product_tag']) or '/page/' in pathof(u) else 'page'
  h=s.find('h1');title=h.get_text(' ',strip=True) if h else (s.title.get_text(' ',strip=True).split('|')[0].strip() if s.title else pathof(u))
  if kind=='archive':
   term=s.select_one('meta[property="og:title"]');title=(term['content'].split(' Archives')[0].split(' | ')[0] if term else title)
  desc=s.select_one('meta[name=description]')
  rec=dict(url=u,path=pathof(u),kind=kind,title=title,description=desc.get('content','') if desc else '',soup=s,sources=[d['url']],sitemap=d['sitemap'])
  if kind=='product-category':rec['term']=next((x[5:] for x in cls if x.startswith('term-') and not x[5:].isdigit()),'')
  RECORDS[u]=rec
  URLS[u]=rec['path']
 # The public WordPress API recovers empty cached HTML articles.
 api=CACHE/'posts-api.json'
 if api.exists():
  for post in json.loads(api.read_text()):
   u=canonical(post['link']);body=post['content']['rendered']
   if u not in RECORDS:
    soup=BeautifulSoup('<html><body class="single-post"><h1>'+post['title']['rendered']+'</h1><div class="blog-details"><div class="post-content">'+body+'</div></div></body></html>','html.parser')
    RECORDS[u]=dict(url=u,path=pathof(u),kind='article',title=BeautifulSoup(post['title']['rendered'],'html.parser').get_text(),description=BeautifulSoup(post.get('excerpt',{}).get('rendered',''),'html.parser').get_text(' ',strip=True),soup=soup,sources=[u],sitemap='post-sitemap.xml',recoveredFromAPI=True)
   FAILURES[:]=[x for x in FAILURES if not(x.get('type')=='empty_page' and x.get('url')==u)]
   RECORDS[u]['apiContent']=body
   RECORDS[u]['date']=post['date']
   URLS[u]=pathof(u)
 return inventory

def product_data(r):
 s=r['soup'];root=s.select_one('.type-product');classes=root.get('class',[])
 r['terms']=[x[12:] for x in classes if x.startswith('product_cat-')]
 r['tags']=[x[12:] for x in classes if x.startswith('product_tag-')]
 parts=[]
 code=root.select_one('.procode')
 if code:parts.append(clean(code,r['url']))
 short=root.select_one('.woocommerce-product-details__short-description')
 if short:r['catalogSummary']=short.get_text(' ',strip=True)
 if short:parts.append('<div class="product-introduction">'+clean(short,r['url'])+'</div>')
 gallery=[]
 for e in root.select('.images img,.leftpanlzoom img,.woocommerce-product-gallery img,[data-hq]'):
  u=e.get('data-hq') or (e.find_parent('a').get('href') if e.find_parent('a') else None) or e.get('data-src') or e.get('src')
  if u and re.search(r'\.(jpe?g|png|webp|gif)(\?|$)',u,re.I):
   p=media(u)
   if p not in gallery:gallery.append(p)
 r['gallery']=gallery
 for panel in root.select('.woocommerce-Tabs-panel'):
  h=panel.get('id','').replace('tab-','').replace('-',' ').replace('_',' ').title()
  parts.append('<section class="product-information"><h2>'+html.escape(h)+'</h2>'+clean(panel,r['url'])+'</section>')
 if not root.select('.woocommerce-Tabs-panel'):
  for e in root.select('.entry-content,.description,.product-description'):parts.append(clean(e,r['url']))
 form=root.select_one('form.variations_form') or root.select_one('form.cart');variants=[]
 if form:
  try:
   data=json.loads(form.get('data-product_variations','[]'))
   if isinstance(data,list):
    for v in data:
     row={k.replace('attribute_','').replace('pa_','').replace('-',' '):val for k,val in v.get('attributes',{}).items()}
     if v.get('sku'):row['SKU']=v['sku']
     if row and row not in variants:variants.append(row)
  except (ValueError,TypeError):pass
  options=[]
  for select in form.select('select'):
   label=select.get('data-attribute_name',select.get('name','')).replace('attribute_','').replace('pa_','').replace('-',' ').replace('cartin[','').replace(']','').title()
   values=[x.get_text(' ',strip=True) for x in select.find_all('option') if x.get('value')]
   if values:options.append('<p><strong>'+html.escape(label)+':</strong> '+html.escape(', '.join(values))+'</p>')
  if options:parts.append('<h2>Available options</h2>'+''.join(options))
 if variants:
  keys=list(dict.fromkeys(k for v in variants for k in v))
  table='<h2>Product variants &amp; SKUs</h2><div class="table-scroll"><table><thead><tr>'+''.join('<th>'+html.escape(k.title())+'</th>' for k in keys)+'</tr></thead><tbody>'
  table+=''.join('<tr>'+''.join('<td>'+html.escape(str(v.get(k,'')))+'</td>' for k in keys)+'</tr>' for v in variants)+'</tbody></table></div>'
  parts.append(table)
 r['variants']=len(variants)
 r['options']=sum(len(x.find_all('option'))-1 for x in form.select('select')) if form else 0
 return '\n'.join(parts)

def extract(r):
 s=r['soup'];kind=r['kind']
 if kind=='product':return product_data(r)
 if r['path']=='/products/':return ''
 if kind=='article':
  node=s.select_one('.blog-details .post-content') or s.select_one('.blog-left .post-content') or s.select_one('article .entry-content')
  image=s.select_one('.blog-details .post-pic img')
  if r.get('apiContent') and (not node or len(BeautifulSoup(r['apiContent'],'html.parser').get_text()) > len(node.get_text())):node=BeautifulSoup(r['apiContent'],'html.parser')
  if image:r['gallery']=[media(image.get('data-src') or image.get('src'))]
  date=s.select_one('meta[property="article:published_time"]')
  if date:r['date']=date.get('content')
 elif kind=='product-category':node=s.select_one('.term-description')
 elif kind=='archive' or r['path']=='/blog/':node=s.select_one('.archive-description')
 elif r['path']=='/':return ''
 else:
  h=s.h1;node=h.parent if h else s.select_one('.innerpagewrap .container')
  if node:
   node=BeautifulSoup(str(node),'html.parser');heading=node.find('h1')
   if heading:heading.decompose()
 if node:return clean(node,r['url'])
 if kind not in ('archive','product-category') and r['path']!='/blog/':FAILURES.append(dict(type='no_content_container',url=r['url']))
 return ''

def download(entry):
 u,rel=entry;p=ROOT/'static'/rel;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.stat().st_size:return dict(url=u,path=rel,status=200,bytes=p.stat().st_size)
 if u in PREVIOUS_ASSETS and PREVIOUS_ASSETS[u]['status']==404:return PREVIOUS_ASSETS[u]
 tmp=p.with_suffix(p.suffix+'.part')
 cp=subprocess.run(['curl','-sSL','--retry','1','--max-time','45','--connect-timeout','10','-w','%{http_code}','-o',str(tmp),u],capture_output=True,text=True)
 status=int(cp.stdout) if cp.stdout.isdigit() else 0
 if status==200 and tmp.exists() and tmp.stat().st_size:
  tmp.replace(p);return dict(url=u,path=rel,status=status,bytes=p.stat().st_size)
 if tmp.exists():tmp.unlink()
 return dict(url=u,path=rel,status=status,error=cp.stderr.strip())

def main():
 inventory=read_records()
 # Keep current navigation URLs as aliases while linking directly to original content paths.
 URLS[BASE+'contact/']='/contact-us/'
 URLS[BASE+'products/']='/products/'
 URLS[BASE+'hospital-bed-mattress/tempurpedic-mattress/']='/product-category/memory-foam-mattress/'
 URLS[BASE+'hospital-bed-mattress/therapeutic-mattresses/']='/product-category/hospital-bed-mattress/replacement-mattress/'
 for r in RECORDS.values():
  if r['path'] in ['/cart/','/checkout/','/my-account/']:URLS[r['url']]='/contact-us/'
 # Legacy category URLs sometimes redirect to an article or a single product.
 # Preserve those destination pages and provide a category index at the original URL.
 for path,title,term in [('/product-category/positioning-pads/','Positioning Pads','positioning-pads'),('/product-category/emergency-response-body-bags/','Emergency Response Body Bags','emergency-response-body-bags')]:
  u=BASE.rstrip('/')+path
  if u not in RECORDS:
   RECORDS[u]=dict(url=u,path=path,kind='product-category',title=title,description='',soup=BeautifulSoup('<html><body></body></html>','html.parser'),sources=[],sitemap='product_cat-sitemap.xml',term=term)
  URLS[u]=path
 # Resolve product relationships from archive listing links, including all paginated pages.
 categories=[r for r in RECORDS.values() if r['kind']=='product-category']
 products=[r for r in RECORDS.values() if r['kind']=='product']
 articles=[r for r in RECORDS.values() if r['kind']=='article']
 for r in RECORDS.values():
  if r['kind']=='product':r['body']=extract(r)
 for r in RECORDS.values():
  if r['kind']!='product':r['body']=extract(r)
 for r in RECORDS.values():
  ids=[]
  for a in r['soup'].select('.product a[href],.post-list a[href],.blog-left h2 a[href]'):
   u=canonical(a['href']);target=RECORDS.get(u)
   if target and target['kind'] in ('product','article') and target['path'] not in ids:ids.append(target['path'])
  if r['kind']=='product-category':
   ids=list(dict.fromkeys(ids+[p['path'] for p in products if r.get('term') in p.get('terms',[])]))
  if r['path']=='/blog/':ids=[p['path'] for p in articles]
  r['items']=ids
 print('Content:',dict(Counter(r['kind'] for r in RECORDS.values())),'media:',len(ASSETS),flush=True)
 results=[]
 with futures.ThreadPoolExecutor(max_workers=4) as ex:
  for i,result in enumerate(ex.map(download,ASSETS.items())):
   results.append(result)
   if (i+1)%25==0:print('Media',i+1,'/',len(ASSETS),'failed',sum(x['status']!=200 for x in results),flush=True)
 (REPORT/'assets.json').write_text(json.dumps(results,indent=2))
 failed_paths={x['path']:x for x in results if x['status']!=200}
 for r in RECORDS.values():
  for path,d in failed_paths.items():
   marker=sitepath(path)
   # The HTML contains Hugo shortcodes; replace tags before Hugo renders them.
   r['body']=re.sub(r'<img\b[^>]*src="'+re.escape(marker)+r'"[^>]*>', '<span class="unavailable-media">Original image unavailable on the source website.</span>', r['body'])
   r['body']=re.sub(r'<a\b[^>]*href="'+re.escape(marker)+r'"[^>]*>(.*?)</a>',r'\1',r['body'],flags=re.S)
  r['gallery']=[p for p in r.get('gallery',[]) if p not in failed_paths]
 # Write generated content only after the complete model has been assembled.
 out=ROOT/'content/legacy';out.mkdir(exist_ok=True)
 for old in out.glob('*.md'):old.unlink()
 manifest=[]
 for r in RECORDS.values():
  if r['path'] in ['/','/cart/','/checkout/','/my-account/']:continue
  name=hashlib.sha256(r['url'].encode()).hexdigest()[:16]
  params={k:r[k] for k in ['title','description','catalogSummary','gallery','terms','term','tags','date','items'] if k in r}
  params.update(url=r['path'],layout='product' if r['kind']=='product' else 'catalog' if r['kind'] in ('product-category','archive') or r['path']=='/blog/' else 'single',sourceURL=r['url'],contentKind=r['kind'])
  aliases=[pathof(u) for u in r['sources'] if pathof(u)!=r['path'] and pathof(u) not in ['/product-category/positioning-pads/','/product-category/emergency-response-body-bags/']]
  if r['path']=='/contact-us/':aliases.append('/contact/')
  compatibility={
   '/product-category/hospital-bed-mattress/':'/products/hospital-bed-mattresses/',
   '/product-category/stretcher-mattresses/':'/products/stretcher-mattresses/',
   '/product-category/o-r-surgery-table-pads/':'/products/surgery-imaging-pads/',
   '/product-category/positioning-pads/':'/products/positioning-patient-safety/',
   '/product-category/endoscopy-respiratory-products/':'/products/endoscopy-respiratory/',
   '/product-category/clean-disinfect/':'/products/cleaning-disinfecting/'}
  for source,target in compatibility.items():
   if r['path']==URLS.get(BASE.rstrip('/')+source,source):aliases.append(target)
  if r['path']=='/products/':params.update(layout='catalog',catalogAll=True,contentKind='product-category',title='All medical products')
  if aliases:params['aliases']=list(dict.fromkeys(aliases))
  generated=json.dumps(params,ensure_ascii=False,indent=2)+'\n\n'+r['body']
  (out/(name+'.md')).write_text('\n'.join(line.rstrip() for line in generated.splitlines()).rstrip()+'\n')
  manifest.append(dict(url=r['url'],path=r['path'],kind=r['kind'],title=r['title'],file='content/legacy/'+name+'.md',textCharacters=len(BeautifulSoup(r['body'],'html.parser').get_text(' ',strip=True)),images=r.get('gallery',[]),variants=r.get('variants',0),options=r.get('options',0),items=r.get('items',[])))
 (REPORT/'pages.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
 (REPORT/'issues.json').write_text(json.dumps(FAILURES,indent=2))
 (REPORT/'crawl.json').write_text(json.dumps({k:v for k,v in inventory.items() if k!='pages'}|{'pages':[{k:v for k,v in d.items() if k!='cache'} for d in inventory['pages']]},indent=2))
 (ROOT/'data/routes.json').write_text(json.dumps({r['path']:'/legacy/'+hashlib.sha256(r['url'].encode()).hexdigest()[:16] for r in RECORDS.values() if r['path'] not in ['/','/cart/','/checkout/','/my-account/']},indent=2))
 (ROOT/'data/catalog.json').write_text(json.dumps(dict(products=[p['path'] for p in products],categories=[p['path'] for p in categories],articles=[p['path'] for p in articles]),indent=2))
 print('DONE',len(manifest),'pages',len(results),'assets','issues',len(FAILURES),flush=True)
if __name__=='__main__':main()
