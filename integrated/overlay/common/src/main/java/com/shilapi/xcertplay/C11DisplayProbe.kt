package com.shilapi.xcertplay

import com.shilapi.xcertplay.host.R
import android.app.Presentation
import android.graphics.Color
import android.graphics.drawable.ColorDrawable
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.Display
import android.view.Gravity
import android.view.WindowManager
import android.widget.TextView
import android.widget.Toast
import androidx.activity.ComponentActivity
import android.app.AlertDialog
import androidx.lifecycle.DefaultLifecycleObserver
import androidx.lifecycle.LifecycleOwner

/** A driver-triggered four-second identification badge, never automatic map probing. */
internal object C11DisplayProbe {
    internal fun configure(window: android.view.Window?) {
        window ?: return
        window.setBackgroundDrawable(ColorDrawable(Color.TRANSPARENT))
        window.clearFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND)
        window.addFlags(WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE)
        window.setGravity(Gravity.TOP or Gravity.RIGHT)
        window.setLayout(140, 40)
    }
    fun show(activity: ComponentActivity, display: Display, confirmed: () -> Unit) {
        if (CarPlayBackgroundSession.active) {
            Toast.makeText(activity, R.string.settings_c11_probe_disconnect, Toast.LENGTH_LONG).show(); return
        }
        val topology = C11ClusterRoute.topology(activity)
        if (C11ClusterRoute.candidates(activity).none { it.displayId == display.displayId && it.name == display.name }) return
        C11ClusterRoute.select(activity, null)
        val presentation = object : Presentation(activity, display) {
            override fun onCreate(savedInstanceState: Bundle?) {
                super.onCreate(savedInstanceState)
                setContentView(TextView(context).apply {
                    text = "C11 #${display.displayId}"; textSize = 14f
                    gravity = Gravity.CENTER; setTextColor(Color.WHITE); setBackgroundColor(0xDD123D37.toInt())
                })
                configure(window)
            }
            override fun onStart() { super.onStart(); configure(window) }
        }
        if (runCatching { presentation.show() }.isFailure) {
            runCatching { presentation.dismiss() }
            Toast.makeText(activity, R.string.settings_c11_probe_failed, Toast.LENGTH_LONG).show(); return
        }
        WheelKeyLog.note("C11 display marker show returned id=${display.displayId} size=140x40 gravity=top-right; physicalVisibility=unconfirmed")
        val handler = Handler(Looper.getMainLooper())
        val hide = Runnable { runCatching { presentation.dismiss() } }
        handler.postDelayed(hide, 4000)
        val dialog = AlertDialog.Builder(activity)
            .setTitle(activity.getString(R.string.settings_c11_probe_title, display.displayId))
            .setMessage(R.string.settings_c11_probe_description)
            .setPositiveButton(R.string.settings_c11_probe_confirm) { _, _ ->
                if (!CarPlayBackgroundSession.active && C11ClusterRoute.topology(activity) == topology) {
                    C11ClusterRoute.select(activity, display.name, display.displayId)
                    WheelKeyLog.note("C11 instrument visually confirmed id=${display.displayId}")
                    confirmed()
                }
            }
            .setNegativeButton(android.R.string.cancel, null).create()
        val observer = object : DefaultLifecycleObserver {
            override fun onStop(owner: LifecycleOwner) { dialog.dismiss(); hide.run() }
        }
        activity.lifecycle.addObserver(observer)
        dialog.setOnDismissListener { handler.removeCallbacks(hide); hide.run(); activity.lifecycle.removeObserver(observer) }
        if (runCatching { dialog.show() }.isFailure) {
            handler.removeCallbacks(hide); hide.run(); activity.lifecycle.removeObserver(observer)
        }
    }
}
