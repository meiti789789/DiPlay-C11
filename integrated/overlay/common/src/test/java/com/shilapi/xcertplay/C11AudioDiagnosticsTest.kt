package com.shilapi.xcertplay

import android.media.AudioManager
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28, 33])
class C11AudioDiagnosticsTest {
    @Test fun reportObservesAudioWithoutChangingIt() {
        val context = RuntimeEnvironment.getApplication()
        val audio = context.getSystemService(AudioManager::class.java)
        audio.mode = AudioManager.MODE_IN_COMMUNICATION
        audio.setStreamVolume(AudioManager.STREAM_MUSIC, 3, 0)
        val mode = audio.mode
        val volume = audio.getStreamVolume(AudioManager.STREAM_MUSIC)
        val speaker = audio.isSpeakerphoneOn
        val sco = audio.isBluetoothScoOn
        val report = C11AudioDiagnostics.report(context)
        assertTrue(report, report.contains("mode=$mode"))
        assertTrue(report, report.contains("3:volume=$volume/"))
        assertTrue(report, report.contains("not proof of the active playback route"))
        assertEquals(mode, audio.mode)
        assertEquals(volume, audio.getStreamVolume(AudioManager.STREAM_MUSIC))
        assertEquals(speaker, audio.isSpeakerphoneOn)
        assertEquals(sco, audio.isBluetoothScoOn)
    }
}
