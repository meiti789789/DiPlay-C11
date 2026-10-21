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
    data class Viewport(val left: Int = 1200, val top: Int = 0, val width: Int = 720, val height: Int = 720)
    fun platformSupported(fingerprint: String = Build.FINGERPRINT, model: String = Build.MODEL): Boolean =
        "$fingerprint $model".contains("msmnile_gvmq", ignoreCase = true)
    fun plan(width: Int, height: Int, supported: Boolean = platformSupported()): Viewport? =
        if (supported && width == 1920 && height == 720) Viewport() else null
    private fun prefs(context: Context) = context.getSharedPreferences("c11-cluster", Context.MODE_PRIVATE)
    private val processBoot = java.util.UUID.randomUUID().toString()
    private fun boot(context: Context): String = runCatching {
        android.provider.Settings.Global.getInt(context.contentResolver, android.provider.Settings.Global.BOOT_COUNT)
    }.getOrDefault(-1).let { if (it >= 0) "boot:$it" else "process:$processBoot" }
    internal fun topology(context: Context) = candidates(context).sortedBy { it.displayId }
        .joinToString { "${it.displayId}:${it.name}:${size(it).x}x${size(it).y}:${it.flags}" }
    fun selection(context: Context): String? = prefs(context).getString("display_name", null)
    fun select(context: Context, name: String?, displayId: Int? = null) {
        val target = if (name == null) null else candidates(context).filter { it.name == name }
            .let { matches -> if (displayId != null) matches.singleOrNull { it.displayId == displayId } else matches.singleOrNull() }
        prefs(context).edit().putString("display_name", target?.name).putInt("display_id", target?.displayId ?: -1)
            .putString("boot", boot(context)).putString("topology", topology(context)).apply()
        WheelKeyLog.note("C11 cluster selection changed; reconnect required")
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
        // Manual visual confirmation binds the ID, name, boot and complete public-display topology.
        // Names alone cannot distinguish the C11 passenger panel from its instrument panel.
        if (prefs(context).getString("boot", null) != boot(context) ||
            prefs(context).getString("topology", null) != topology(context)) return null
        val expectedId = prefs(context).getInt("display_id", -1)
        return candidates(context).singleOrNull { it.name == name && it.displayId == expectedId }
    }
    fun streamConfig(content: CarPlayClusterDisplay.Content) = CarPlayClusterDisplay.config(
        widthPixels = 720, heightPixels = 720, scalePercent = 100, content = content,
        baseSafeArea = CarPlayClusterDisplay.VIRTUAL_SAFE_AREA_PERCENT)
    fun configureWindow(window: Window?, display: Display) {
        val size = size(display)
        val viewport = plan(size.x, size.y) ?: return
        window ?: return
        window.setBackgroundDrawable(android.graphics.drawable.ColorDrawable(android.graphics.Color.TRANSPARENT))
        window.clearFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND)
        window.addFlags(WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE)
        window.setGravity(Gravity.TOP or Gravity.RIGHT)
        window.setLayout(viewport.width, viewport.height)
        window.attributes = window.attributes.apply { x = 0; y = 0 }
    }
    fun diagnostic(context: Context) = "C11 cluster platform=${platformSupported()} selected=${selection(context) ?: "none"} " +
        "selectedId=${prefs(context).getInt("display_id", -1)} candidates=${candidates(context).joinToString { "${it.displayId}:${it.name}" }}; automaticSelection=false"
}
