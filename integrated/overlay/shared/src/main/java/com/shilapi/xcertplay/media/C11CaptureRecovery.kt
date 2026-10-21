package com.shilapi.xcertplay.media

/** Digital zero samples indicate a stuck/blocked capture path; quiet nonzero PCM is left alone. */
internal class C11CaptureRecovery(private val silenceMillis: Long = 2_000) {
    var attempts = 0
        private set
    private var zeroSince: Long? = null
    fun inspect(bytes: ByteArray, count: Int, nowMillis: Long): Boolean {
        if (count <= 0) return false
        if ((0 until count).any { bytes[it] != 0.toByte() }) { zeroSince = null; return false }
        val since = zeroSince ?: nowMillis.also { zeroSince = it }
        if (attempts >= 2 || nowMillis - since < silenceMillis) return false
        attempts++
        zeroSince = nowMillis
        return true
    }
}
