package com.shilapi.xcertplay.media
import android.media.MediaRecorder
import org.junit.Assert.*
import org.junit.Test
class C11MicrophoneProfileTest {
    @Test fun defaultsAndUnrecognizedProfilesKeepUpstreamSources() {
        assertNull(C11MicrophoneProfile.resolve(0,true))
        assertNull(C11MicrophoneProfile.resolve(1,false))
        assertNull(C11MicrophoneProfile.resolve(99,true))
    }
    @Test fun knownC11CanOptIntoOneOfTwoPublicCaptureSources() {
        assertEquals(MediaRecorder.AudioSource.VOICE_RECOGNITION,C11MicrophoneProfile.resolve(1,true))
        assertEquals(MediaRecorder.AudioSource.MIC,C11MicrophoneProfile.resolve(2,true))
        assertTrue(C11MicrophoneProfile.supported("qti/msmnile_gvmq:9", "unknown"))
        assertFalse(C11MicrophoneProfile.supported("byd", "other"))
    }
}
