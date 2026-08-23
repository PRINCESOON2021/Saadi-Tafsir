from pathlib import Path
import json, sys, re

src = Path(sys.argv[1])
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
count_files = count_ayahs = 0
for f in sorted(src.glob('*.json')):
    m = re.match(r'(\d{3})_', f.name)
    if not m:
        continue
    data = json.loads(f.read_text(encoding='utf-8'))
    ayahs = []
    for a in data.get('ayahs', []):
        saadi = ''
        for t in a.get('tafsir', []):
            if 'السعدي' in t.get('type', ''):
                saadi = t.get('text', '').strip()
                break
        ayahs.append({
            'ayah_number': int(a['ayah_number']),
            'text': a.get('text', '').strip(),
            'tafsir': [{'type': 'تفسير السعدي', 'text': saadi}]
        })
    slim = {'surah': data.get('surah',''), 'number': int(data.get('number', int(m.group(1)))), 'ayahs': ayahs}
    (out / f'{m.group(1)}.json').write_text(json.dumps(slim, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    count_files += 1
    count_ayahs += len(ayahs)

if count_files != 114 or count_ayahs != 6236:
    raise SystemExit(f'Invalid Quran dataset: files={count_files}, ayahs={count_ayahs}')
print(f'Imported {count_files} surahs / {count_ayahs} ayahs with Tafsir Al-Saadi')
