package com.shilapi.xcertplay

import android.content.Context
import android.graphics.Point
import android.hardware.display.DisplayManager
import android.os.Build
import android.view.Display
import android.view.Gravity
import android.view.Window
import android.view.WindowManager
import com.shilapi.xcertplay.airplay.CarPlayClusterDisplay

/** Explicitly chosen public projection display only; never routes tasks or writes vehicle state. */
internal object C11ClusterRoute {
    const val FADE_PERCENT = 12
    // The owner wants the centre of the physical 720x720 map pane, not the
    // centre of the portion remaining after its left-edge fade (previously 56%).
    const val DEFAULT_MARKER_X = 50
    const val DEFAULT_MARKER_Y = 50
    data class Viewport(val left: Int = 1200, val top: Int = 0, val width: Int = 720, val height: Int = 720)
    fun platformSupported(fingerprint: String = Build.FINGERPRINT, model: String = Build.MODEL): Boolean =
        "$fingerprint $model".contains("msmnile_gvmq", ignoreCase = true)
    fun plan(width: Int, height: Int, supported: Boolean = platformSupported()): Viewport? =
        if (supported && width == 1920 && height == 720) Viewport() else null
    private fun prefs(context: Context) = context.getSharedPreferences("c11-cluster", Context.MODE_PRIVATE)
    fun normalizeLegacyCenter(context: Context) {
        if (!platformSupported()) return
        val state = prefs(context)
        if (state.getInt("centering_revision", 0) >= 101) return
        val x = AirPlayPersistence.loadClusterMarkerXPercent(context)
        val y = AirPlayPersistence.loadClusterMarkerYPercent(context)
        val legacyDefault = (x == 56 && y == 50) || (x == 50 && y == 45)
        // Retain an audit/rollback snapshot; never clear the driver's preferences.
        state.edit().putInt("centering_original_x", x).putInt("centering_original_y", y)
            .putBoolean("centering_default_repaired", legacyDefault).putInt("centering_revision", 101).apply()
        if (legacyDefault) {
            AirPlayPersistence.saveClusterMarkerXPercent(context, DEFAULT_MARKER_X)
            AirPlayPersistence.saveClusterMarkerYPercent(context, DEFAULT_MARKER_Y)
        }
        WheelKeyLog.note("C11 cluster centre migration previous=$x,$y defaultRepaired=$legacyDefault")
    }
    internal fun topology(context: Context) = candidates(context).sortedBy { it.displayId }
        .joinToString { "${it.displayId}:${it.name}:${size(it).x}x${size(it).y}:${it.flags}" }
    fun selection(context: Context): String? = prefs(context).getString("display_name", null)
    fun select(context: Context, name: String?, displayId: Int? = null) {
        val target = if (name == null) null else candidates(context).filter { it.name == name }
            .let { matches -> if (displayId != null) matches.singleOrNull { it.displayId == displayId } else matches.singleOrNull() }
        prefs(context).edit().putString("display_name", target?.name).putInt("display_id", target?.displayId ?: -1)
            .putInt("selection_version", 2).putString("firmware", Build.FINGERPRINT)
            .putString("topology", topology(context)).apply()
        WheelKeyLog.note("C11 cluster selection saved across reboot; reconnect required")
    }
    fun size(display: Display) = Point().also {
        @Suppress("DEPRECATION")
        display.getRealSize(it)
    }
    fun candidates(context: Context): List<Display> {
        if (!platformSupported()) return emptyList()
        return context.getSystemService(DisplayManager::class.java)
            ?.getDisplays(DisplayManager.DISPLAY_CATEGORY_PRESENTATION).orEmpty().filter {
                val size = size(it)
                it.displayId != Display.DEFAULT_DISPLAY && it.isValid &&
                    (it.flags and Display.FLAG_PRIVATE) == 0 &&
                    (it.flags and Display.FLAG_PRESENTATION) != 0 && plan(size.x, size.y) != null
            }
    }
    fun findDisplay(context: Context): Display? {
        val name = selection(context) ?: return null
        // Remember the owner's visually confirmed numbered output across normal reboots.
        // Never infer another output from a duplicate name, or migrate an old temporary choice.
        if (prefs(context).getInt("selection_version", 0) != 2 ||
            prefs(context).getString("firmware", null) != Build.FINGERPRINT ||
            prefs(context).getString("topology", null) != topology(context)) return null
        val expectedId = prefs(context).getInt("display_id", -1)
        return candidates(context).singleOrNull { it.name == name && it.displayId == expectedId }
    }
    fun streamConfig(content: CarPlayClusterDisplay.Content, scalePercent: Int = 100,
        markerXPercent: Int? = null, markerYPercent: Int? = null) = CarPlayClusterDisplay.config(
        widthPixels = 720, heightPixels = 720, scalePercent = scalePercent, content = content,
        markerXPercent = markerXPercent, markerYPercent = markerYPercent,
        baseSafeArea = com.shilapi.xcertplay.airplay.AirPlayInsets(top = 8, bottom = 8, left = FADE_PERCENT, right = FADE_PERCENT)).let { config ->
            // A centred request reserves matching horizontal margins. Map pixels may still
            // fill the whole frame; there is no video transform, crop or window translation.
            val width = config.widthPixels
            val fade = kotlin.math.ceil(width * FADE_PERCENT / 100.0).toInt()
            val x = width * (markerXPercent ?: DEFAULT_MARKER_X).coerceIn(FADE_PERCENT + 5, 95) / 100
            val half = minOf(x - fade, width - x)
            config.copy(safeArea = config.safeArea!!.copy(left = x - half, right = width - x - half))
        }
    fun configureWindow(window: Window?, display: Display) {
        val size = size(display)
        val viewport = plan(size.x, size.y) ?: return
        window ?: return
        window.setFormat(android.graphics.PixelFormat.TRANSLUCENT)
        window.setBackgroundDrawable(android.graphics.drawable.ColorDrawable(android.graphics.Color.TRANSPARENT))
        window.clearFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND)
        window.addFlags(WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE)
        window.setGravity(Gravity.TOP or Gravity.RIGHT)
        window.setLayout(viewport.width, viewport.height)
        window.attributes = window.attributes.apply { x = 0; y = 0 }
    }
    fun diagnostic(context: Context) = "C11 cluster platform=${platformSupported()} selected=${selection(context) ?: "none"} " +
        "selectedId=${prefs(context).getInt("display_id", -1)} candidates=${candidates(context).joinToString { "${it.displayId}:${it.name}" }}; savedAcrossBoot=${prefs(context).getInt("selection_version", 0) == 2} automaticSelection=false" +
        " viewport=right720x720 scale=${AirPlayPersistence.loadClusterMapScalePercent(context)} " +
        "marker=${AirPlayPersistence.loadClusterMarkerXPercent(context)},${AirPlayPersistence.loadClusterMarkerYPercent(context)} " +
        "content=${AirPlayPersistence.loadClusterContent(context)} fade=alpha-left${FADE_PERCENT}% " +
        "source=111 independentFromMain110=true centreRevision=${prefs(context).getInt("centering_revision", 0)} " +
        "previousCentre=${prefs(context).getInt("centering_original_x", -1)},${prefs(context).getInt("centering_original_y", -1)}"
}
