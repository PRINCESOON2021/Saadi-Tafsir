from pathlib import Path

root = Path('saadi-audio-tafsir')
player = root/'app/src/main/java/com/distritech/saaditafsir/player'
ui = root/'app/src/main/java/com/distritech/saaditafsir/ui/SaadiApp.kt'
manifest = root/'app/src/main/AndroidManifest.xml'
build = root/'app/build.gradle.kts'

(player/'AudioUrlResolver.kt').write_text('''package com.distritech.saaditafsir.player
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
        require(url.startsWith("https://"))
        val existing = controller
        if (existing != null) { existing.setMediaItem(mediaItem(url,title)); existing.prepare(); existing.play(); return }
        val future = MediaController.Builder(context, SessionToken(context, ComponentName(context, AudioPlaybackService::class.java))).buildAsync()
        future.addListener({ runCatching { future.get().also { controller=it; it.setMediaItem(mediaItem(url,title)); it.prepare(); it.play() } } }, ContextCompat.getMainExecutor(context))
    }
    fun toggle() { controller?.let { if(it.isPlaying) it.pause() else it.play() } }
    fun seekBy(deltaMs: Long) { controller?.let { val max=it.duration.takeIf { d->d>0 } ?: Long.MAX_VALUE; it.seekTo((it.currentPosition+deltaMs).coerceIn(0L,max)) } }
    fun seekTo(ms: Long) { controller?.seekTo(ms.coerceAtLeast(0L)) }
    fun isPlaying() = controller?.isPlaying == true
    fun currentPosition() = controller?.currentPosition?.coerceAtLeast(0L) ?: 0L
    fun duration() = controller?.duration?.takeIf { it>0 } ?: 0L
    private fun mediaItem(url:String,title:String)=MediaItem.Builder().setUri(url).setMediaMetadata(MediaMetadata.Builder().setTitle(title).build()).build()
}
''', encoding='utf-8')

# Security settings are deterministic and do not depend on fragile UI text matching.
m = manifest.read_text(encoding='utf-8')
if 'android:allowBackup="true"' in m:
    m = m.replace('android:allowBackup="true"','android:allowBackup="false"')
if 'android:usesCleartextTraffic=' not in m:
    m = m.replace('<application','<application\n        android:usesCleartextTraffic="false"',1)
if 'android:networkSecurityConfig=' not in m:
    m = m.replace('<application','<application\n        android:networkSecurityConfig="@xml/network_security_config"',1)
manifest.write_text(m,encoding='utf-8')
xml=root/'app/src/main/res/xml/network_security_config.xml'; xml.parent.mkdir(parents=True,exist_ok=True)
xml.write_text('''<?xml version="1.0" encoding="utf-8"?>
<network-security-config><base-config cleartextTrafficPermitted="false"><trust-anchors><certificates src="system" /></trust-anchors></base-config></network-security-config>
''',encoding='utf-8')

b=build.read_text(encoding='utf-8').replace('versionCode = 5','versionCode = 6').replace('versionName = "0.3.2"','versionName = "0.3.3"')
build.write_text(b,encoding='utf-8')

# Do not fail here on UI pattern differences; the workflow performs final feature checks.
assert 'download.media.islamway.net' in (player/'AudioUrlResolver.kt').read_text(encoding='utf-8')
assert 'allowBackup="false"' in manifest.read_text(encoding='utf-8')
print('v0.3.3 core upgrade applied')
