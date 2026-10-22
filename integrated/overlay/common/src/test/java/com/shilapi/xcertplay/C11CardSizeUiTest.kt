package com.shilapi.xcertplay

import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.hardware.display.DisplayManager
import android.view.Display
import android.view.View
import android.view.ViewGroup
import android.widget.SeekBar
import android.widget.TextView
import com.shilapi.xcertplay.airplay.CarPlayClusterDisplay
import com.shilapi.xcertplay.airplay.ClusterTurnCardOverlay
import com.shilapi.xcertplay.hud.ClusterTurnGuidance
import com.shilapi.xcertplay.host.R
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
class C11CardSizeUiTest {
    private val context get() = RuntimeEnvironment.getApplication()
    private fun descendants(v: View): Sequence<View> = sequence {
        yield(v)
        if (v is ViewGroup) for (i in 0 until v.childCount) yieldAll(descendants(v.getChildAt(i)))
    }
    private fun saveImage(name: String, bitmap: Bitmap) {
        val file = File("build/reports/c11-ui/$name.png"); file.parentFile.mkdirs()
        file.outputStream().use { assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG, 100, it)) }
    }
    @Test fun c11PersistenceKeepsExtendedSizesAndExistingMarkerCoordinates() {
        ShadowBuild.setModel("msmnile_gvmq for arm64")
        AirPlayPersistence.saveClusterMarkerXPercent(context, 37)
        AirPlayPersistence.saveClusterMarkerYPercent(context, 61)
        AirPlayPersistence.saveClusterTurnCardOverlaySizePercent(context, 95)
        assertEquals(95, AirPlayPersistence.loadClusterTurnCardOverlaySizePercent(context))
        AirPlayPersistence.saveClusterTurnCardOverlaySizePercent(context, 190)
        assertEquals(190, AirPlayPersistence.loadClusterTurnCardOverlaySizePercent(context))
        AirPlayPersistence.saveClusterSmallWindowCardSizePercent(context, 190)
        assertEquals(190, AirPlayPersistence.loadClusterSmallWindowCardSizePercent(context))
        assertEquals(37, AirPlayPersistence.loadClusterMarkerXPercent(context))
        assertEquals(61, AirPlayPersistence.loadClusterMarkerYPercent(context))
        ShadowBuild.setModel("other head unit")
        assertEquals(95, AirPlayPersistence.clusterTurnCardSizePercents().last())
        assertEquals(95, AirPlayPersistence.loadClusterTurnCardOverlaySizePercent(context))
    }
    @Test @GraphicsMode(GraphicsMode.Mode.NATIVE)
    fun actualCardRendererDoublesTextAndArrowAreaAtMaximum() {
        val view = ClusterTurnCardView(context)
        view.setGuidance(ClusterTurnGuidance(2, 0, 52, "进入无名道路", remainingSeconds = 600, remainingMeters = 4600))
        view.layout(0, 0, 720, 720)
        var originalText = 0f
        var originalInfo = 0f
        for (size in listOf(95, 190)) {
            view.setLayout(64, 30, size)
            val bitmap = Bitmap.createBitmap(720, 720, Bitmap.Config.ARGB_8888)
            try {
                val canvas = Canvas(bitmap); canvas.drawColor(Color.rgb(30, 45, 60)); view.draw(canvas)
                val text = ReflectionHelpers.getField<Paint>(view, "distancePaint").textSize
                val info = ReflectionHelpers.getField<Paint>(view, "infoPaint").textSize
                if (size == 95) { originalText = text; originalInfo = info }
                else { assertEquals(originalText * 2, text, 0.01f); assertEquals(originalInfo * 2, info, 0.01f) }
                saveImage("custom-card-actual-$size", bitmap)
            } finally { bitmap.recycle() }
        }
    }
    @Test @GraphicsMode(GraphicsMode.Mode.NATIVE)
    @Config(qualifiers = "zh-rCN-w320dp-h600dp-mdpi")
    fun compactSizeControl() = preview("card-size-compact-zh", 320)
    @Test @GraphicsMode(GraphicsMode.Mode.NATIVE)
    @Config(qualifiers = "zh-rCN-w1000dp-h720dp-mdpi")
    fun wideSizeControl() = preview("card-size-wide-zh", 1000)
    @Test @GraphicsMode(GraphicsMode.Mode.NATIVE)
    @Config(qualifiers = "ar-ldrtl-w320dp-h600dp-mdpi")
    fun rtlSizeControl() = preview("card-size-compact-ar", 320)
    private fun preview(name: String, width: Int) {
        ShadowBuild.setModel("msmnile_gvmq for arm64")
        RuntimeEnvironment.setFontScale(1.3f)
        val id = ShadowDisplayManager.addDisplay("w1920dp-h720dp-mdpi", 5)
        val display = context.getSystemService(DisplayManager::class.java).getDisplay(id)
        shadowOf(display).setName("C11 instrument simulated"); shadowOf(display).setFlags(Display.FLAG_PRESENTATION)
        C11ClusterRoute.select(context, display.name, id)
        AirPlayPersistence.saveClusterMapEnabled(context, true)
        AirPlayPersistence.saveClusterContent(context, CarPlayClusterDisplay.Content.MAP_WITH_CUSTOM_CARD)
        AirPlayPersistence.saveClusterTurnCardOverlaySizePercent(context, 95)
        val controller = Robolectric.buildActivity(DiPlayActivity::class.java,
            Intent(context, DiPlayActivity::class.java).putExtra("page", "settings")).setup()
        try {
            val screen = controller.get()
            ReflectionHelpers.setField(screen, "settingsCategory", SettingsCategory.ADVANCED)
            ReflectionHelpers.setField(screen, "settingsSectionFilter", setOf(SettingsSection.CLUSTER_MAP))
            ReflectionHelpers.callInstanceMethod<Unit>(screen, "render")
            val title = descendants(screen.window.decorView).filterIsInstance<TextView>()
                .single { it.text == screen.getString(R.string.turn_card_overlay_size) }
            val row = title.parent.parent as ViewGroup
            val slider = descendants(row).filterIsInstance<SeekBar>().single()
            val listener = SeekBar::class.java.getDeclaredField("mOnSeekBarChangeListener")
                .apply { isAccessible = true }.get(slider) as SeekBar.OnSeekBarChangeListener
            slider.progress = slider.max
            listener.onProgressChanged(slider, slider.max, true)
            assertEquals(190, AirPlayPersistence.loadClusterTurnCardOverlaySizePercent(context))
            row.measure(View.MeasureSpec.makeMeasureSpec(width, View.MeasureSpec.EXACTLY),
                View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED))
            row.layout(0, 0, width, row.measuredHeight)
            val bitmap = Bitmap.createBitmap(width, row.height, Bitmap.Config.ARGB_8888)
            try {
                val canvas = Canvas(bitmap); canvas.drawColor(Color.rgb(30, 45, 60)); row.draw(canvas)
                saveImage(name, bitmap)
            } finally { bitmap.recycle() }
        } finally {
            controller.pause().stop().destroy(); C11ClusterRoute.select(context, null)
            ShadowDisplayManager.removeDisplay(id)
        }
    }
}
