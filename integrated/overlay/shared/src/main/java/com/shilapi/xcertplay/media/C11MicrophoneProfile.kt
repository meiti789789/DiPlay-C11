package com.shilapi.xcertplay.media

import android.content.Context
import android.media.MediaRecorder
import android.os.Build

/** Optional capture-source selection only; no system properties, volume or OEM HAL writes. */
object C11MicrophoneProfile {
    fun supported(fingerprint: String = Build.FINGERPRINT, model: String = Build.MODEL) =
        "$fingerprint $model".contains("msmnile_gvmq", true)
    fun selected(context: Context) = context.getSharedPreferences("c11-call", Context.MODE_PRIVATE)
        .getInt("source", 0).takeIf { it in 0..2 } ?: 0
    fun save(context: Context, value: Int) {
        context.getSharedPreferences("c11-call", Context.MODE_PRIVATE).edit().putInt("source", value.takeIf { it in 0..2 } ?: 0).apply()
    }
    fun resolve(selection: Int, supported: Boolean): Int? = if (!supported) null else when (selection) {
        1 -> MediaRecorder.AudioSource.VOICE_RECOGNITION
        2 -> MediaRecorder.AudioSource.MIC
        else -> null
    }
    fun source(context: Context?): Int? = context?.let { resolve(selected(it), supported()) }
}
