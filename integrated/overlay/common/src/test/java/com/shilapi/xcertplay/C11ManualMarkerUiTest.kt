package com.shilapi.xcertplay

import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Canvas
import android.hardware.display.DisplayManager
import android.view.Display
import android.view.View
import android.view.ViewGroup
import android.widget.SeekBar
import android.widget.TextView
import com.shilapi.xcertplay.host.R
import com.shilapi.xcertplay.airplay.CarPlayClusterDisplay
import java.io.File
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode
import org.robolectric.shadows.ShadowBuild
import org.robolectric.shadows.ShadowDisplayManager
import org.robolectric.util.ReflectionHelpers

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], qualifiers = "zh-rCN-w600dp-h720dp-mdpi")
class C11ManualMarkerUiTest {
    private fun views(view: View): Sequence<View> = sequence {
        yield(view)
        if (view is ViewGroup) for (i in 0 until view.childCount) yieldAll(views(view.getChildAt(i)))
    }
    private fun withEditor(test: (DiPlayActivity, ViewGroup) -> Unit) {
        val context = RuntimeEnvironment.getApplication()
        ShadowBuild.setModel("msmnile_gvmq for arm64")
        val id = ShadowDisplayManager.addDisplay("w1920dp-h720dp-mdpi", 5)
        val display = context.getSystemService(DisplayManager::class.java).getDisplay(id)
        shadowOf(display).setName("C11 instrument simulated")
        shadowOf(display).setFlags(Display.FLAG_PRESENTATION)
        C11ClusterRoute.select(context, display.name, id)
        AirPlayPersistence.saveClusterMapEnabled(context, true)
        // An old small-window preference must not expose controls wired to the wrong keys.
        AirPlayPersistence.saveClusterSmallWindowMode(context, 2)
        val controller = Robolectric.buildActivity(DiPlayActivity::class.java,
            Intent(context, DiPlayActivity::class.java).putExtra("page", "settings")).setup()
        try {
            val screen = controller.get()
            ReflectionHelpers.setField(screen, "settingsCategory", SettingsCategory.ADVANCED)
            ReflectionHelpers.setField(screen, "settingsSectionFilter", setOf(SettingsSection.CLUSTER_MAP))
            ReflectionHelpers.callInstanceMethod<Unit>(screen, "render")
            val editor = views(screen.window.decorView).single { it.tag == "c11-marker-controls" } as ViewGroup
            test(screen, editor)
        } finally {
            CarPlayBackgroundSession.clear()
            PendingReconnect.clear()
            controller.pause().stop().destroy()
            C11ClusterRoute.select(context, null)
            ShadowDisplayManager.removeDisplay(id)
        }
    }
    private fun drag(slider: SeekBar, index: Int) {
        val listener = SeekBar::class.java.getDeclaredField("mOnSeekBarChangeListener")
            .apply { isAccessible = true }.get(slider) as SeekBar.OnSeekBarChangeListener
        slider.progress = index
        listener.onProgressChanged(slider, index, true)
        listener.onStopTrackingTouch(slider)
    }
    @Test fun controlsSaveActualInstrumentCoordinatesAndPreserveThemAcrossReconnectMigration() = withEditor { screen, editor ->
        val session = org.mockito.Mockito.mock(com.shilapi.xcertplay.orchestration.CarPlayController::class.java)
        val sink = org.mockito.Mockito.mock(com.shilapi.xcertplay.media.AndroidMediaSink::class.java)
        var disconnects = 0
        CarPlayBackgroundSession.store(session, sink, 800, 480, Any(),
            CarPlaySessionDisplay(800, 480, android.view.Surface.ROTATION_0, false, false, 800, 480)) { disconnects++ }
        CarPlayBackgroundSession.active = true
        PendingReconnect.clear()
        val sliders = views(editor).filterIsInstance<SeekBar>().toList()
        assertEquals(2, sliders.size)
        val labels = views(screen.window.decorView).filterIsInstance<TextView>().map { it.text.toString() }.toList()
        assertFalse(labels.contains(screen.getString(R.string.cluster_small_window_horizontal)))
        assertFalse(labels.contains(screen.getString(R.string.cluster_small_window_grant_access)))
        assertEquals(C11ClusterRoute.markerXPercents.lastIndex, sliders[0].max)
        drag(sliders[0], C11ClusterRoute.markerXPercents.indexOf(35))
        drag(sliders[1], CarPlayClusterDisplay.markerYPercents.indexOf(60))
        assertTrue(PendingReconnect.isPending(session))
        assertEquals(0, disconnects)
        assertSame(session, CarPlayBackgroundSession.snapshot()?.controller)
        assertEquals(35, AirPlayPersistence.loadClusterMarkerXPercent(screen))
        assertEquals(60, AirPlayPersistence.loadClusterMarkerYPercent(screen))
        fun requested() = C11ClusterRoute.streamConfig(CarPlayClusterDisplay.Content.INSTRUMENTS,
            markerXPercent = AirPlayPersistence.loadClusterMarkerXPercent(screen),
            markerYPercent = AirPlayPersistence.loadClusterMarkerYPercent(screen))
        val config = requested()
        val area = config.safeArea!!
        assertEquals(35.0, (area.left + config.widthPixels - area.right) * 50.0 / config.widthPixels, 0.2)
        assertEquals(60.0, (area.top + config.heightPixels - area.bottom) * 50.0 / config.heightPixels, 0.2)
        C11ClusterRoute.normalizeLegacyCenter(screen)
        assertEquals(config, requested())
        // A manual value equal to an old default must not be migrated away later.
        drag(sliders[0], C11ClusterRoute.markerXPercents.indexOf(50))
        drag(sliders[1], CarPlayClusterDisplay.markerYPercents.indexOf(45))
        C11ClusterRoute.normalizeLegacyCenter(screen)
        assertEquals(45, AirPlayPersistence.loadClusterMarkerYPercent(screen))
        views(editor).filterIsInstance<TextView>().single { it.text == screen.getString(R.string.reset_car_marker_to_centre) }.performClick()
        assertEquals(50, AirPlayPersistence.loadClusterMarkerXPercent(screen))
        assertEquals(50, AirPlayPersistence.loadClusterMarkerYPercent(screen))
    }
    @Test @GraphicsMode(GraphicsMode.Mode.NATIVE)
    @Config(qualifiers = "zh-rCN-w320dp-h600dp-mdpi")
    fun compactLargeFontPreview() = preview("marker-compact-zh", 320)
    @Test @GraphicsMode(GraphicsMode.Mode.NATIVE)
    @Config(qualifiers = "zh-rCN-w1000dp-h720dp-mdpi")
    fun wideLargeFontPreview() = preview("marker-wide-zh", 1000)
    @Test @GraphicsMode(GraphicsMode.Mode.NATIVE)
    @Config(qualifiers = "ar-ldrtl-w320dp-h600dp-mdpi")
    fun rtlLargeFontPreview() = preview("marker-compact-ar", 320)
    private fun preview(name: String, widthDp: Int) {
        RuntimeEnvironment.setFontScale(1.3f)
        withEditor { screen, editor ->
            val width = (widthDp * screen.resources.displayMetrics.density).toInt()
            editor.measure(View.MeasureSpec.makeMeasureSpec(width, View.MeasureSpec.EXACTLY),
                View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED))
            editor.layout(0, 0, width, editor.measuredHeight)
            assertTrue(editor.height > 0)
            val bitmap = Bitmap.createBitmap(width, editor.height, Bitmap.Config.ARGB_8888)
            try {
                editor.draw(Canvas(bitmap))
                val file = File("build/reports/c11-ui/$name.png")
                file.parentFile.mkdirs()
                file.outputStream().use { assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG, 100, it)) }
            } finally { bitmap.recycle() }
        }
    }
}
