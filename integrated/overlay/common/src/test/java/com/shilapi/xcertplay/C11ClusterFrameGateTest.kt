package com.shilapi.xcertplay

import org.junit.Assert.*
import org.junit.Test

class C11ClusterFrameGateTest {
    @Test fun waitingAndNegotiationNeverShowTheInstrumentWindow() {
        val gate = C11ClusterFrameGate()
        assertFalse(gate.visible)
        gate.frameReceived(); assertFalse(gate.visible)
        gate.setActive(true); assertFalse(gate.visible)
        gate.frameReceived(); assertTrue(gate.visible)
    }
    @Test fun disconnectHidesImmediatelyAndNextConnectionNeedsANewFrame() {
        val gate = C11ClusterFrameGate()
        gate.setActive(true); gate.frameReceived(); assertTrue(gate.visible)
        gate.setActive(false); assertFalse(gate.visible)
        gate.frameReceived(); gate.setActive(true); assertFalse(gate.visible)
        gate.frameReceived(); assertTrue(gate.visible)
    }
    @Test fun hiddenMapAndRecreatedSurfaceCannotExposeAnOldFrame() {
        val gate = C11ClusterFrameGate()
        gate.setActive(true); gate.frameReceived(); gate.shown = false; assertFalse(gate.visible)
        gate.shown = true; assertTrue(gate.visible)
        gate.resetFrames(); assertFalse(gate.visible)
    }
}
