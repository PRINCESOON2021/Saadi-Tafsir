from pathlib import Path

root = Path('saadi-audio-tafsir')
player = root/'app/src/main/java/com/distritech/saaditafsir/player'
ui = root/'app/src/main/java/com/distritech/saaditafsir/ui/SaadiApp.kt'
manifest = root/'app/src/main/AndroidManifest.xml'
build = root/'app/build.gradle.kts'

(player/'AudioUrlResolver.kt').write_text('''package com.distritech.saaditafsir.player

/** Tafsir Al-Saadi audio mirrored by IslamWay. One MP3 per surah. */
object AudioUrlResolver {
    fun tafsirUrl(surah: Int, ayah: Int = 1): String? {
        if (surah !in 1..114) return null
        val n = surah.toString().padStart(3, '0')
        return "https://download.media.islamway.net/lessons/3239/10985/$n.mp3"
    }
}
''', encoding='utf-8')

(player/'AudioClient.kt').write_text('''package com.distritech.saaditafsir.player

import android.content.ComponentName
import android.content.Context
import androidx.core.content.ContextCompat
import androidx.media3.common.MediaItem
import androidx.media3.common.MediaMetadata
import androidx.media3.session.MediaController
import androidx.media3.session.SessionToken

object AudioClient {
    private var controller: MediaController? = null

    fun play(context: Context, url: String, title: String) {
        require(url.startsWith("https://")) { "HTTPS audio required" }
        val existing = controller
        if (existing != null) {
            existing.setMediaItem(mediaItem(url, title)); existing.prepare(); existing.play(); return
        }
        val token = SessionToken(context, ComponentName(context, AudioPlaybackService::class.java))
        val future = MediaController.Builder(context, token).buildAsync()
        future.addListener({ runCatching { future.get().also { controller = it; it.setMediaItem(mediaItem(url, title)); it.prepare(); it.play() } } }, ContextCompat.getMainExecutor(context))
    }

    fun toggle() { controller?.let { if (it.isPlaying) it.pause() else it.play() } }
    fun pause() { controller?.pause() }
    fun seekBy(deltaMs: Long) { controller?.let { it.seekTo((it.currentPosition + deltaMs).coerceIn(0L, it.duration.takeIf { d -> d > 0 } ?: Long.MAX_VALUE)) } }
    fun seekTo(positionMs: Long) { controller?.seekTo(positionMs.coerceAtLeast(0L)) }
    fun isPlaying(): Boolean = controller?.isPlaying == true
    fun currentPosition(): Long = controller?.currentPosition?.coerceAtLeast(0L) ?: 0L
    fun duration(): Long = controller?.duration?.takeIf { it > 0 } ?: 0L

    private fun mediaItem(url: String, title: String) = MediaItem.Builder().setUri(url)
        .setMediaMetadata(MediaMetadata.Builder().setTitle(title).build()).build()
}
''', encoding='utf-8')

s = ui.read_text(encoding='utf-8')
s = s.replace('import androidx.compose.foundation.layout.*', 'import androidx.compose.foundation.background\nimport androidx.compose.foundation.layout.*')
s = s.replace('import androidx.compose.ui.Alignment', 'import androidx.compose.ui.Alignment\nimport androidx.compose.ui.graphics.Brush\nimport androidx.compose.ui.graphics.Color')
s = s.replace('import kotlinx.coroutines.launch', 'import kotlinx.coroutines.delay\nimport kotlinx.coroutines.launch')

old_state = '    val listState = rememberLazyListState()\n'
new_state = '''    val listState = rememberLazyListState()\n    var playerTick by remember { mutableLongStateOf(0L) }\n    LaunchedEffect(Unit) { while (true) { delay(500); playerTick++ } }\n    val audioPosition = AudioClient.currentPosition()\n    val audioDuration = AudioClient.duration()\n    val audioPlaying = AudioClient.isPlaying()\n'''
s = s.replace(old_state, new_state)

s = s.replace('''    Scaffold(\n        snackbarHost = { SnackbarHost(snackbar) },\n        topBar = { TopAppBar(title = { Text(surah?.let { "سورة ${it.name}" } ?: "التفسير") }, navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowForward, null) } }) }\n    ) { pad ->\n        LazyColumn(state = listState, modifier = Modifier.padding(pad).padding(horizontal = 14.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {''', '''    Scaffold(\n        containerColor = Color(0xFFF5F0E4),\n        snackbarHost = { SnackbarHost(snackbar) },\n        topBar = { TopAppBar(\n            colors = TopAppBarDefaults.topAppBarColors(containerColor = Color(0xFF123C32), titleContentColor = Color.White, navigationIconContentColor = Color.White),\n            title = { Text(surah?.let { "سورة ${it.name}" } ?: "التفسير") }, navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowForward, null) } }) }\n    ) { pad ->\n        LazyColumn(state = listState, modifier = Modifier.padding(pad).background(Brush.verticalGradient(listOf(Color(0xFFF8F4E8), Color(0xFFEAF2EA)))).padding(horizontal = 14.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {''')

