#!/usr/bin/env python3
from __future__ import annotations
import argparse, io, json, re
from pathlib import Path
import requests
from pypdf import PdfReader

URLS = {
    "4": "https://blumont.edu.pl/images/memory_master_listy_slow/MEMORY%20MASTER%20-%20lista%20klasa%204.pdf",
    "5": "https://blumont.edu.pl/images/memory_master_listy_slow/MEMORY%20MASTER%20-%20lista%20klasa%205.pdf",
    "6": "https://blumont.edu.pl/images/memory_master_listy_slow/MEMORY%20MASTER%20-%20lista%20klasa%206.pdf",
    "7": "https://blumont.edu.pl/images/memory_master_listy_slow/MEMORY%20MASTER%20-%20lista%20klasa%207.pdf",
    "8": "https://blumont.edu.pl/images/memory_master_listy_slow/MEMORY%20MASTER%20-%20lista%20klasa%208.pdf",
}
HEADER_RE = re.compile(r"Ogólnopolski Konkurs Języka Angielskiego.*?klasa\s+\d", re.I)
SEP_RE = re.compile(r"\s+[–-]\s+|(?<=[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż)])[-–]\s+")
POLISH = set("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ")

def clean_lines(text: str):
    raw=[]
    for ln in text.replace('\u00a0',' ').splitlines():
        s=' '.join(ln.strip().split())
        if not s: continue
        if HEADER_RE.search(s): continue
        if '©MEMORY MASTER' in s: continue
        if re.fullmatch(r'\d+', s): continue
        raw.append(s)
    return raw

def is_category(s: str) -> bool:
    if '-' in s or '–' in s: return False
    letters=''.join(ch for ch in s if ch.isalpha())
    if not letters: return False
    return letters.upper()==letters and len(s) <= 80

def split_entry(s: str):
    matches=list(SEP_RE.finditer(s))
    if not matches: return None
    m=matches[-1]
    en=s[:m.start()].strip(' -–')
    pl=s[m.end():].strip()
    if not en or not pl: return None
    return en,pl

def looks_english_fragment(s: str) -> bool:
    if any(ch in POLISH for ch in s): return False
    return bool(re.search(r'[A-Za-z]', s))

def parse_pdf(content: bytes):
    reader=PdfReader(io.BytesIO(content))
    lines=[]
    for p in reader.pages:
        lines.extend(clean_lines(p.extract_text() or ''))
    items=[]; cat='OTHER'; i=0
    while i < len(lines):
        s=lines[i]
        if is_category(s):
            cat=s; i+=1; continue
        low=s.lower()
        if low.startswith('make friends with somebody '):
            pl=s[len('make friends with somebody '):].strip()
            items.append({'cat':cat,'en':'make friends with somebody','pl':pl})
            i+=1; continue
        if low == 'tax podatek':
            items.append({'cat':cat,'en':'tax','pl':'podatek'})
            i+=1; continue
        entry=split_entry(s)
        if entry:
            en,pl=entry
            items.append({'cat':cat,'en':en,'pl':pl})
            i+=1; continue
        if i+1 < len(lines) and split_entry(lines[i+1]) and looks_english_fragment(s):
            en2,pl2=split_entry(lines[i+1])
            items.append({'cat':cat,'en':f'{s} {en2}'.strip(),'pl':pl2})
            i+=2; continue
        if items and not is_category(s):
            items[-1]['pl'] = (items[-1]['pl'] + ' ' + s).strip()
        i+=1
    cleaned=[]; seen=set()
    for it in items:
        key=(it['cat'],it['en'],it['pl'])
        if key in seen: continue
        seen.add(key); cleaned.append(it)
    return cleaned

def download(url):
    r=requests.get(url,timeout=60,headers={'User-Agent':'Mozilla/5.0 MemoryMasterSchoolBuilder/2.2'})
    r.raise_for_status()
    return r.content

def patch_html(path: Path, data, meta):
    text=path.read_text(encoding='utf-8')
    data_json=json.dumps(data,ensure_ascii=False,separators=(',',':'))
    meta_json=json.dumps(meta,ensure_ascii=False,separators=(',',':'))
    text,n1=re.subn(r'const DATA = \{.*?\};\n', f'const DATA = {data_json};\n', text, count=1, flags=re.S)
    text,n2=re.subn(r'const VOCAB_META = \{.*?\};\n', f'const VOCAB_META = {meta_json};\n', text, count=1, flags=re.S)
    if n1!=1 or n2!=1:
        raise RuntimeError('Nie znaleziono bloków DATA/VOCAB_META w index.html')
    path.write_text(text,encoding='utf-8')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--html',default='index.html')
    ap.add_argument('--json-out',default='data/vocab.json')
    args=ap.parse_args()
    all_data={}; counts={}
    for cls,url in URLS.items():
        print(f'Pobieram klasę {cls}: {url}', flush=True)
        data=parse_pdf(download(url))
        all_data[cls]=data; counts[cls]=len(data)
        print(f'  -> {len(data)} pozycji', flush=True)
        if len(data) < 100:
            raise RuntimeError(f'Podejrzanie mało pozycji dla klasy {cls}: {len(data)}')
    out=Path(args.json_out); out.parent.mkdir(parents=True,exist_ok=True)
    meta={'fullImport':True,'source':'official-memory-master-pdf','generatedAt':'github-actions','counts':counts,'urls':URLS}
    out.write_text(json.dumps({'meta':meta,'data':all_data},ensure_ascii=False,indent=2),encoding='utf-8')
    patch_html(Path(args.html),all_data,meta)
    print('Gotowe:',counts)

if __name__=='__main__':
    main()
