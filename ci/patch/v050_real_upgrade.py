from pathlib import Path
import re

root = Path('saadi-audio-tafsir')
java = root/'app/src/main/java/com/distritech/saaditafsir'
search_dir = java/'search'
ui = java/'ui/SaadiApp.kt'
build = root/'app/build.gradle.kts'

# 1) SEARCH SPEED: cache normalized Quran text once per hit instead of normalizing
# all 6,236 ayahs on every keystroke.
idx_file = search_dir/'AyahTextIndex.kt'
idx = idx_file.read_text(encoding='utf-8')
idx = idx.replace(
    'data class AyahTextHit(val surah: Int, val ayah: Int, val text: String)',
    '''data class AyahTextHit(val surah: Int, val ayah: Int, val text: String) {\n    val normalizedText: String by lazy(LazyThreadSafetyMode.NONE) { AyahSearch.normalizeArabic(text) }\n}'''
)
idx = idx.replace(
    '.filter { AyahSearch.normalizeArabic(it.text).contains(q) }',
    '.filter { it.normalizedText.contains(q) }'
)
idx_file.write_text(idx, encoding='utf-8')

# 2) AUDIO BLOCK MODEL: the current IslamHouse source is one original MP3 per surah.
# We expose deterministic text/audio blocks of max 5 ayahs without inventing fake
# timestamps. Exact seek points can later be filled only from verified timing data.
(search_dir/'AudioAyahBlock.kt').write_text('''package com.distritech.saaditafsir.search

data class AudioAyahBlock(
    val surah: Int,
    val startAyah: Int,
    val endAyah: Int,
    val startMs: Long? = null,
    val endMs: Long? = null
) {
    init {
        require(surah in 1..114)
        require(startAyah >= 1)
        require(endAyah >= startAyah)
        require(endAyah - startAyah + 1 <= 5)
    }
    val hasVerifiedTiming: Boolean get() = startMs != null && endMs != null && endMs > startMs
}

object AudioAyahBlockResolver {
    fun blocks(surah: Int, maxAyah: Int): List<AudioAyahBlock> {
        require(surah in 1..114)
        require(maxAyah >= 1)
        return (1..maxAyah step 5).map { start ->
            AudioAyahBlock(surah, start, minOf(start + 4, maxAyah))
        }
    }

    fun blockForAyah(surah: Int, ayah: Int, maxAyah: Int): AudioAyahBlock =
        blocks(surah, maxAyah).first { ayah in it.startAyah..it.endAyah }
}
''', encoding='utf-8')

# 3) VISIBLE DESIGN: add a real Islamic/zellij hero card on the home results list.
s = ui.read_text(encoding='utf-8')
anchor = '                if (ayahTextResults.isNotEmpty()) {'
hero = '''                item {\n                    Box(\n                        modifier = Modifier\n                            .fillMaxWidth()\n                            .height(150.dp)\n                            .clip(RoundedCornerShape(24.dp))\n                    ) {\n                        Image(\n                            painter = painterResource(com.distritech.saaditafsir.R.drawable.bg_zellij_saadi),\n                            contentDescription = null,\n                            modifier = Modifier.fillMaxSize(),\n                            contentScale = ContentScale.Crop\n                        )\n                        Column(\n                            modifier = Modifier.fillMaxSize().padding(20.dp),\n                            horizontalAlignment = Alignment.CenterHorizontally,\n                            verticalArrangement = Arrangement.Center\n                        ) {\n                            Text("۞ تفسير السعدي ۞", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 26.sp)\n                            Spacer(Modifier.height(8.dp))\n                            Text("القرآن الكريم • التفسير • الاستماع", color = SaadiGold, fontSize = 15.sp)\n                        }\n                    }\n                    Spacer(Modifier.height(10.dp))\n                }\n\n'''
if '۞ تفسير السعدي ۞' not in s:
    if anchor not in s:
        raise SystemExit('V050_HOME_RESULTS_ANCHOR_NOT_FOUND')
    s = s.replace(anchor, hero + anchor, 1)

# Make the player explain the real source/block behavior instead of claiming
# per-ayah files that do not exist in the current source.
s = s.replace(
    'سورة ${surah?.name.orEmpty()} • النص والتفسير مرتبطان بالتسجيل الكامل',
    'سورة ${surah?.name.orEmpty()} • التسجيل الأصلي كامل، والنص مقسّم إلى مقاطع من 1 إلى 5 آيات'
)

imports = [
    'import androidx.compose.foundation.Image',
    'import androidx.compose.ui.res.painterResource',
    'import androidx.compose.ui.layout.ContentScale',
    'import androidx.compose.ui.draw.clip',
]
for imp in imports:
    if imp not in s:
        lines = s.splitlines()
        pos = max([i for i,l in enumerate(lines) if l.startswith('import ')], default=0) + 1
        lines.insert(pos, imp)
        s = '\n'.join(lines) + '\n'
ui.write_text(s, encoding='utf-8')

b = build.read_text(encoding='utf-8')
b = re.sub(r'versionCode\s*=\s*\d+', 'versionCode = 14', b)
b = re.sub(r'versionName\s*=\s*"[^"]+"', 'versionName = "0.5.0"', b)
build.write_text(b, encoding='utf-8')

final_idx = idx_file.read_text(encoding='utf-8')
final_ui = ui.read_text(encoding='utf-8')
assert 'normalizedText' in final_idx
assert '.filter { it.normalizedText.contains(q) }' in final_idx
assert (search_dir/'AudioAyahBlock.kt').is_file()
assert 'endAyah - startAyah + 1 <= 5' in (search_dir/'AudioAyahBlock.kt').read_text(encoding='utf-8')
assert 'bg_zellij_saadi' in final_ui
assert '۞ تفسير السعدي ۞' in final_ui
assert 'مقاطع من 1 إلى 5 آيات' in final_ui
assert 'versionName = "0.5.0"' in build.read_text(encoding='utf-8')
print('v0.5.0 applied: cached Arabic search + visible zellij hero + max-5 audio/text block model')
