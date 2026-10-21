package com.shilapi.xcertplay

import org.junit.Assert.*
import org.junit.Test

class C11MusicPolicyTest {
    private class Fake(override val id: Any = Any(), override val packageName: String = "com.netease.cloudmusic",
        override var state: Int = 3) : C11MusicPolicy.Player {
        var pauses = 0; var plays = 0; var failPause = false
        override fun pause() { if (failPause) throw IllegalStateException(); pauses++; state = 2 }
        override fun play() { plays++; state = 3 }
    }
    @Test fun initialPlayingSessionIsPausedAndRestoredWithoutChangingOtherPlayers() {
        val policy = C11MusicPolicy(); val music = Fake(); val nav = Fake(packageName = "com.autonavi.amapauto")
        val own = Fake(packageName = "com.c11.diplay"); val call = Fake(packageName = "com.android.dialer")
        policy.inspect(listOf(music,nav,own,call),0)
        assertEquals(1,music.pauses); assertEquals(0,nav.pauses); assertEquals(0,own.pauses); assertEquals(0,call.pauses)
        policy.finish(true,setOf(music.id)); assertEquals(1,music.plays)
        policy.finish(true); assertEquals(1,music.plays)
    }
    @Test fun initiallyPausedAndNewlyStartedSessionsNeverAutoPlayOnDisconnect() {
        val policy=C11MusicPolicy();val old=Fake(state=2);policy.inspect(listOf(old),0)
        old.state=3;val new=Fake();policy.inspect(listOf(old,new),1000)
        assertEquals(1,old.pauses);assertEquals(1,new.pauses)
        policy.finish(true);assertEquals(0,old.plays);assertEquals(0,new.plays)
    }
    @Test fun eachWheelRestartIsPausedAgainWithBoundedRetries() {
        val policy=C11MusicPolicy();val music=Fake();policy.inspect(listOf(music),0)
        music.state=3;policy.inspect(listOf(music),100);assertEquals(1,music.pauses)
        policy.inspect(listOf(music),750);assertEquals(2,music.pauses)
        music.state=3;policy.inspect(listOf(music),1500);assertEquals(3,music.pauses)
    }
    @Test fun failedPauseIsNotRestoredAndCanBeRetried() {
        val policy=C11MusicPolicy();val music=Fake().apply { failPause=true }
        policy.inspect(listOf(music),0);music.state=2;policy.finish(true);assertEquals(0,music.plays)
    }
    @Test fun restoreDisabledDestroyedOrAlreadyPlayingSessionsAreNotRestarted() {
        val policy=C11MusicPolicy();val music=Fake();policy.inspect(listOf(music),0)
        policy.finish(true, emptySet());assertEquals(0,music.plays)
        music.state=3;policy.inspect(listOf(music),1000);policy.finish(false);assertEquals(0,music.plays)
        music.state=3;policy.inspect(listOf(music),2000);music.state=3;policy.finish(true);assertEquals(0,music.plays)
    }
    @Test fun aCallDoesNotReceivePauseCommands() {
        val policy=C11MusicPolicy();val music=Fake();policy.inspect(listOf(music),0,pause=false)
        assertEquals(0,music.pauses);policy.inspect(listOf(music),1000,pause=true);assertEquals(1,music.pauses)
    }
    @Test fun unsupportedAndLookalikePackagesRemainUntouched() {
        assertTrue(C11MusicPolicy.supported("com.netease.cloudmusic.car"))
        assertFalse(C11MusicPolicy.supported("com.netease.cloudmusic.evil".replace("cloudmusic.","cloudmusicx.")))
        assertFalse(C11MusicPolicy.supported("com.leapmotor.navigation"))
    }
    @Test fun bufferingIsPausedBeforePlaybackAndDoesNotAutoStartOnDisconnect() {
        val policy = C11MusicPolicy(); val music = Fake(state = 6)
        policy.inspect(listOf(music), 0)
        assertEquals(1, music.pauses)
        policy.finish(true); assertEquals(0, music.plays)
    }
    @Test fun confirmedPausedThenRestartedDoesNotWaitForRetryCooldown() {
        val policy = C11MusicPolicy(); val music = Fake()
        policy.inspect(listOf(music), 0)
        policy.inspect(listOf(music), 10)
        music.state = 3; policy.inspect(listOf(music), 60)
        assertEquals(2, music.pauses)
    }

}
