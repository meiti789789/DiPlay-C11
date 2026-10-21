package com.shilapi.xcertplay.media

import android.Manifest
import android.media.AudioRecord
import android.media.MediaRecorder
import com.shilapi.xcertplay.airplay.MicrophoneConfig
import java.net.InetAddress
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicReference
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config
import org.robolectric.shadows.ShadowAudioRecord

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], manifest = Config.NONE)
class C11SilentCaptureTest {
    @Test fun digitalZeroRecoveryRestartsTheSameSourceAndCaptureContinuesAfterwards() {
        shadowOf(RuntimeEnvironment.getApplication()).grantPermissions(Manifest.permission.RECORD_AUDIO)
        val recovered = AtomicBoolean(false)
        val resumed = CountDownLatch(1)
        val recorder = AtomicReference<AudioRecord>()
        ShadowAudioRecord.setSourceProvider { record ->
            recorder.set(record)
            object : ShadowAudioRecord.AudioRecordSource {
                override fun readInByteArray(buffer: ByteArray, offset: Int, size: Int, blocking: Boolean): Int {
                    Thread.sleep(5)
                    buffer.fill(0, offset, offset + size)
                    if (recovered.get()) { buffer[offset] = 1; resumed.countDown() }
                    return size
                }
            }
        }
        val uplink = MicrophoneUplink(
            MicrophoneConfig(audioType = "telephony", sampleRate = 16_000, channels = 1,
                payloadType = 100, frameMillis = 20, host = InetAddress.getLoopbackAddress(), port = 9, key = ByteArray(32)),
            telephonySourceOverride = MediaRecorder.AudioSource.VOICE_RECOGNITION,
            recoverSilentCapture = true, silentCaptureMillis = 25,
            onDiagnostic = { if (it.startsWith("C11 microphone silent capture recovery")) recovered.set(true) },
        )
        try {
            assertTrue(uplink.start())
            assertTrue("capture must resume after bounded digital-zero recovery", resumed.await(5, TimeUnit.SECONDS))
            assertEquals(MediaRecorder.AudioSource.VOICE_RECOGNITION, recorder.get().audioSource)
            assertEquals(AudioRecord.RECORDSTATE_RECORDING, recorder.get().recordingState)
        } finally { uplink.close(); ShadowAudioRecord.clearSource() }
        assertEquals(AudioRecord.STATE_UNINITIALIZED, recorder.get().state)
    }
}
