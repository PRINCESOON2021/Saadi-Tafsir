from pathlib import Path
import re

root = Path('saadi-audio-tafsir')
ui = root/'app/src/main/java/com/distritech/saaditafsir/ui/SaadiApp.kt'
build = root/'app/build.gradle.kts'
s = ui.read_text(encoding='utf-8')

# Idempotent: if already wired, do not try to patch the same block again.
if 'val directAyahRef = remember(query)' not in s:
    pattern = re.compile(
        r'''    val filtered = remember\(query\) \{\n'''
        r'''        QuranMetadata\.surahs\.filter \{ it\.name\.contains\(query\.trim\(\)\) \|\| it\.number\.toString\(\) == query\.trim\(\) \}\n'''
        r'''    \}'''
    )
    replacement = '''    val directAyahRef = remember(query) { com.distritech.saaditafsir.search.AyahSearch.parseDirectRef(query) }\n    val filtered = remember(query, directAyahRef) {\n        val ref = directAyahRef\n        if (ref != null) QuranMetadata.surahs.filter { it.number == ref.surah }\n        else QuranMetadata.surahs.filter { it.name.contains(query.trim()) || it.number.toString() == query.trim() }\n    }'''
    s, count = pattern.subn(replacement, s, count=1)
    if count != 1:
        raise SystemExit('V039_FILTER_TARGET_NOT_FOUND')

# Limit navigation replacement to HomeScreen. The last known green build shows
# HomeScreen already opens resume positions with (surah, ayah), so the callback
# supports the two-argument form we need here.
start = s.find('private fun HomeScreen')
if start < 0:
    start = s.find('fun HomeScreen')
if start < 0:
    raise SystemExit('V039_HOME_SCREEN_NOT_FOUND')
end = s.find('\n@Composable', start + 20)
if end < 0:
    end = len(s)
segment = s[start:end]

wanted = 'onOpenSurah(s.number, directAyahRef?.takeIf { it.surah == s.number }?.ayah ?: 1)'
if wanted not in segment:
    segment, count = re.subn(
        r'onOpenSurah\(s\.number\)',
        wanted,
        segment,
        count=1
    )
    if count != 1:
        raise SystemExit('V039_HOME_NAV_TARGET_NOT_FOUND')
    s = s[:start] + segment + s[end:]

# Search hint: keep it idempotent.
if 'ابحث عن سورة أو آية مثل 2:255' not in s:
    s = s.replace('ابحث عن سورة بالاسم أو الرقم', 'ابحث عن سورة أو آية مثل 2:255', 1)

ui.write_text(s, encoding='utf-8')

b = build.read_text(encoding='utf-8')
b = re.sub(r'versionCode\s*=\s*\d+', 'versionCode = 12', b)
b = re.sub(r'versionName\s*=\s*"[^"]+"', 'versionName = "0.3.9"', b)
build.write_text(b, encoding='utf-8')

final = ui.read_text(encoding='utf-8')
assert 'val directAyahRef = remember(query)' in final
assert 'AyahSearch.parseDirectRef(query)' in final
assert wanted in final
assert 'ابحث عن سورة أو آية مثل 2:255' in final
assert 'versionName = "0.3.9"' in build.read_text(encoding='utf-8')
print('v0.3.9 applied: exact ayah reference search wired robustly to Home navigation')
