from pathlib import Path
import re

root = Path('saadi-audio-tafsir')
player = root / 'app/src/main/java/com/distritech/saaditafsir/player'
player.mkdir(parents=True, exist_ok=True)
ui = root / 'app/src/main/java/com/distritech/saaditafsir/ui/SaadiApp.kt'
build = root / 'app/build.gradle.kts'
manifest = root / 'app/src/main/AndroidManifest.xml'

# Keep the exact MP3 source that already works on the user's phone.
(player / 'AudioUrlResolver.kt').write_text('''package com.distritech.saaditafsir.player

object AudioUrlResolver {
    fun tafsirUrl(surah: Int, ayah: Int = 1): String? {
        if (surah !in 1..114) return null
        val n = surah.toString().padStart(3, '0')
        return "https://d1.islamhouse.com/data/ar/ih_sounds/chain/Tafceer_Saadi_Al-Ahmad/ar_${n}_Tafceer_Saadi_Al-Ahmad.mp3"
    }
}
''', encoding='utf-8')

# Preserve Media3 playback and add real app-level volume control.
(player / 'AudioClient.kt').write_text('''package com.distritech.saaditafsir.player

import android.content.ComponentName
import android.content.Context
import androidx.core.content.ContextCompat
import androidx.media3.common.MediaItem
import androidx.media3.common.MediaMetadata
import androidx.media3.session.MediaController
import androidx.media3.session.SessionToken

object AudioClient {
    private var controller: MediaController? = null
    private var requestedVolume: Float = 1f

    fun play(context: Context, url: String, title: String, onError: ((String) -> Unit)? = null) {
        if (!url.startsWith("https://")) { onError?.invoke("رابط الصوت غير آمن"); return }
        val ready = controller
        if (ready != null) {
            ready.volume = requestedVolume
            ready.setMediaItem(item(url, title))
            ready.prepare()
            ready.play()
            return
        }
        val future = MediaController.Builder(
            context,
            SessionToken(context, ComponentName(context, AudioPlaybackService::class.java))
        ).buildAsync()
        future.addListener({
            try {
                val c = future.get()
                controller = c
                c.volume = requestedVolume
                c.setMediaItem(item(url, title))
                c.prepare()
                c.play()
            } catch (e: Exception) {
                onError?.invoke("تعذر تشغيل الصوت")
            }
        }, ContextCompat.getMainExecutor(context))
    }

    fun playPause() { controller?.let { if (it.isPlaying) it.pause() else it.play() } }
    fun pause() { controller?.pause() }
    fun seekBack10() { seekBy(-10_000L) }
    fun seekForward10() { seekBy(10_000L) }
    fun seekBy(delta: Long) { controller?.let { c ->
        val end = c.duration.takeIf { it > 0 } ?: Long.MAX_VALUE
        c.seekTo((c.currentPosition + delta).coerceIn(0L, end))
    } }
    fun setVolume(value: Float) {
        requestedVolume = value.coerceIn(0f, 1f)
        controller?.volume = requestedVolume
    }
    fun volume(): Float = requestedVolume
    fun currentPosition(): Long = controller?.currentPosition?.coerceAtLeast(0L) ?: 0L
    fun duration(): Long = controller?.duration?.takeIf { it > 0 } ?: 0L
    fun isPlaying(): Boolean = controller?.isPlaying == true

    private fun item(url: String, title: String) = MediaItem.Builder()
        .setUri(url)
        .setMediaMetadata(MediaMetadata.Builder().setTitle(title).build())
        .build()
}
''', encoding='utf-8')

s = ui.read_text(encoding='utf-8')

# Match either the original V1 player block or the previous v0.3.4 block.
old_v1 = '''                        IconButton(onClick = {\n                            val url = AudioUrlResolver.tafsirUrl(id, initialAyah)\n                            if (url == null) scope.launch { snackbar.showSnackbar("مصدر الصوت المرخّص لم يُضبط بعد") }\n                            else AudioClient.play(context, url, "تفسير سورة ${surah?.name.orEmpty()}")\n                        }) { Icon(Icons.Default.PlayCircle, null, modifier = Modifier.size(36.dp)) }\n                        Column(Modifier.weight(1f)) { Text("الاستماع للتفسير", fontWeight = FontWeight.Bold); Text("تشغيل في الخلفية عبر Media3", fontSize = 12.sp) }\n                        IconButton(onClick = {\n                            val url = AudioUrlResolver.tafsirUrl(id, initialAyah)\n                            if (url == null) scope.launch { snackbar.showSnackbar("أضف رابط الصوت المرخّص أولًا") }\n                            else AudioDownloader.enqueue(context, url, "saadi_${id}_${initialAyah}.mp3")\n                        }) { Icon(Icons.Default.Download, null) }'''

