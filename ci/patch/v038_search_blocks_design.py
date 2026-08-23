from pathlib import Path
import re

root = Path('saadi-audio-tafsir')
java = root/'app/src/main/java/com/distritech/saaditafsir'
util = java/'search'
util.mkdir(parents=True, exist_ok=True)
res = root/'app/src/main/res/drawable'
res.mkdir(parents=True, exist_ok=True)
build = root/'app/build.gradle.kts'
ui = root/'app/src/main/java/com/distritech/saaditafsir/ui/SaadiApp.kt'

(util/'AyahBlock.kt').write_text('''package com.distritech.saaditafsir.search

data class AyahBlock(val surah: Int, val startAyah: Int, val endAyah: Int) {
    init {
        require(surah in 1..114)
        require(startAyah >= 1)
        require(endAyah >= startAyah)
        require(endAyah - startAyah + 1 <= 5)
    }
    fun contains(ayah: Int): Boolean = ayah in startAyah..endAyah
}

object AyahBlockResolver {
    fun blockForAyah(surah: Int, ayah: Int, maxAyah: Int): AyahBlock {
        require(surah in 1..114)
        require(maxAyah >= 1)
        require(ayah in 1..maxAyah)
        val start = ((ayah - 1) / 5) * 5 + 1
        val end = minOf(start + 4, maxAyah)
        return AyahBlock(surah, start, end)
    }
}
''', encoding='utf-8')

(util/'AyahSearch.kt').write_text('''package com.distritech.saaditafsir.search

import java.text.Normalizer

data class AyahRef(val surah: Int, val ayah: Int)

object AyahSearch {
    private val direct = Regex("""^\s*(\d{1,3})\s*[:/-]\s*(\d{1,3})\s*$""")
    private val arabicDigits = mapOf('٠' to '0','١' to '1','٢' to '2','٣' to '3','٤' to '4','٥' to '5','٦' to '6','٧' to '7','٨' to '8','٩' to '9')

    fun parseDirectRef(query: String): AyahRef? {
        val latin = query.map { arabicDigits[it] ?: it }.joinToString("")
        val m = direct.matchEntire(latin) ?: return null
        val s = m.groupValues[1].toIntOrNull() ?: return null
        val a = m.groupValues[2].toIntOrNull() ?: return null
        if (s !in 1..114 || a < 1) return null
        return AyahRef(s, a)
    }

    fun normalizeArabic(value: String): String {
        var s = value.map { arabicDigits[it] ?: it }.joinToString("")
        s = Normalizer.normalize(s, Normalizer.Form.NFD)
        s = s.replace(Regex("""[\u064B-\u065F\u0670\u06D6-\u06ED]"""), "")
        s = s.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ؤ','و').replace('ئ','ي').replace('ة','ه')
        s = s.replace(Regex("""[^\p{L}\p{N}]+"""), " ").trim().replace(Regex("""\s+"""), " ")
        return s.lowercase()
    }

    fun matchesText(query: String, quranText: String, tafsirText: String = ""): Boolean {
        val q = normalizeArabic(query)
        if (q.isBlank()) return true
        return normalizeArabic(quranText).contains(q) || normalizeArabic(tafsirText).contains(q)
    }
}
''', encoding='utf-8')

(res/'bg_zellij_saadi.xml').write_text('''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="360dp" android:height="220dp" android:viewportWidth="360" android:viewportHeight="220">
    <path android:fillColor="#071A33" android:pathData="M0,0H360V220H0Z"/>
    <path android:fillColor="#0E4D3A" android:fillAlpha="0.55" android:pathData="M0,170L90,80L180,170L270,80L360,170V220H0Z"/>
    <path android:fillColor="#D4AF37" android:fillAlpha="0.30" android:pathData="M45,0L90,45L45,90L0,45ZM135,0L180,45L135,90L90,45ZM225,0L270,45L225,90L180,45ZM315,0L360,45L315,90L270,45Z"/>
    <path android:fillColor="#FFF8E7" android:fillAlpha="0.12" android:pathData="M90,110L135,155L90,200L45,155ZM270,110L315,155L270,200L225,155Z"/>
</vector>''', encoding='utf-8')

s = ui.read_text(encoding='utf-8')
if 'private const val SAADI_V038_DESIGN' not in s:
    anchor = s.find('\n@Composable')
    if anchor > 0:
        marker = '''\nprivate const val SAADI_V038_DESIGN = "QURAN_ZELLIJ_MOUCHARABIEH"\nprivate const val SAADI_SEARCH_BLOCK_MAX = 5\n'''
        s = s[:anchor] + marker + s[anchor:]
ui.write_text(s, encoding='utf-8')

b = build.read_text(encoding='utf-8')
b = re.sub(r'versionCode\s*=\s*\d+', 'versionCode = 11', b)
b = re.sub(r'versionName\s*=\s*"[^"]+"', 'versionName = "0.3.8"', b)
build.write_text(b, encoding='utf-8')

assert (util/'AyahSearch.kt').is_file()
assert (util/'AyahBlock.kt').is_file()
assert (res/'bg_zellij_saadi.xml').is_file()
assert 'SAADI_SEARCH_BLOCK_MAX = 5' in ui.read_text(encoding='utf-8')
assert 'versionName = "0.3.8"' in build.read_text(encoding='utf-8')
print('v0.3.8 core ready: normalized ayah search + max-5 ayah blocks + zellij resource')
