from pathlib import Path
import re

root = Path('saadi-audio-tafsir')
player = root / 'app/src/main/java/com/distritech/saaditafsir/player'
ui = root / 'app/src/main/java/com/distritech/saaditafsir/ui/SaadiApp.kt'
build = root / 'app/build.gradle.kts'
client = player / 'AudioClient.kt'

# Preserve the working IslamHouse MP3 source. Only improve track handling.
c = client.read_text(encoding='utf-8')
needle = '''    fun playPause() { controller?.let { if (it.isPlaying) it.pause() else it.play() } }'''
insert = '''    fun playResumable(context: Context, url: String, title: String, resumeKey: String, onError: ((String) -> Unit)? = null) {
        if (!url.startsWith("https://")) { onError?.invoke("رابط الصوت غير آمن"); return }
        val saved = context.getSharedPreferences("saadi_audio_positions", Context.MODE_PRIVATE).getLong(resumeKey, 0L)
        fun start(c: MediaController) {
            c.volume = requestedVolume
            c.setMediaItem(item(url, title))
            c.prepare()
            if (saved > 0L) c.seekTo(saved)
            c.play()
        }
        val ready = controller
        if (ready != null) { start(ready); return }
        val future = MediaController.Builder(context, SessionToken(context, ComponentName(context, AudioPlaybackService::class.java))).buildAsync()
        future.addListener({
            try { future.get().also { controller = it; start(it) } }
            catch (e: Exception) { onError?.invoke("تعذر تشغيل الصوت") }
        }, ContextCompat.getMainExecutor(context))
    }

    fun savePosition(context: Context, resumeKey: String) {
        val p = currentPosition()
        if (p > 0L) context.getSharedPreferences("saadi_audio_positions", Context.MODE_PRIVATE)
            .edit().putLong(resumeKey, p).apply()
    }
    fun clearPosition(context: Context, resumeKey: String) {
        context.getSharedPreferences("saadi_audio_positions", Context.MODE_PRIVATE).edit().remove(resumeKey).apply()
    }
    fun seekTo(positionMs: Long) { controller?.seekTo(positionMs.coerceAtLeast(0L)) }

    fun playPause() { controller?.let { if (it.isPlaying) it.pause() else it.play() } }'''
if needle not in c:
    raise SystemExit('V036_AUDIOCLIENT_TARGET_NOT_FOUND')
c = c.replace(needle, insert, 1)
client.write_text(c, encoding='utf-8')

s = ui.read_text(encoding='utf-8')
# Add state + polling immediately before the Islamic player Surface.
needle_state = '''                        var playerVolume by remember { mutableStateOf(AudioClient.volume()) }
                        Surface('''
replacement_state = '''                        var playerVolume by remember { mutableStateOf(AudioClient.volume()) }
                        var playerPosition by remember { mutableStateOf(0L) }
                        var playerDuration by remember { mutableStateOf(0L) }
                        LaunchedEffect(id) {
                            while (true) {
                                playerPosition = AudioClient.currentPosition()
                                playerDuration = AudioClient.duration()
                                AudioClient.savePosition(context, "surah-$id")
                                delay(750)
                            }
                        }
                        Surface('''
if needle_state not in s:
    raise SystemExit('V036_PLAYER_STATE_TARGET_NOT_FOUND')
s = s.replace(needle_state, replacement_state, 1)

# Main play button now resumes this surah from the last saved position.
s = s.replace(
    '''else AudioClient.play(context, url, "تفسير سورة ${surah?.name.orEmpty()}") { msg -> scope.launch { snackbar.showSnackbar(msg) } }''',
    '''else AudioClient.playResumable(context, url, "تفسير سورة ${surah?.name.orEmpty()}", "surah-$id") { msg -> scope.launch { snackbar.showSnackbar(msg) } }''',
    1
)

# Insert a real seek bar + elapsed/total time above the volume control.
needle_volume = '''                                Spacer(Modifier.height(8.dp))
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Icon(Icons.Default.VolumeUp, "مستوى الصوت", tint = Color(0xFF0E4D3A))'''
replacement_volume = '''                                Spacer(Modifier.height(10.dp))
                                Slider(
                                    value = if (playerDuration > 0L) (playerPosition.toFloat() / playerDuration.toFloat()).coerceIn(0f, 1f) else 0f,
                                    onValueChange = { fraction ->
                                        if (playerDuration > 0L) {
                                            val target = (playerDuration * fraction).toLong()
                                            AudioClient.seekTo(target)
                                            playerPosition = target
                                            AudioClient.savePosition(context, "surah-$id")
                                        }
                                    },
                                    valueRange = 0f..1f,
                                    modifier = Modifier.fillMaxWidth()
                                )
                                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                    Text("%02d:%02d".format(playerPosition / 60000, (playerPosition / 1000) % 60), fontSize = 12.sp, color = Color(0xFF6B5A32))
                                    Text("%02d:%02d".format(playerDuration / 60000, (playerDuration / 1000) % 60), fontSize = 12.sp, color = Color(0xFF6B5A32))
                                }
                                Spacer(Modifier.height(8.dp))
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Icon(Icons.Default.VolumeUp, "مستوى الصوت", tint = Color(0xFF0E4D3A))'''
if needle_volume not in s:
    raise SystemExit('V036_PROGRESS_TARGET_NOT_FOUND')
s = s.replace(needle_volume, replacement_volume, 1)

imports = [
    'import androidx.compose.runtime.LaunchedEffect',
    'import kotlinx.coroutines.delay',
]
for imp in imports:
    if imp not in s:
        lines = s.splitlines()
        pos = max([i for i,l in enumerate(lines) if l.startswith('import ')], default=0) + 1
        lines.insert(pos, imp)
        s = '\n'.join(lines) + '\n'
ui.write_text(s, encoding='utf-8')

b = build.read_text(encoding='utf-8')
b = re.sub(r'versionCode\s*=\s*\d+', 'versionCode = 9', b)
b = re.sub(r'versionName\s*=\s*"[^"]+"', 'versionName = "0.3.6"', b)
build.write_text(b, encoding='utf-8')

final_ui = ui.read_text(encoding='utf-8')
final_client = client.read_text(encoding='utf-8')
assert 'AudioClient.playResumable' in final_ui
assert 'AudioClient.seekTo(target)' in final_ui
assert 'AudioClient.savePosition(context, "surah-$id")' in final_ui
assert 'playerPosition' in final_ui and 'playerDuration' in final_ui
assert 'saadi_audio_positions' in final_client
assert 'fun seekTo(positionMs: Long)' in final_client
assert 'versionName = "0.3.6"' in build.read_text(encoding='utf-8')
print('v0.3.6 applied: seekable track + elapsed/total time + automatic resume per surah')