old_v034 = '''                        Column(Modifier.fillMaxWidth()) {\n                            Text("الاستماع إلى تفسير السعدي", fontWeight = FontWeight.Bold, color = Color(0xFF123C32))\n                            Text("النص المعروض أدناه هو نص السورة والتفسير المرتبطان بهذا التسجيل الكامل", fontSize = 12.sp, color = Color(0xFF6B5A32))\n                            Spacer(Modifier.height(8.dp))\n                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly, verticalAlignment = Alignment.CenterVertically) {\n                                IconButton(onClick = { AudioClient.seekBack10() }) { Icon(Icons.Default.Replay10, "رجوع 10 ثوان", tint = Color(0xFF1B5A49)) }\n                                IconButton(onClick = {\n                                    val url = AudioUrlResolver.tafsirUrl(id, 1)\n                                    if (url == null) scope.launch { snackbar.showSnackbar("الصوت غير متوفر") }\n                                    else AudioClient.play(context, url, "تفسير سورة ${surah?.name.orEmpty()}") { msg -> scope.launch { snackbar.showSnackbar(msg) } }\n                                }) { Icon(Icons.Default.PlayCircle, "تشغيل", modifier = Modifier.size(44.dp), tint = Color(0xFFC58A46)) }\n                                IconButton(onClick = { AudioClient.playPause() }) { Icon(Icons.Default.PauseCircle, "تشغيل أو إيقاف مؤقت", modifier = Modifier.size(40.dp), tint = Color(0xFF123C32)) }\n                                IconButton(onClick = { AudioClient.seekForward10() }) { Icon(Icons.Default.Forward10, "تقديم 10 ثوان", tint = Color(0xFF1B5A49)) }\n                                IconButton(onClick = {\n                                    val url = AudioUrlResolver.tafsirUrl(id, 1)\n                                    if (url == null) scope.launch { snackbar.showSnackbar("الصوت غير متوفر") }\n                                    else AudioDownloader.enqueue(context, url, "saadi_${id}.mp3")\n                                }) { Icon(Icons.Default.Download, "تحميل", tint = Color(0xFFC58A46)) }\n                            }\n                        }'''

