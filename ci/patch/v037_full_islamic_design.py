from pathlib import Path
import re

root = Path('saadi-audio-tafsir')
ui = root / 'app/src/main/java/com/distritech/saaditafsir/ui/SaadiApp.kt'
build = root / 'app/build.gradle.kts'

s = ui.read_text(encoding='utf-8')

# Global palette: emerald + gold + ivory. This changes the whole app theme,
# while leaving the proven audio source/client untouched.
if 'val SaadiEmerald = Color(0xFF0E4D3A)' not in s:
    anchor = s.find('\n@Composable')
    if anchor == -1:
        raise SystemExit('V037_COMPOSABLE_ANCHOR_NOT_FOUND')
    palette = '''\nprivate val SaadiEmerald = Color(0xFF0E4D3A)\nprivate val SaadiEmeraldDark = Color(0xFF08392C)\nprivate val SaadiGold = Color(0xFFD4AF37)\nprivate val SaadiIvory = Color(0xFFFFF8E7)\nprivate val SaadiBackground = Color(0xFFF4EEDF)\nprivate val SaadiText = Color(0xFF24352F)\n\nprivate val SaadiLightColors = lightColorScheme(\n    primary = SaadiEmerald,\n    onPrimary = Color.White,\n    primaryContainer = Color(0xFFDCEBE5),\n    onPrimaryContainer = SaadiEmeraldDark,\n    secondary = SaadiGold,\n    onSecondary = Color(0xFF2D260E),\n    secondaryContainer = Color(0xFFFFEDB0),\n    onSecondaryContainer = Color(0xFF493B00),\n    background = SaadiBackground,\n    onBackground = SaadiText,\n    surface = SaadiIvory,\n    onSurface = SaadiText,\n    surfaceVariant = Color(0xFFEDE5D5),\n    outline = Color(0xFFBDAA77)\n)\n'''
    s = s[:anchor] + palette + s[anchor:]

# Replace the first plain MaterialTheme wrapper with the real Saadi theme.
if 'MaterialTheme(colorScheme = SaadiLightColors)' not in s:
    if 'MaterialTheme {' not in s:
        raise SystemExit('V037_MATERIAL_THEME_TARGET_NOT_FOUND')
    s = s.replace('MaterialTheme {', 'MaterialTheme(colorScheme = SaadiLightColors) {', 1)

# Give all plain Scaffolds the ivory app background where safe.
# Only replace zero-argument opening form, avoiding screens with custom parameters.
s = s.replace('Scaffold {', 'Scaffold(containerColor = SaadiBackground) {')
s = s.replace('Scaffold(\n', 'Scaffold(\n        containerColor = SaadiBackground,\n', 1) if 'Scaffold(\n' in s and 'containerColor = SaadiBackground' not in s else s

# Harmonize the already-visible audio player card with the global palette.
s = s.replace('color = Color(0xFFFFF8E7)', 'color = SaadiIvory')
s = s.replace('Color(0xFFD4AF37)', 'SaadiGold')
s = s.replace('Color(0xFF0E4D3A)', 'SaadiEmerald')
s = s.replace('Color(0xFF6B5A32)', 'Color(0xFF6A5A31)')

# Ensure imports needed by the global theme.
imports = [
    'import androidx.compose.material3.lightColorScheme',
    'import androidx.compose.ui.graphics.Color',
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

final = ui.read_text(encoding='utf-8')
assert 'SaadiLightColors = lightColorScheme' in final
assert 'primary = SaadiEmerald' in final
assert 'secondary = SaadiGold' in final
assert 'background = SaadiBackground' in final
assert 'surface = SaadiIvory' in final
assert 'MaterialTheme(colorScheme = SaadiLightColors)' in final
assert 'تفسير السعدي المسموع' in final
assert 'AudioClient.setVolume(it)' in final
assert 'AudioClient.seekTo(target)' in final
assert 'versionName = "0.3.7"' in build.read_text(encoding='utf-8')
print('v0.3.7 applied: global Islamic theme + existing working audio controls preserved')
