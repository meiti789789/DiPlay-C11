package com.shilapi.xcertplay

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.PorterDuff
import android.graphics.PorterDuffXfermode
import android.graphics.Shader
import android.widget.FrameLayout

/** Fades only our video into the actual OEM pixels, so both OEM day/night backgrounds survive. */
internal class C11ClusterBlendLayout(context: Context) : FrameLayout(context) {
    private val mask = Paint().apply { xfermode = PorterDuffXfermode(PorterDuff.Mode.DST_IN) }

    override fun dispatchDraw(canvas: Canvas) {
        if (width == 0 || height == 0) return
        val layer = canvas.saveLayer(0f, 0f, width.toFloat(), height.toFloat(), null)
        super.dispatchDraw(canvas)
        mask.shader = LinearGradient(0f, 0f, fadeWidth(width), 0f,
            IntArray(17) { i -> Color.argb(kotlin.math.round(alphaAt(i / 16f) * 255).toInt(), 0, 0, 0) },
            FloatArray(17) { it / 16f }, Shader.TileMode.CLAMP)
        canvas.drawRect(0f, 0f, width.toFloat(), height.toFloat(), mask)
        canvas.restoreToCount(layer)
    }

    companion object {
        // The visual feather is independent of the phone's safe area and saved marker coordinates.
        // Smoothstep has no slope jump where the map becomes opaque; every row shares the mask.
        const val BLEND_WIDTH_PERCENT = 24
        fun fadeWidth(width: Int): Float = width * BLEND_WIDTH_PERCENT / 100f
        internal fun alphaAt(position: Float): Float {
            val t = position.coerceIn(0f, 1f)
            return t * t * (3f - 2f * t)
        }
    }
}
