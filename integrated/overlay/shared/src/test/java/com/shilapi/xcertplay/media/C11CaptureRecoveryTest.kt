package com.shilapi.xcertplay.media

import org.junit.Assert.*
import org.junit.Test

class C11CaptureRecoveryTest {
    @Test fun digitalZerosRequireASustainedIntervalAndRetriesAreBounded() {
        val policy = C11CaptureRecovery(2_000)
        val zero = ByteArray(320)
        assertFalse(policy.inspect(zero, zero.size, 0))
        assertFalse(policy.inspect(zero, zero.size, 1_999))
        assertTrue(policy.inspect(zero, zero.size, 2_000))
        assertFalse(policy.inspect(zero, zero.size, 2_001))
        assertTrue(policy.inspect(zero, zero.size, 4_000))
        assertFalse(policy.inspect(zero, zero.size, 100_000))
        assertEquals(2, policy.attempts)
    }
    @Test fun quietNonzeroInputResetsSilenceAndStaleBufferBytesAreIgnored() {
        val policy = C11CaptureRecovery(100)
        val buffer = ByteArray(16)
        assertFalse(policy.inspect(buffer, 8, 0))
        buffer[1] = 1
        assertFalse(policy.inspect(buffer, 8, 200))
        buffer[1] = 0
        buffer[15] = 1 // Beyond the bytes actually returned by AudioRecord.read.
        assertFalse(policy.inspect(buffer, 8, 201))
        assertTrue(policy.inspect(buffer, 8, 301))
        assertEquals(1, policy.attempts)
    }
}
