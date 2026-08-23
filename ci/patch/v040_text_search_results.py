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

# Build a compact in-app Quran ayah index from the already imported 114 surahs.
entries = []
for f in sorted(assets.glob('*.json')):
    data = json.loads(f.read_text(encoding='utf-8'))
    surah = int(data['number'])
    for a in data.get('ayahs', []):
        ayah = int(a['ayah_number'])
        text = a.get('text', '').strip()
        if text:
            entries.append((surah, ayah, text))

if len(entries) != 6236:
    raise SystemExit(f'V040_INVALID_QURAN_INDEX_SIZE:{len(entries)}')

# Kotlin source. Normalization delegates to the already tested AyahSearch.normalizeArabic.
def kstr(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)

lines = [
    'package com.distritech.saaditafsir.search',
    '',
    'data class AyahTextHit(val surah: Int, val ayah: Int, val text: String)',
    '',
    'object AyahTextIndex {',
    '    private val entries = listOf(',
]
for surah, ayah, text in entries:
    lines.append(f'        AyahTextHit({surah}, {ayah}, {kstr(text)}),')
lines += [
    '    )',
    '',
    '    fun search(query: String, limit: Int = 50): List<AyahTextHit> {',
    '        val q = AyahSearch.normalizeArabic(query)',
    '        if (q.length < 2) return emptyList()',
    '        return entries.asSequence()',
    '            .filter { AyahSearch.normalizeArabic(it.text).contains(q) }',
    '            .take(limit.coerceIn(1, 100))',
    '            .toList()',
    '    }',
    '}',
    '',
]
(search_dir/'AyahTextIndex.kt').write_text('\n'.join(lines), encoding='utf-8')

s = ui.read_text(encoding='utf-8')

# v0.3.9 must already have wired direct-reference search.
needle = '''    val directAyahRef = remember(query) { com.distritech.saaditafsir.search.AyahSearch.parseDirectRef(query) }\n    val filtered = remember(query, directAyahRef) {'''
replacement = '''    val directAyahRef = remember(query) { com.distritech.saaditafsir.search.AyahSearch.parseDirectRef(query) }\n    val ayahTextResults = remember(query, directAyahRef) {\n        if (directAyahRef == null && query.trim().length >= 2)\n            com.distritech.saaditafsir.search.AyahTextIndex.search(query.trim(), 50)\n        else emptyList()\n    }\n    val filtered = remember(query, directAyahRef, ayahTextResults) {'''
if needle not in s:
    raise SystemExit('V040_V039_SEARCH_WIRING_NOT_FOUND')
s = s.replace(needle, replacement, 1)

# If Quran-text hits exist, don't also flood the same screen with unrelated surah-name hits.
s = s.replace(
    '''        if (ref != null) QuranMetadata.surahs.filter { it.number == ref.surah }\n        else QuranMetadata.surahs.filter { it.name.contains(query.trim()) || it.number.toString() == query.trim() }''',
    '''        if (ref != null) QuranMetadata.surahs.filter { it.number == ref.surah }\n        else if (ayahTextResults.isNotEmpty()) emptyList()\n        else QuranMetadata.surahs.filter { it.name.contains(query.trim()) || it.number.toString() == query.trim() }''',
    1
)

# Insert ayah result cards immediately before the existing surah result items.
anchor = '''                items(filtered, key = { it.number }) { s ->'''
if anchor not in s:
    raise SystemExit('V040_HOME_ITEMS_ANCHOR_NOT_FOUND')
results_ui = '''                if (ayahTextResults.isNotEmpty()) {\n                    item {\n                        Text("نتائج الآيات (${ayahTextResults.size})", fontWeight = FontWeight.Bold, color = SaadiEmerald, modifier = Modifier.padding(vertical = 6.dp))\n                    }\n                    items(ayahTextResults, key = { "ayah:${it.surah}:${it.ayah}" }) { hit ->\n                        val hitSurahName = QuranMetadata.surahs.firstOrNull { it.number == hit.surah }?.name ?: hit.surah.toString()\n                        Card(\n                            Modifier.fillMaxWidth().clickable { onOpenSurah(hit.surah, hit.ayah) },\n                            colors = CardDefaults.cardColors(containerColor = SaadiIvory),\n                            shape = RoundedCornerShape(16.dp)\n                        ) {\n                            Column(Modifier.fillMaxWidth().padding(14.dp)) {\n                                Text("سورة $hitSurahName • الآية ${hit.ayah}", fontWeight = FontWeight.Bold, color = SaadiEmerald)\n                                Spacer(Modifier.height(6.dp))\n                                Text(hit.text, maxLines = 3, overflow = TextOverflow.Ellipsis, textAlign = TextAlign.Right, modifier = Modifier.fillMaxWidth())\n                            }\n                        }\n                    }\n                }\n\n                items(filtered, key = { it.number }) { s ->'''
s = s.replace(anchor, results_ui, 1)

# Search hint clearly advertises all supported modes.
s = s.replace('ابحث عن سورة أو آية مثل 2:255', 'ابحث بكلمة أو عبارة من الآية، أو مثل 2:255', 1)

# Ensure TextOverflow import exists.
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
assert 'versionName = "0.4.0"' in build.read_text(encoding='utf-8')
print('v0.4.0 applied: Arabic word/phrase ayah search with selectable result list')
