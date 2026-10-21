package com.shilapi.xcertplay

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.view.View
import android.widget.FrameLayout
import org.junit.Assert.assertEquals
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [29], manifest = Config.NONE)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class C11ClusterMapFrameTest {
    @Test fun diagonalLeavesOriginalBackgroundVisibleAndKeepsSafeAreaContent() {
        val context = RuntimeEnvironment.getApplication()
        val root = C11ClusterMapFrame(context)
        root.addView(View(context).apply { setBackgroundColor(Color.MAGENTA) }, FrameLayout.LayoutParams(-1, -1))
        val exact = View.MeasureSpec.makeMeasureSpec(720, View.MeasureSpec.EXACTLY)
        root.measure(exact, exact)
        root.layout(0, 0, 720, 720)
        val bitmap = Bitmap.createBitmap(720, 720, Bitmap.Config.ARGB_8888)
        try {
            root.draw(Canvas(bitmap))
            assertEquals(Color.TRANSPARENT, bitmap.getPixel(5, 5))
            assertEquals(Color.TRANSPARENT, bitmap.getPixel(5, 360))
            assertEquals(Color.MAGENTA, bitmap.getPixel(60, 60))
            assertEquals(Color.MAGENTA, bitmap.getPixel(660, 60))
            assertEquals(Color.MAGENTA, bitmap.getPixel(10, 710))
            assertEquals(Color.MAGENTA, bitmap.getPixel(660, 660))
        } finally { bitmap.recycle() }
    }
}
