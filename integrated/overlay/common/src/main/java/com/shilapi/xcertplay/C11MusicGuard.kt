package com.shilapi.xcertplay

import android.content.ComponentName
import android.content.Context
import android.media.AudioManager
import android.media.session.MediaController
import android.media.session.MediaSessionManager
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.service.notification.NotificationListenerService
import androidx.core.app.NotificationManagerCompat

/** Notification content is never read. Authorization is used only for Android media sessions. */
class C11MusicAccessService : NotificationListenerService() {
    override fun onListenerConnected() { super.onListenerConnected(); C11MusicGuard.accessChanged(this, true) }
    override fun onListenerDisconnected() { C11MusicGuard.accessChanged(this, false); super.onListenerDisconnected() }
    override fun onDestroy() { C11MusicGuard.accessChanged(this, false); super.onDestroy() }
}

internal object C11MusicGuard {
    private val handler = Handler(Looper.getMainLooper())
    private var context: Context? = null
    private var owner: Any? = null
    private var connectedService: C11MusicAccessService? = null
    private var policy = C11MusicPolicy()
    private var running = false
    private var lastSnapshot = "none"
    private var missingLogged = false
    private fun prefs(c: Context) = c.getSharedPreferences("c11-music", Context.MODE_PRIVATE)
    fun enabled(c: Context) = prefs(c).getBoolean("enabled", false)
    fun restoreEnabled(c: Context) = prefs(c).getBoolean("restore", true)
    fun accessGranted(c: Context) = NotificationManagerCompat.getEnabledListenerPackages(c).contains(c.packageName)
    fun setEnabled(c: Context, value: Boolean) {
        prefs(c).edit().putBoolean("enabled", value).apply()
        if (!value) stopMonitoring(restoreEnabled(c)) else refresh()
    }
    fun setRestore(c: Context, value: Boolean) { prefs(c).edit().putBoolean("restore", value).apply() }
    fun accessChanged(service: C11MusicAccessService, ready: Boolean) {
        if (ready) { connectedService = service; refresh() }
        else if (connectedService === service) {
            connectedService = null; stopMonitoring(false)
            WheelKeyLog.note("C11 music access disconnected; no restoration attempted")
        }
    }
    fun start(c: Context, session: Any) {
        if (owner === session) return
        // Controller replacement must not briefly restart the car player between two sessions.
        stopMonitoring(false)
        context = c.applicationContext; owner = session; missingLogged = false
        refresh()
    }
    fun stopCurrent() { stop(owner) }
    fun stop(session: Any?) {
        if (session == null || owner !== session) return
        val app = context
        stopMonitoring(app != null && restoreEnabled(app))
        owner = null; context = null
    }
    private val tick = object : Runnable {
        override fun run() { if (!running) return; scan(); if (running) handler.postDelayed(this, 750) }
    }
    fun refresh() {
        val c = context ?: return
        if (owner == null || !enabled(c)) return
        if (!accessGranted(c) || connectedService == null) {
            if (!missingLogged) WheelKeyLog.note("C11 music waiting for notification access/listener connection")
            missingLogged = true; return
        }
        if (!running) { running = true; missingLogged = false; handler.post(tick) }
    }
    fun wheelEvent() {
        refresh()
        if (running) { handler.removeCallbacks(tick); handler.post(tick) }
    }
    private fun players(c: Context): List<C11MusicPolicy.Player> {
        val manager = c.getSystemService(MediaSessionManager::class.java)
        return manager.getActiveSessions(ComponentName(c, C11MusicAccessService::class.java)).map { controller ->
            object : C11MusicPolicy.Player {
                override val id: Any get() = controller.sessionToken
                override val packageName get() = controller.packageName
                override val state get() = controller.playbackState?.state ?: 0
                override fun pause() {
                    controller.transportControls.pause()
                    WheelKeyLog.note("C11 music pause requested package=$packageName")
                }
                override fun play() {
                    controller.transportControls.play()
                    WheelKeyLog.note("C11 music restore requested package=$packageName")
                }
            }
        }
    }
    private fun scan() {
        val c = context ?: return
        if (!enabled(c) || !accessGranted(c) || connectedService == null) { stopMonitoring(false); return }
        try {
            val players = players(c)
            val snapshot = players.joinToString { "${it.packageName}:${it.state}:supported=${C11MusicPolicy.supported(it.packageName)}" }
            if (snapshot != lastSnapshot) { lastSnapshot = snapshot; WheelKeyLog.note("C11 music sessions=${snapshot.ifEmpty { "none" }}") }
            // C11 firmware may retain MODE_IN_COMMUNICATION after a call. Only allowlisted
            // music sessions receive PAUSE; call/navigation sessions are never targeted.
            policy.inspect(players, SystemClock.elapsedRealtime())
        } catch (e: RuntimeException) {
            WheelKeyLog.note("C11 music session access failed: ${e.javaClass.simpleName}")
            stopMonitoring(false)
        }
    }
    private fun stopMonitoring(restore: Boolean) {
        running = false; handler.removeCallbacks(tick)
        val c = context
        val mode = c?.getSystemService(AudioManager::class.java)?.mode
        // Existing iAP call state is observed locally; this getter performs no vehicle/ADB writes.
        val callActive = com.shilapi.xcertplay.hud.BydNavigationOutputs.carPlayCall() != null
        val allowed = restore && c != null && connectedService != null && accessGranted(c) &&
            restorationAllowed(mode, callActive)
        if (restore) WheelKeyLog.note("C11 music restore decision allowed=$allowed audioMode=$mode carPlayCall=$callActive")
        val activeIds = if (allowed && c != null) runCatching { players(c).map { it.id }.toSet() }.getOrNull() else null
        policy.finish(allowed && activeIds != null, activeIds); policy = C11MusicPolicy(); lastSnapshot = "none"
    }
    internal fun restorationAllowed(audioMode: Int?, carPlayCall: Boolean): Boolean = !carPlayCall &&
        (audioMode == AudioManager.MODE_NORMAL || audioMode == AudioManager.MODE_IN_COMMUNICATION)
    fun diagnostic(c: Context) = "C11 music enabled=${enabled(c)} restore=${restoreEnabled(c)} access=${accessGranted(c)} " +
        "listenerConnected=${connectedService != null} session=${owner != null} monitoring=$running " +
        "audioMode=${c.getSystemService(AudioManager::class.java)?.mode} sessions=$lastSnapshot"
}
