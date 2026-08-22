package com.distritech.saaditafsir.player

import android.content.Context
import android.speech.tts.TextToSpeech
import java.util.Locale

object TafsirTts {
    private var tts: TextToSpeech? = null
    private var ready = false
    private var initializing = false
    private val pending = mutableListOf<Pair<String, String>>()

    private fun ensure(context: Context, onReady: (() -> Unit)? = null) {
        if (ready && tts != null) {
            onReady?.invoke()
            return
        }
        if (initializing) return
        initializing = true
        tts = TextToSpeech(context.applicationContext) { status ->
            initializing = false
            if (status == TextToSpeech.SUCCESS) {
                val engine = tts ?: return@TextToSpeech
                val result = engine.setLanguage(Locale("ar"))
                ready = result != TextToSpeech.LANG_MISSING_DATA && result != TextToSpeech.LANG_NOT_SUPPORTED
                engine.setSpeechRate(0.92f)
                if (ready) {
                    val copy = pending.toList()
                    pending.clear()
                    copy.forEachIndexed { index, (text, id) ->
                        engine.speak(text, if (index == 0) TextToSpeech.QUEUE_FLUSH else TextToSpeech.QUEUE_ADD, null, id)
                    }
                    onReady?.invoke()
                }
            }
        }
    }

    fun speak(context: Context, text: String, utteranceId: String) {
        if (text.isBlank()) return
        val engine = tts
        if (ready && engine != null) {
            engine.speak(text, TextToSpeech.QUEUE_FLUSH, null, utteranceId)
        } else {
            pending.clear()
            pending += text to utteranceId
            ensure(context)
        }
    }

    fun speakAll(context: Context, texts: List<String>, prefix: String = "saadi") {
        val clean = texts.filter { it.isNotBlank() }
        if (clean.isEmpty()) return
        val engine = tts
        if (ready && engine != null) {
            clean.forEachIndexed { index, text ->
                engine.speak(text, if (index == 0) TextToSpeech.QUEUE_FLUSH else TextToSpeech.QUEUE_ADD, null, "$prefix-$index")
            }
        } else {
            pending.clear()
            clean.forEachIndexed { index, text -> pending += text to "$prefix-$index" }
            ensure(context)
        }
    }

    fun stop() {
        tts?.stop()
        pending.clear()
    }
}
