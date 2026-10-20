package com.shilapi.xcertplay

import android.content.Intent
import android.os.Looper
import com.shilapi.xcertplay.airplay.CarPlayMediaButton
import com.shilapi.xcertplay.orchestration.CarPlayController
import org.junit.After
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.mockito.Mockito.mock
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28, 33])
class C11WheelKeysTest {
    private val context get() = RuntimeEnvironment.getApplication()
    private fun key(value: Int) = Intent("com.leapmotor.action.METER.CTRL")
        .putExtra("keyEventType", "steeringWheel").putExtra("value", value)
    @After fun stop() { C11WheelKeys.detach(null); C11WheelKeys.setEnabled(context, false) }
    @Test fun decodingAcceptsStringAndIntegerButRejectsOtherVehicleCommands() {
        assertEquals(C11WheelProtocol.Command.PREVIOUS, C11WheelKeys.decode(key(1)))
        assertEquals(C11WheelProtocol.Command.TOGGLE, C11WheelKeys.decode(key(3).putExtra("value", "3")))
        assertNull(C11WheelKeys.decode(key(1).putExtra("keyEventType", "backRow")))
        assertNull(C11WheelKeys.decode(Intent("com.leapmotor.command.music").putExtra("action", "pause")))
        assertNull(C11WheelKeys.decode(Intent("com.leapmotor.command.next").putExtra("action", "{\"src\":\"diplay\",\"data\":{\"action\":\"next\"}}")))
        assertNull(C11WheelKeys.decode(Intent("com.leapmotor.command.next").putExtra("receiver", byteArrayOf(0,50,1))))
    }
    @Test fun disabledByDefaultAndDetachedSessionsCannotForward() {
        assertFalse(C11WheelKeys.enabled(context))
        val delivered = mutableListOf<Int>()
        val session = mock(CarPlayController::class.java)
        C11WheelKeys.attach(context, session) { delivered += it }
        context.sendBroadcast(key(2)); shadowOf(Looper.getMainLooper()).idle()
        assertTrue(delivered.isEmpty())
        C11WheelKeys.setEnabled(context, true)
        context.sendBroadcast(key(2)); shadowOf(Looper.getMainLooper()).idle()
        assertEquals(listOf(CarPlayMediaButton.NEXT), delivered)
        C11WheelKeys.detach(session)
        context.sendBroadcast(key(1)); shadowOf(Looper.getMainLooper()).idle()
        assertEquals(1, delivered.size)
    }
    @Test fun reconnectDoesNotDoubleRegisterAndOldDetachCannotStopNewSession() {
        val delivered = mutableListOf<Int>()
        val old = mock(CarPlayController::class.java); val next = mock(CarPlayController::class.java)
        C11WheelKeys.attach(context, old) { fail("Old receiver must not dispatch") }
        C11WheelKeys.attach(context, next) { delivered += it }
        C11WheelKeys.attach(context, next) { fail("Repeated attach must be ignored") }
        C11WheelKeys.detach(old)
        C11WheelKeys.setEnabled(context, true)
        context.sendBroadcast(key(2)); shadowOf(Looper.getMainLooper()).idle()
        assertEquals(listOf(CarPlayMediaButton.NEXT), delivered)
    }
    @Test fun deduplicatesBroadcastAndNativeMediaKeysAndResetsAcrossSessions() {
        val session = mock(CarPlayController::class.java)
        C11WheelKeys.attach(context, session) {}
        C11WheelKeys.setEnabled(context, true)
        assertTrue(C11WheelKeys.claim(CarPlayMediaButton.PAUSE, 1000))
        assertFalse(C11WheelKeys.claim(CarPlayMediaButton.PLAY_PAUSE, 1100))
        assertTrue(C11WheelKeys.claim(CarPlayMediaButton.PLAY_PAUSE, 1250))
        assertTrue(C11WheelKeys.claim(CarPlayMediaButton.NEXT, 1251))
        C11WheelKeys.setEnabled(context, false)
        assertTrue(C11WheelKeys.claim(CarPlayMediaButton.NEXT, 1252))
        C11WheelKeys.detach(session)
        C11WheelKeys.attach(context, mock(CarPlayController::class.java)) {}
        C11WheelKeys.setEnabled(context, true)
        assertTrue(C11WheelKeys.claim(CarPlayMediaButton.NEXT, 1253))
    }
}
