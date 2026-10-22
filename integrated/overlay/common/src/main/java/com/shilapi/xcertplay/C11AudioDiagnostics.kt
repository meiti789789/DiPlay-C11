package com.shilapi.xcertplay

import android.content.Context
import android.media.AudioManager

/** Read-only snapshot. Never requests focus, changes mode, volume, SCO or vehicle settings. */
internal object C11AudioDiagnostics {
    fun report(context: Context): String = runCatching {
        val audio = context.getSystemService(AudioManager::class.java)
            ?: return "C11 audio snapshot unavailable"
        val streams = listOf(AudioManager.STREAM_MUSIC, AudioManager.STREAM_VOICE_CALL,
            AudioManager.STREAM_BLUETOOTH_SCO).joinToString { stream ->
            "$stream:volume=${audio.getStreamVolume(stream)}/${audio.getStreamMaxVolume(stream)}:muted=${audio.isStreamMute(stream)}"
        }
        val outputs = audio.getDevices(AudioManager.GET_DEVICES_OUTPUTS).joinToString { "${it.id}:${it.type}" }
        "C11 audio snapshot mode=${audio.mode} musicActive=${audio.isMusicActive} " +
            "speakerphone=${audio.isSpeakerphoneOn} bluetoothSco=${audio.isBluetoothScoOn} " +
            "bluetoothA2dp=${audio.isBluetoothA2dpOn} streams=[$streams] availableOutputs=[$outputs] " +
            "(availableOutputs are capabilities, not proof of the active playback route)"
    }.getOrElse { "C11 audio snapshot failed=${it.javaClass.simpleName}" }
}
