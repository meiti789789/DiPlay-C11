package com.shilapi.xcertplay

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.widget.FrameLayout

/** A transparent inset edge, confined to the already-confirmed instrument window. */
internal class C11ClusterMapFrame(context: Context) : FrameLayout(context) {
    private val boundary = Path()
    private val seam = Path()
    private val seamPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.argb(45, 210, 225, 240)
        style = Paint.Style.STROKE
        strokeWidth = 1f
    }

    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        super.onSizeChanged(w, h, oldw, oldh)
        // Confine the inset to 6%, inside the stream’s advertised 8% safe margin.
        val inset = w * 0.06f
        boundary.reset()
        boundary.moveTo(inset, 0f)
        boundary.lineTo(w.toFloat(), 0f)
        boundary.lineTo(w.toFloat(), h.toFloat())
        boundary.lineTo(0f, h.toFloat())
        boundary.close()
        seam.reset()
        seam.moveTo(inset, 0f)
        seam.lineTo(0f, h.toFloat())
    }

    override fun dispatchDraw(canvas: Canvas) {
        val checkpoint = canvas.save()
        canvas.clipPath(boundary)
        super.dispatchDraw(canvas)
        canvas.restoreToCount(checkpoint)
        canvas.drawPath(seam, seamPaint)
    }
}