old_card = '''                Card(shape = RoundedCornerShape(18.dp), modifier = Modifier.fillMaxWidth()) {\n                    Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {\n                        IconButton(onClick = {\n                            val url = AudioUrlResolver.tafsirUrl(id, initialAyah)\n                            if (url == null) scope.launch { snackbar.showSnackbar("مصدر الصوت المرخّص لم يُضبط بعد") }\n                            else AudioClient.play(context, url, "تفسير سورة ${surah?.name.orEmpty()}")\n                        }) { Icon(Icons.Default.PlayCircle, null, modifier = Modifier.size(36.dp)) }\n                        Column(Modifier.weight(1f)) { Text("الاستماع للتفسير", fontWeight = FontWeight.Bold); Text("صوت حقيقي لتفسير السعدي • تشغيل عبر الإنترنت", fontSize = 12.sp) }\n                        IconButton(onClick = {\n                            val url = AudioUrlResolver.tafsirUrl(id, initialAyah)\n                            if (url == null) scope.launch { snackbar.showSnackbar("أضف رابط الصوت المرخّص أولًا") }\n                            else AudioDownloader.enqueue(context, url, "saadi_${id}_${initialAyah}.mp3")\n                        }) { Icon(Icons.Default.Download, null) }\n                    }\n                }'''
new_card = '''                Card(shape = RoundedCornerShape(22.dp), colors = CardDefaults.cardColors(containerColor = Color(0xFF123C32)), modifier = Modifier.fillMaxWidth()) {\n                    Column(Modifier.padding(16.dp)) {\n                        Row(verticalAlignment = Alignment.CenterVertically) {\n                            Text("۞  الاستماع لتفسير السعدي", color = Color(0xFFFFD98A), fontWeight = FontWeight.Bold, fontSize = 18.sp, modifier = Modifier.weight(1f))\n                            IconButton(onClick = { AudioUrlResolver.tafsirUrl(id)?.let { AudioDownloader.enqueue(context, it, "saadi_${id}.mp3") } }) { Icon(Icons.Default.Download, "تحميل", tint = Color.White) }\n                        }\n                        Text("تشغيل آمن عبر HTTPS • مصدر الصوت: طريق الإسلام", color = Color.White.copy(alpha=.78f), fontSize = 12.sp)\n                        Spacer(Modifier.height(8.dp))\n                        Slider(value = if (audioDuration > 0) audioPosition.toFloat().coerceIn(0f, audioDuration.toFloat()) else 0f, onValueChange = { AudioClient.seekTo(it.toLong()) }, valueRange = 0f..(audioDuration.takeIf { it > 0 } ?: 1L).toFloat())\n                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) { Text(formatTime(audioPosition), color = Color.White, fontSize = 11.sp); Text(formatTime(audioDuration), color = Color.White, fontSize = 11.sp) }\n                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center, verticalAlignment = Alignment.CenterVertically) {\n                            IconButton(onClick = { AudioClient.seekBy(-10000) }) { Icon(Icons.Default.Replay10, "رجوع 10 ثوان", tint = Color.White) }\n                            FilledIconButton(onClick = {\n                                if (audioDuration == 0L && audioPosition == 0L) AudioUrlResolver.tafsirUrl(id)?.let { AudioClient.play(context, it, "تفسير سورة ${surah?.name.orEmpty()}") } else AudioClient.toggle()\n                            }) { Icon(if (audioPlaying) Icons.Default.Pause else Icons.Default.PlayArrow, if (audioPlaying) "إيقاف مؤقت" else "تشغيل") }\n                            IconButton(onClick = { AudioClient.seekBy(10000) }) { Icon(Icons.Default.Forward10, "تقديم 10 ثوان", tint = Color.White) }\n                        }\n                    }\n                }'''
s = s.replace(old_card, new_card)

# Remove per-ayah whole-surah play button to avoid misleading sync.
s = s.replace('''                            IconButton(onClick = {\n                                vm.saveProgress(v.surah, v.ayah)\n                                val url = AudioUrlResolver.tafsirUrl(v.surah, v.ayah)\n                                if (url == null) scope.launch { snackbar.showSnackbar("الصوت لهذه الآية غير مربوط بعد") }\n                                else { AudioClient.play(context, url, "تفسير سورة ${surah?.name.orEmpty()}"); scope.launch { snackbar.showSnackbar("التسجيل الحالي للسورة كاملة؛ ربط الآيات بالزمن سيضاف لاحقًا") } }\n                            }) { Icon(Icons.Default.PlayArrow, null) }''', '')

s += '''\nprivate fun formatTime(ms: Long): String {\n    val total = (ms.coerceAtLeast(0L) / 1000)\n    return "%02d:%02d".format(total / 60, total % 60)\n}\n'''
ui.write_text(s, encoding='utf-8')

m = manifest.read_text(encoding='utf-8')
m = m.replace('android:allowBackup="true"', 'android:allowBackup="false"\n        android:usesCleartextTraffic="false"\n        android:networkSecurityConfig="@xml/network_security_config"')
manifest.write_text(m, encoding='utf-8')

xml = root/'app/src/main/res/xml/network_security_config.xml'
xml.parent.mkdir(parents=True, exist_ok=True)
xml.write_text('''<?xml version="1.0" encoding="utf-8"?>\n<network-security-config>\n    <base-config cleartextTrafficPermitted="false">\n        <trust-anchors><certificates src="system" /></trust-anchors>\n    </base-config>\n</network-security-config>\n''', encoding='utf-8')

b = build.read_text(encoding='utf-8').replace('versionCode = 5', 'versionCode = 6').replace('versionName = "0.3.2"', 'versionName = "0.3.3"')
build.write_text(b, encoding='utf-8')

# Guard rails for CI.
assert 'download.media.islamway.net' in (player/'AudioUrlResolver.kt').read_text()
assert 'allowBackup="false"' in manifest.read_text()
assert 'FilledIconButton' in ui.read_text()
print('v0.3.3 upgrade applied')
