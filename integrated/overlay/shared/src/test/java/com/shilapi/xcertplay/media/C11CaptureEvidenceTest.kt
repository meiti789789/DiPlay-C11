package com.shilapi.xcertplay.media

import com.shilapi.xcertplay.airplay.AudioCodecKind
import com.shilapi.xcertplay.airplay.MicrophoneConfig
import java.net.InetAddress
import org.junit.Assert.*
import org.junit.Test

class C11CaptureEvidenceTest {
    @Test fun separatesLiveInputFromSilentProcessedOutputAndResetsBothWindows() {
        val config = MicrophoneConfig("telephony", 48000, 1, 100, 20,
            InetAddress.getByName("198.51.100.20"), 54321, ByteArray(32), AudioCodecKind.OPUS)
        val reports = mutableListOf<String>()
        val stats = MicrophoneCaptureStats(config, reports::add)
        val input = byteArrayOf(0, 64)
        val copy = input.copyOf()
        stats.inputLevel(input)
        stats.level(byteArrayOf(0, 0))
        stats.flush(ended = true)
        assertTrue(reports.last().contains("inputPeakDbfs=-6 peakDbfs=silent"))
        assertArrayEquals(copy, input)
        stats.flush(ended = true)
        assertTrue(reports.last().contains("inputPeakDbfs=silent peakDbfs=silent"))
    }
}
