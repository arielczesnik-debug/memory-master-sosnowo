#!/usr/bin/env python3
import json, sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else 'data/vocab.json')
obj=json.loads(p.read_text(encoding='utf-8'))
print('Źródło:',obj['meta'].get('source'))
for c in '45678':
    rows=obj['data'][c]
    cats=len(set(x['cat'] for x in rows))
    print(f'Klasa {c}: {len(rows)} pozycji, {cats} kategorii')
    assert len(rows) >= 100
print('Weryfikacja OK')
