package com.shilapi.xcertplay

/** Receiving stream metadata alone must not cover the original C11 instrument. */
internal class C11ClusterFrameGate {
    private var active = false
    private var frame = false
    var shown = true
    val visible get() = active && frame && shown
    fun setActive(value: Boolean) { active = value; if (!value) frame = false }
    fun frameReceived() { if (active) frame = true }
    fun resetFrames() { frame = false }
}
