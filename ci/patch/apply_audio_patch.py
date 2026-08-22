from pathlib import Path

ui = Path('saadi-audio-tafsir/app/src/main/java/com/distritech/saaditafsir/ui/SaadiApp.kt')
s = ui.read_text()

if 'import com.distritech.saaditafsir.player.TafsirTts' not in s:
    s = s.replace('import com.distritech.saaditafsir.player.AudioUrlResolver\n', 'import com.distritech.saaditafsir.player.AudioUrlResolver\nimport com.distritech.saaditafsir.player.TafsirTts\n')

old = '''                        IconButton(onClick = {\n                            val url = AudioUrlResolver.tafsirUrl(id, initialAyah)\n                            if (url == null) scope.launch { snackbar.showSnackbar("مصدر الصوت المرخّص لم يُضبط بعد") }\n                            else AudioClient.play(context, url, "تفسير سورة ${surah?.name.orEmpty()}")\n                        }) { Icon(Icons.Default.PlayCircle, null, modifier = Modifier.size(36.dp)) }\n                        Column(Modifier.weight(1f)) { Text("الاستماع للتفسير", fontWeight = FontWeight.Bold); Text("تشغيل في الخلفية عبر Media3", fontSize = 12.sp) }\n                        IconButton(onClick = {\n                            val url = AudioUrlResolver.tafsirUrl(id, initialAyah)\n                            if (url == null) scope.launch { snackbar.showSnackbar("أضف رابط الصوت المرخّص أولًا") }\n                            else AudioDownloader.enqueue(context, url, "saadi_${id}_${initialAyah}.mp3")\n                        }) { Icon(Icons.Default.Download, null) }'''

new = '''                        IconButton(onClick = {\n                            val start = verses.indexOfFirst { it.ayah == initialAyah }.let { if (it < 0) 0 else it }\n                            TafsirTts.speakAll(context, verses.drop(start).map { "الآية ${it.ayah}. ${it.tafsirText}" }, "surah-$id")\n                        }) { Icon(Icons.Default.PlayCircle, "استماع", modifier = Modifier.size(36.dp)) }\n                        Column(Modifier.weight(1f)) { Text("الاستماع للتفسير", fontWeight = FontWeight.Bold); Text("قراءة عربية عبر محرك الصوت في الهاتف", fontSize = 12.sp) }\n                        IconButton(onClick = { TafsirTts.stop() }) { Icon(Icons.Default.StopCircle, "إيقاف") }'''

if old in s:
    s = s.replace(old, new)

old2 = '''                                val url = AudioUrlResolver.tafsirUrl(v.surah, v.ayah)\n                                if (url == null) scope.launch { snackbar.showSnackbar("الصوت لهذه الآية غير مربوط بعد") }\n                                else AudioClient.play(context, url, "سورة ${surah?.name.orEmpty()} - الآية ${v.ayah}")'''
new2 = '''                                TafsirTts.speak(context, "الآية ${v.ayah}. ${v.tafsirText}", "${v.surah}-${v.ayah}")'''
if old2 in s:
    s = s.replace(old2, new2)

ui.write_text(s)

build = Path('saadi-audio-tafsir/app/build.gradle.kts')
b = build.read_text().replace('versionCode = 3', 'versionCode = 4').replace('versionName = "0.3.0"', 'versionName = "0.3.1"')
build.write_text(b)
