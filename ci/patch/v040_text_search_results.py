from pathlib import Path
import json, re

root = Path('saadi-audio-tafsir')
assets = root/'app/src/main/assets/tafsir'
java = root/'app/src/main/java/com/distritech/saaditafsir'
search_dir = java/'search'
ui = java/'ui/SaadiApp.kt'
build = root/'app/build.gradle.kts'

if not assets.exists():
    raise SystemExit('V040_TAFSIR_ASSETS_NOT_FOUND')

entries_by_surah = {}
total = 0
for f in sorted(assets.glob('*.json')):
    data = json.loads(f.read_text(encoding='utf-8'))
    surah = int(data['number'])
    rows = []
    for a in data.get('ayahs', []):
        ayah = int(a['ayah_number'])
        text = a.get('text', '').strip()
        if text:
            rows.append((ayah, text))
            total += 1
    entries_by_surah[surah] = rows

if total != 6236 or len(entries_by_surah) != 114:
    raise SystemExit(f'V040_INVALID_QURAN_INDEX_SIZE:{total}/{len(entries_by_surah)}')

def kstr(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)

# IMPORTANT: do not generate all 6236 AyahTextHit constructors in one Kotlin object.
# That creates a JVM <clinit> method larger than 64 KiB. One small shard per surah
# keeps every generated method well below the JVM bytecode limit.
shard_dir = search_dir/'textindex'
shard_dir.mkdir(parents=True, exist_ok=True)
for old in shard_dir.glob('AyahTextShard*.kt'):
    old.unlink()

for surah in range(1, 115):
    rows = entries_by_surah[surah]
    name = f'AyahTextShard{surah:03d}'
    lines = [
        'package com.distritech.saaditafsir.search.textindex',
        '',
        'import com.distritech.saaditafsir.search.AyahTextHit',
        '',
        f'object {name} {{',
        '    val entries: List<AyahTextHit> = listOf(',
    ]
    for ayah, text in rows:
        lines.append(f'        AyahTextHit({surah}, {ayah}, {kstr(text)}),')
    lines += ['    )', '}', '']
    (shard_dir/f'{name}.kt').write_text('\n'.join(lines), encoding='utf-8')

index_lines = [
    'package com.distritech.saaditafsir.search',
    '',
    'import com.distritech.saaditafsir.search.textindex.*',
    '',
    'data class AyahTextHit(val surah: Int, val ayah: Int, val text: String)',
    '',
    'object AyahTextIndex {',
    '    private val shards: List<List<AyahTextHit>> = listOf(',
]
for surah in range(1, 115):
    index_lines.append(f'        AyahTextShard{surah:03d}.entries,')
index_lines += [
    '    )',
    '',
    '    fun search(query: String, limit: Int = 50): List<AyahTextHit> {',
    '        val q = AyahSearch.normalizeArabic(query)',
    '        if (q.length < 2) return emptyList()',
    '        return shards.asSequence()',
    '            .flatten()',
    '            .filter { AyahSearch.normalizeArabic(it.text).contains(q) }',
    '            .take(limit.coerceIn(1, 100))',
    '            .toList()',
    '    }',
    '}',
    '',
]
(search_dir/'AyahTextIndex.kt').write_text('\n'.join(index_lines), encoding='utf-8')

s = ui.read_text(encoding='utf-8')
needle = '''    val directAyahRef = remember(query) { com.distritech.saaditafsir.search.AyahSearch.parseDirectRef(query) }\n    val filtered = remember(query, directAyahRef) {'''
replacement = '''    val directAyahRef = remember(query) { com.distritech.saaditafsir.search.AyahSearch.parseDirectRef(query) }\n    val ayahTextResults = remember(query, directAyahRef) {\n        if (directAyahRef == null && query.trim().length >= 2)\n            com.distritech.saaditafsir.search.AyahTextIndex.search(query.trim(), 50)\n        else emptyList()\n    }\n    val filtered = remember(query, directAyahRef, ayahTextResults) {'''
if needle not in s:
    raise SystemExit('V040_V039_SEARCH_WIRING_NOT_FOUND')
