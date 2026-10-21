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
            Color.TRANSPARENT, Color.BLACK, Shader.TileMode.CLAMP)
        canvas.drawRect(0f, 0f, width.toFloat(), height.toFloat(), mask)
        canvas.restoreToCount(layer)
    }

    companion object {
        // A bounded transition; the rest of the map is fully opaque. Never changes its transform.
        fun fadeWidth(width: Int): Float = width * C11ClusterRoute.FADE_PERCENT / 100f
    }
}