new = '''                        var playerVolume by remember { mutableStateOf(AudioClient.volume()) }\n                        Surface(\n                            modifier = Modifier.fillMaxWidth(),\n                            shape = RoundedCornerShape(22.dp),\n                            color = Color(0xFFFFF8E7),\n                            border = BorderStroke(1.dp, Color(0xFFD4AF37)),\n                            shadowElevation = 6.dp\n                        ) {\n                            Column(Modifier.fillMaxWidth().padding(16.dp)) {\n                                Row(verticalAlignment = Alignment.CenterVertically) {\n                                    Text("۞", fontSize = 26.sp, color = Color(0xFFD4AF37))\n                                    Spacer(Modifier.width(8.dp))\n                                    Column(Modifier.weight(1f)) {\n                                        Text("تفسير السعدي المسموع", fontWeight = FontWeight.Bold, color = Color(0xFF0E4D3A), fontSize = 18.sp)\n                                        Text("سورة ${surah?.name.orEmpty()} • النص والتفسير مرتبطان بالتسجيل الكامل", fontSize = 12.sp, color = Color(0xFF6B5A32))\n                                    }\n                                }\n                                Spacer(Modifier.height(12.dp))\n                                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly, verticalAlignment = Alignment.CenterVertically) {\n                                    IconButton(onClick = { AudioClient.seekBack10() }) { Icon(Icons.Default.Replay10, "رجوع 10 ثوان", tint = Color(0xFF0E4D3A)) }\n                                    IconButton(onClick = {\n                                        val url = AudioUrlResolver.tafsirUrl(id, 1)\n                                        if (url == null) scope.launch { snackbar.showSnackbar("الصوت غير متوفر") }\n                                        else AudioClient.play(context, url, "تفسير سورة ${surah?.name.orEmpty()}") { msg -> scope.launch { snackbar.showSnackbar(msg) } }\n                                    }) { Icon(Icons.Default.PlayCircle, "تشغيل", modifier = Modifier.size(48.dp), tint = Color(0xFFD4AF37)) }\n                                    IconButton(onClick = { AudioClient.playPause() }) { Icon(Icons.Default.PauseCircle, "تشغيل أو إيقاف مؤقت", modifier = Modifier.size(42.dp), tint = Color(0xFF0E4D3A)) }\n                                    IconButton(onClick = { AudioClient.seekForward10() }) { Icon(Icons.Default.Forward10, "تقديم 10 ثوان", tint = Color(0xFF0E4D3A)) }\n                                    IconButton(onClick = {\n                                        val url = AudioUrlResolver.tafsirUrl(id, 1)\n                                        if (url == null) scope.launch { snackbar.showSnackbar("الصوت غير متوفر") }\n                                        else AudioDownloader.enqueue(context, url, "saadi_${id}.mp3")\n                                    }) { Icon(Icons.Default.Download, "تحميل", tint = Color(0xFFD4AF37)) }\n                                }\n                                Spacer(Modifier.height(8.dp))\n                                Row(verticalAlignment = Alignment.CenterVertically) {\n                                    Icon(Icons.Default.VolumeUp, "مستوى الصوت", tint = Color(0xFF0E4D3A))\n                                    Spacer(Modifier.width(8.dp))\n                                    Slider(\n                                        value = playerVolume,\n                                        onValueChange = { playerVolume = it; AudioClient.setVolume(it) },\n                                        valueRange = 0f..1f,\n                                        modifier = Modifier.weight(1f)\n                                    )\n                                    Text("${(playerVolume * 100).toInt()}%", fontSize = 12.sp, color = Color(0xFF6B5A32))\n                                }\n                            }\n                        }'''

if old_v034 in s:
    s = s.replace(old_v034, new, 1)
elif old_v1 in s:
    s = s.replace(old_v1, new, 1)
else:
    raise SystemExit('V035_PLAYER_TARGET_NOT_FOUND: refusing unchanged UI')

imports = [
    'import androidx.compose.ui.graphics.Color',
    'import androidx.compose.foundation.BorderStroke',
    'import androidx.compose.foundation.shape.RoundedCornerShape',
    'import androidx.compose.foundation.layout.Arrangement',
    'import androidx.compose.runtime.remember',
    'import androidx.compose.runtime.mutableStateOf',
    'import androidx.compose.runtime.getValue',
    'import androidx.compose.runtime.setValue',
]
for imp in imports:
    if imp not in s:
        lines = s.splitlines()
        pos = max([i for i,l in enumerate(lines) if l.startswith('import ')], default=0) + 1
        lines.insert(pos, imp)
        s = '\n'.join(lines) + '\n'
ui.write_text(s, encoding='utf-8')

m = manifest.read_text(encoding='utf-8')
m = m.replace('android:allowBackup="true"', 'android:allowBackup="false"')
if 'android:usesCleartextTraffic=' not in m:
    m = m.replace('<application', '<application\n        android:usesCleartextTraffic="false"', 1)
manifest.write_text(m, encoding='utf-8')

b = build.read_text(encoding='utf-8')
b = re.sub(r'versionCode\s*=\s*\d+', 'versionCode = 8', b)
b = re.sub(r'versionName\s*=\s*"[^"]+"', 'versionName = "0.3.5"', b)
build.write_text(b, encoding='utf-8')

final_ui = ui.read_text(encoding='utf-8')
assert 'AudioClient.setVolume(it)' in final_ui
assert 'RoundedCornerShape(22.dp)' in final_ui
assert 'Color(0xFFFFF8E7)' in final_ui
assert 'تفسير السعدي المسموع' in final_ui
assert 'Icons.Default.VolumeUp' in final_ui
assert 'd1.islamhouse.com/data/ar/ih_sounds/chain/Tafceer_Saadi_Al-Ahmad' in (player/'AudioUrlResolver.kt').read_text(encoding='utf-8')
assert 'versionName = "0.3.5"' in build.read_text(encoding='utf-8')
print('v0.3.5 applied: working V1 audio preserved + visible Islamic player card + volume slider')
