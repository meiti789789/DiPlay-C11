package com.shilapi.xcertplay

import org.junit.After
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class) @Config(sdk=[28,33])
class C11MusicGuardTest {
    private val context get() = RuntimeEnvironment.getApplication()
    @After fun cleanup() { C11MusicGuard.stopCurrent();C11MusicGuard.setEnabled(context,false) }
    @Test fun defaultsOffAndMissingAccessNeverStartsMonitoring() {
        assertFalse(C11MusicGuard.enabled(context));assertTrue(C11MusicGuard.restoreEnabled(context))
        val owner=Any();C11MusicGuard.start(context,owner);C11MusicGuard.setEnabled(context,true)
        assertTrue(C11MusicGuard.diagnostic(context).contains("monitoring=false"))
        assertTrue(C11MusicGuard.diagnostic(context).contains("session=true"))
        C11MusicGuard.stop(owner)
        assertTrue(C11MusicGuard.diagnostic(context).contains("session=false"))
    }
    @Test fun staleCommunicationModeAllowsRestorationButAnActualCallDoesNot() {
        assertTrue(C11MusicGuard.restorationAllowed(android.media.AudioManager.MODE_NORMAL,false))
        assertTrue(C11MusicGuard.restorationAllowed(android.media.AudioManager.MODE_IN_COMMUNICATION,false))
        assertFalse(C11MusicGuard.restorationAllowed(android.media.AudioManager.MODE_IN_COMMUNICATION,true))
        assertFalse(C11MusicGuard.restorationAllowed(android.media.AudioManager.MODE_IN_CALL,false))
        assertFalse(C11MusicGuard.restorationAllowed(android.media.AudioManager.MODE_RINGTONE,false))
        assertFalse(C11MusicGuard.restorationAllowed(null,false))
    }
    @Test fun staleSessionEndCannotStopReplacementAndRestorePreferencePersists() {
        val old=Any();val current=Any();C11MusicGuard.start(context,old);C11MusicGuard.start(context,current)
        C11MusicGuard.stop(old);assertTrue(C11MusicGuard.diagnostic(context).contains("session=true"))
        C11MusicGuard.setRestore(context,false);assertFalse(C11MusicGuard.restoreEnabled(context))
        C11MusicGuard.stop(current);assertTrue(C11MusicGuard.diagnostic(context).contains("session=false"))
    }
}