s = s.replace(needle, replacement, 1)

s = s.replace(
    '''        if (ref != null) QuranMetadata.surahs.filter { it.number == ref.surah }\n        else QuranMetadata.surahs.filter { it.name.contains(query.trim()) || it.number.toString() == query.trim() }''',
    '''        if (ref != null) QuranMetadata.surahs.filter { it.number == ref.surah }\n        else if (ayahTextResults.isNotEmpty()) emptyList()\n        else QuranMetadata.surahs.filter { it.name.contains(query.trim()) || it.number.toString() == query.trim() }''',
    1
)

anchor = '''                items(filtered, key = { it.number }) { s ->'''
if anchor not in s:
    raise SystemExit('V040_HOME_ITEMS_ANCHOR_NOT_FOUND')
results_ui = '''                if (ayahTextResults.isNotEmpty()) {\n                    item {\n                        Text("نتائج الآيات (${ayahTextResults.size})", fontWeight = FontWeight.Bold, color = SaadiEmerald, modifier = Modifier.padding(vertical = 6.dp))\n                    }\n                    items(ayahTextResults, key = { "ayah:${it.surah}:${it.ayah}" }) { hit ->\n                        val hitSurahName = QuranMetadata.surahs.firstOrNull { it.number == hit.surah }?.name ?: hit.surah.toString()\n                        Card(\n                            Modifier.fillMaxWidth().clickable { onOpenSurah(hit.surah, hit.ayah) },\n                            colors = CardDefaults.cardColors(containerColor = SaadiIvory),\n                            shape = RoundedCornerShape(16.dp)\n                        ) {\n                            Column(Modifier.fillMaxWidth().padding(14.dp)) {\n                                Text("سورة $hitSurahName • الآية ${hit.ayah}", fontWeight = FontWeight.Bold, color = SaadiEmerald)\n                                Spacer(Modifier.height(6.dp))\n                                Text(hit.text, maxLines = 3, overflow = TextOverflow.Ellipsis, textAlign = TextAlign.Right, modifier = Modifier.fillMaxWidth())\n                            }\n                        }\n                    }\n                }\n\n                items(filtered, key = { it.number }) { s ->'''
s = s.replace(anchor, results_ui, 1)
s = s.replace('ابحث عن سورة أو آية مثل 2:255', 'ابحث بكلمة أو عبارة من الآية، أو مثل 2:255', 1)

imp = 'import androidx.compose.ui.text.style.TextOverflow'
if imp not in s:
    ls = s.splitlines()
    pos = max([i for i,l in enumerate(ls) if l.startswith('import ')], default=0) + 1
    ls.insert(pos, imp)
    s = '\n'.join(ls) + '\n'
ui.write_text(s, encoding='utf-8')

b = build.read_text(encoding='utf-8')
b = re.sub(r'versionCode\s*=\s*\d+', 'versionCode = 13', b)
b = re.sub(r'versionName\s*=\s*"[^"]+"', 'versionName = "0.4.0"', b)
build.write_text(b, encoding='utf-8')

final = ui.read_text(encoding='utf-8')
idx = (search_dir/'AyahTextIndex.kt').read_text(encoding='utf-8')
assert 'AyahTextIndex.search(query.trim(), 50)' in final
assert 'نتائج الآيات (${ayahTextResults.size})' in final
assert 'onOpenSurah(hit.surah, hit.ayah)' in final
assert 'ابحث بكلمة أو عبارة من الآية، أو مثل 2:255' in final
assert 'TextOverflow.Ellipsis' in final
assert 'fun search(query: String, limit: Int = 50)' in idx
assert len(list(shard_dir.glob('AyahTextShard*.kt'))) == 114
assert 'versionName = "0.4.0"' in build.read_text(encoding='utf-8')
print('v0.4.0 applied: Arabic ayah text search using 114 compiler-safe surah shards')
