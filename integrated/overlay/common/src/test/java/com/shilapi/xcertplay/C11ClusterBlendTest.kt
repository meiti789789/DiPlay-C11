package com.shilapi.xcertplay

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.view.View
import android.widget.FrameLayout
import java.io.File
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], qualifiers = "mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class C11ClusterBlendTest {
    @Test fun smoothMaskHasTransparentAndOpaqueEndsWithoutChangingMarkerRequests() {
        assertEquals(0f, C11ClusterBlendLayout.alphaAt(0f), 0f)
        assertEquals(1f, C11ClusterBlendLayout.alphaAt(1f), 0f)
        assertEquals(0.5f, C11ClusterBlendLayout.alphaAt(0.5f), 0.0001f)
        assertTrue(C11ClusterBlendLayout.alphaAt(0.01f) < 0.001f)
        assertTrue(1f - C11ClusterBlendLayout.alphaAt(0.99f) < 0.001f)
        assertEquals(172.8f, C11ClusterBlendLayout.fadeWidth(720), 0.01f)
        val config = C11ClusterRoute.streamConfig(com.shilapi.xcertplay.airplay.CarPlayClusterDisplay.Content.MAP, markerXPercent = 50, markerYPercent = 50)
        assertEquals(config.safeArea!!.left, config.safeArea!!.right)
        assertEquals(87, config.safeArea!!.left)
    }

    @Test fun leftEdgeRevealsTheRealBackgroundInDayAndNightWithoutMovingTheMap() {
        val context = RuntimeEnvironment.getApplication()
        for (background in listOf(Color.rgb(232, 230, 239), Color.rgb(25, 20, 42))) {
            val root = FrameLayout(context).apply { setBackgroundColor(background) }
            val blend = C11ClusterBlendLayout(context)
            blend.addView(View(context).apply { setBackgroundColor(Color.RED) }, FrameLayout.LayoutParams(-1, -1))
            root.addView(blend, FrameLayout.LayoutParams(720, 720))
            val spec = View.MeasureSpec.makeMeasureSpec(720, View.MeasureSpec.EXACTLY)
            root.measure(spec, spec); root.layout(0, 0, 720, 720)
            val bitmap = Bitmap.createBitmap(720, 720, Bitmap.Config.ARGB_8888)
            root.draw(Canvas(bitmap))
            // Verify identical alpha at the top and bottom, not just the middle row.
            for (x in listOf(0, 20, 42, 85, 100, 173, 719)) {
                assertEquals(bitmap.getPixel(x, 2), bitmap.getPixel(x, 360))
                assertEquals(bitmap.getPixel(x, 717), bitmap.getPixel(x, 360))
            }
            val left = bitmap.getPixel(0, 360)
            assertTrue(kotlin.math.abs(Color.red(left) - Color.red(background)) <= 2)
            assertTrue(kotlin.math.abs(Color.blue(left) - Color.blue(background)) <= 2)
            assertNotEquals(background, bitmap.getPixel(42, 360))
            assertNotEquals(Color.RED, bitmap.getPixel(42, 360))
            assertNotEquals(Color.RED, bitmap.getPixel(100, 360))
            assertEquals(Color.RED, bitmap.getPixel(173, 360))
            assertEquals(0, blend.left); assertEquals(720, blend.width)
            File("build/reports/c11-ui").mkdirs()
            File("build/reports/c11-ui/blend-simulated-$background.png").outputStream().use {
                bitmap.compress(Bitmap.CompressFormat.PNG, 100, it)
            }
            bitmap.recycle()
        }
    }
}
