from pathlib import Path
import re

root = Path('saadi-audio-tafsir')
ui = root / 'app/src/main/java/com/distritech/saaditafsir/ui/SaadiApp.kt'
build = root / 'app/build.gradle.kts'

s = ui.read_text(encoding='utf-8')

# v0.3.7 must NOT depend on a MaterialTheme wrapper being present in SaadiApp.kt.
# The base app may apply its theme from MainActivity/Theme.kt. We therefore style
# the actual screens/components rendered by SaadiApp and preserve the working audio.

# First harmonize colors that already exist in the injected player BEFORE defining
# named palette constants (avoids accidentally rewriting the constant definitions).
s = s.replace('color = Color(0xFFFFF8E7)', 'color = SaadiIvory')
s = s.replace('border = BorderStroke(1.dp, Color(0xFFD4AF37))', 'border = BorderStroke(1.dp, SaadiGold)')
s = s.replace('tint = Color(0xFFD4AF37)', 'tint = SaadiGold')
s = s.replace('color = Color(0xFFD4AF37)', 'color = SaadiGold')
s = s.replace('tint = Color(0xFF0E4D3A)', 'tint = SaadiEmerald')
s = s.replace('color = Color(0xFF0E4D3A)', 'color = SaadiEmerald')

# Define a stable Islamic palette near the composables.
if 'private val SaadiEmerald = Color(0xFF0E4D3A)' not in s:
    anchor = s.find('\n@Composable')
    if anchor == -1:
        raise SystemExit('V037_COMPOSABLE_ANCHOR_NOT_FOUND')
    palette = '''\nprivate val SaadiEmerald = Color(0xFF0E4D3A)\nprivate val SaadiEmeraldDark = Color(0xFF08392C)\nprivate val SaadiGold = Color(0xFFD4AF37)\nprivate val SaadiIvory = Color(0xFFFFF8E7)\nprivate val SaadiBackground = Color(0xFFF4EEDF)\nprivate val SaadiText = Color(0xFF24352F)\nprivate val SaadiMuted = Color(0xFF6A5A31)\n'''
    s = s[:anchor] + palette + s[anchor:]

# Apply the background to actual Scaffolds without relying on MaterialTheme.
# Handle common Compose forms conservatively.
s = s.replace('Scaffold {', 'Scaffold(containerColor = SaadiBackground) {')
s = re.sub(
    r'Scaffold\(\s*snackbarHost\s*=',
    'Scaffold(\n        containerColor = SaadiBackground,\n        snackbarHost =',
    s
)
s = re.sub(
    r'Scaffold\(\s*topBar\s*=',
    'Scaffold(\n        containerColor = SaadiBackground,\n        topBar =',
    s
)

# Restyle common cards/surfaces used for surah/ayah/tafsir without changing logic.
# Only touch explicit default Surface/Card openings where the base code has no custom color.
s = s.replace('Surface(Modifier.fillMaxWidth()) {', 'Surface(Modifier.fillMaxWidth(), color = SaadiIvory, shape = RoundedCornerShape(18.dp)) {')
s = s.replace('Card(Modifier.fillMaxWidth()) {', 'Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = SaadiIvory), shape = RoundedCornerShape(18.dp)) {')

# Harmonize common hard-coded text colors from prior patches.
s = s.replace('Color(0xFF6B5A32)', 'SaadiMuted')

# Ensure imports required by the real component-level styling.
imports = [
    'import androidx.compose.ui.graphics.Color',
    'import androidx.compose.material3.CardDefaults',
    'import androidx.compose.foundation.shape.RoundedCornerShape',
]
for imp in imports:
    if imp not in s:
        lines = s.splitlines()
        pos = max([i for i,l in enumerate(lines) if l.startswith('import ')], default=0) + 1
        lines.insert(pos, imp)
        s = '\n'.join(lines) + '\n'

ui.write_text(s, encoding='utf-8')

b = build.read_text(encoding='utf-8')
b = re.sub(r'versionCode\s*=\s*\d+', 'versionCode = 10', b)
b = re.sub(r'versionName\s*=\s*"[^"]+"', 'versionName = "0.3.7"', b)
build.write_text(b, encoding='utf-8')

# Hard acceptance assertions. Do not silently build an unchanged UI.
final = ui.read_text(encoding='utf-8')
assert 'private val SaadiEmerald = Color(0xFF0E4D3A)' in final
assert 'private val SaadiGold = Color(0xFFD4AF37)' in final
assert 'private val SaadiIvory = Color(0xFFFFF8E7)' in final
assert 'private val SaadiBackground = Color(0xFFF4EEDF)' in final
assert 'SaadiGold = SaadiGold' not in final
assert 'SaadiEmerald = SaadiEmerald' not in final
assert 'تفسير السعدي المسموع' in final
assert 'AudioClient.setVolume(it)' in final
assert 'AudioClient.seekTo(target)' in final
assert 'versionName = "0.3.7"' in build.read_text(encoding='utf-8')
print('v0.3.7 applied: component-level Islamic design + working audio controls preserved')
