from pathlib import Path
import re

root = Path('saadi-audio-tafsir')
ui = root/'app/src/main/java/com/distritech/saaditafsir/ui/SaadiApp.kt'
build = root/'app/build.gradle.kts'
s = ui.read_text(encoding='utf-8')

# Wire the direct-reference parser into Home search, but keep the patch idempotent.
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

# Restrict navigation change to HomeScreen and preserve any existing resume fallback.
start = s.find('private fun HomeScreen')
if start < 0:
    start = s.find('fun HomeScreen')
if start < 0:
    raise SystemExit('V039_HOME_SCREEN_NOT_FOUND')
end = s.find('\n@Composable', start + 20)
if end < 0:
    end = len(s)
segment = s[start:end]

marker = 'onOpenSurah(s.number, directAyahRef?.takeIf { it.surah == s.number }?.ayah'
if marker not in segment:
    call_start = segment.find('onOpenSurah(s.number')
    if call_start < 0:
        raise SystemExit('V039_HOME_NAV_TARGET_NOT_FOUND')

    open_paren = segment.find('(', call_start)
    depth = 0
    close_paren = -1
    for i in range(open_paren, len(segment)):
        ch = segment[i]
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                close_paren = i
                break
    if close_paren < 0:
        raise SystemExit('V039_HOME_NAV_UNBALANCED_CALL')

    call = segment[call_start:close_paren + 1]
    inner = call[len('onOpenSurah('):-1]

    # Split only the top-level comma so nested expressions remain untouched.
    comma = -1
    paren = brace = bracket = 0
    for i, ch in enumerate(inner):
        if ch == '(':
            paren += 1
        elif ch == ')':
            paren -= 1
        elif ch == '{':
            brace += 1
        elif ch == '}':
            brace -= 1
        elif ch == '[':
            bracket += 1
        elif ch == ']':
            bracket -= 1
        elif ch == ',' and paren == 0 and brace == 0 and bracket == 0:
            comma = i
            break

    if comma < 0:
        first_arg = inner.strip()
        fallback = '1'
    else:
        first_arg = inner[:comma].strip()
        fallback = inner[comma + 1:].strip()

    if first_arg != 's.number':
        raise SystemExit('V039_HOME_NAV_FIRST_ARG_CHANGED')
    if not fallback:
        fallback = '1'

    wanted = f'onOpenSurah(s.number, directAyahRef?.takeIf {{ it.surah == s.number }}?.ayah ?: ({fallback}))'
    segment = segment[:call_start] + wanted + segment[close_paren + 1:]
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
assert 'onOpenSurah(s.number, directAyahRef?.takeIf { it.surah == s.number }?.ayah' in final
assert 'ابحث عن سورة أو آية مثل 2:255' in final
assert 'versionName = "0.3.9"' in build.read_text(encoding='utf-8')
print('v0.3.9 applied: direct ayah navigation wired while preserving existing Home fallback')
