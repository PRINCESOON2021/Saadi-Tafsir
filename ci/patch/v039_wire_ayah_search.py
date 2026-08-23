from pathlib import Path
import re

root = Path('saadi-audio-tafsir')
ui = root/'app/src/main/java/com/distritech/saaditafsir/ui/SaadiApp.kt'
build = root/'app/build.gradle.kts'
s = ui.read_text(encoding='utf-8')

# Wire the already-tested AyahSearch parser into the real Home search.
old = '''    val filtered = remember(query) {
        QuranMetadata.surahs.filter { it.name.contains(query.trim()) || it.number.toString() == query.trim() }
    }'''
new = '''    val directAyahRef = remember(query) { com.distritech.saaditafsir.search.AyahSearch.parseDirectRef(query) }
    val filtered = remember(query, directAyahRef) {
        val ref = directAyahRef
        if (ref != null) QuranMetadata.surahs.filter { it.number == ref.surah }
        else QuranMetadata.surahs.filter { it.name.contains(query.trim()) || it.number.toString() == query.trim() }
    }'''
if old not in s:
    raise SystemExit('V039_FILTER_TARGET_NOT_FOUND')
s = s.replace(old, new, 1)

# Change only the Home screen result navigation: a direct reference such as 2:255
# must open ayah 255, while normal surah search still opens ayah 1.
start = s.find('private fun HomeScreen')
if start < 0:
    start = s.find('fun HomeScreen')
if start < 0:
    raise SystemExit('V039_HOME_SCREEN_NOT_FOUND')
end = s.find('\n@Composable', start + 20)
if end < 0:
    end = len(s)
segment = s[start:end]
segment2, count = re.subn(
    r'onOpenSurah\(s\.number\)',
    'onOpenSurah(s.number, directAyahRef?.takeIf { it.surah == s.number }?.ayah ?: 1)',
    segment
)
if count < 1:
    raise SystemExit('V039_HOME_NAV_TARGET_NOT_FOUND')
s = s[:start] + segment2 + s[end:]

# Make the search hint explicit so the feature is discoverable.
s = s.replace('ابحث عن سورة بالاسم أو الرقم', 'ابحث عن سورة أو آية مثل 2:255', 1)

ui.write_text(s, encoding='utf-8')

b = build.read_text(encoding='utf-8')
b = re.sub(r'versionCode\s*=\s*\d+', 'versionCode = 12', b)
b = re.sub(r'versionName\s*=\s*"[^"]+"', 'versionName = "0.3.9"', b)
build.write_text(b, encoding='utf-8')

final = ui.read_text(encoding='utf-8')
assert 'val directAyahRef = remember(query)' in final
assert 'AyahSearch.parseDirectRef(query)' in final
assert 'directAyahRef?.takeIf { it.surah == s.number }?.ayah ?: 1' in final
assert 'ابحث عن سورة أو آية مثل 2:255' in final
assert 'versionName = "0.3.9"' in build.read_text(encoding='utf-8')
print('v0.3.9 applied: exact ayah reference search wired to real Home navigation')
