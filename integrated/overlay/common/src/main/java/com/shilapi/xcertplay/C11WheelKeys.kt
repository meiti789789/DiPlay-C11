package com.shilapi.xcertplay

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.SystemClock
import androidx.core.content.ContextCompat
import com.shilapi.xcertplay.airplay.CarPlayMediaButton
import com.shilapi.xcertplay.orchestration.CarPlayController
import org.json.JSONObject

/** C11 media broadcasts only. No CAN writes, gear requests, volume or audio-focus changes. */
internal object C11WheelKeys {
    private var context: Context? = null
    private var controller: CarPlayController? = null
    private var receiver: BroadcastReceiver? = null
    private var lastButton = -1
    private var lastAt = -1L
    private fun prefs(context: Context) = context.getSharedPreferences("c11-wheel", Context.MODE_PRIVATE)
    fun enabled(context: Context) = prefs(context).getBoolean("enabled", false)
    fun setEnabled(context: Context, enabled: Boolean) {
        prefs(context).edit().putBoolean("enabled", enabled).apply()
        lastButton = -1
        lastAt = -1L
        WheelKeyLog.note("C11 forwarding enabled=$enabled")
    }

    fun attach(context: Context, next: CarPlayController,
        forward: (Int) -> Unit = CarPlayMediaKeys::onC11MediaKey) {
        if (controller === next && receiver != null) return
        detach(null)
        val app = context.applicationContext
        this.context = app
        controller = next
        val created = object : BroadcastReceiver() {
            override fun onReceive(context: Context, intent: Intent) {
                // A queued broadcast from an old session cannot control its replacement.
                if (controller !== next || receiver !== this) return
                runCatching {
                    val command = decode(intent)
                    val detail = if (C11WheelProtocol.isC11(intent.action)) {
                        " type=${safe(intent.extras?.get("keyEventType"))} value=${safe(intent.extras?.get("value"))}"
                    } else if (C11WheelProtocol.isExtra(intent.action)) {
                        " switch=${safe(intent.extras?.get("ICU_MediaSwitch"))} key=${safe(intent.extras?.get("ICU_MediaKey"))}"
                    } else ""
                    WheelKeyLog.note("C11 ${intent.action}$detail -> ${command ?: "unmatched"}; enabled=${enabled(app)}")
                    if (!enabled(app)) return
                    val index = when (command) {
                        C11WheelProtocol.Command.NEXT -> CarPlayMediaButton.NEXT
                        C11WheelProtocol.Command.PREVIOUS -> CarPlayMediaButton.PREVIOUS
                        C11WheelProtocol.Command.TOGGLE -> CarPlayMediaButton.PLAY_PAUSE
                        else -> return
                    }
                    C11MusicGuard.wheelEvent()
                    forward(index)
                }.onFailure { WheelKeyLog.note("C11 ignored malformed broadcast: ${it.javaClass.simpleName}") }
            }
        }
        receiver = created
        val result = runCatching {
            // OEM multimedia services run under different UIDs. Accept only the exact media action list.
            ContextCompat.registerReceiver(app, created,
                IntentFilter().apply { C11WheelProtocol.ACTIONS.forEach(::addAction) },
                ContextCompat.RECEIVER_EXPORTED)
        }
        if (result.isFailure) {
            receiver = null
            WheelKeyLog.note("C11 receiver registration failed: ${result.exceptionOrNull()?.javaClass?.simpleName}")
        } else WheelKeyLog.note("C11 listener attached; forwarding=${enabled(app)}")
    }

    fun detach(expected: CarPlayController?) {
        if (expected != null && controller !== expected) return
        C11MusicGuard.stopCurrent()
        val old = receiver
        receiver = null
        if (old != null) context?.let { runCatching { it.unregisterReceiver(old) } }
        controller = null
        context = null
        lastButton = -1
        lastAt = -1L
    }

    /** Shared by native media callbacks and C11 broadcasts, only while the opt-in is enabled. */
    fun claim(index: Int, now: Long = SystemClock.elapsedRealtime()): Boolean {
        val app = context ?: return true
        if (!enabled(app)) return true
        val normalized = when (index) {
            CarPlayMediaButton.PLAY, CarPlayMediaButton.PAUSE, CarPlayMediaButton.PLAY_PAUSE -> CarPlayMediaButton.PLAY_PAUSE
            CarPlayMediaButton.NEXT, CarPlayMediaButton.PREVIOUS -> index
            else -> return true
        }
        if (normalized == lastButton && now - lastAt in 0L..249L) {
            WheelKeyLog.note("C11 duplicate media event suppressed: $index")
            return false
        }
        lastButton = normalized
        lastAt = now
        return true
    }

    private fun safe(value: Any?): String = when (value) {
        null -> "missing"
        is String, is Number -> "${value.toString().replace('\n', ' ').take(32)}(${value.javaClass.simpleName})"
        else -> value.javaClass.simpleName
    }

    internal fun decode(intent: Intent): C11WheelProtocol.Command? {
        val extras = intent.extras
        if (C11WheelProtocol.isC11(intent.action))
            return C11WheelProtocol.c11(extras?.get("keyEventType"), extras?.get("value"))
        if (C11WheelProtocol.isExtra(intent.action))
            return C11WheelProtocol.extra(extras?.get("ICU_MediaSwitch") ?: extras?.get("mediaSwitch"),
                extras?.get("ICU_MediaKey") ?: extras?.get("mediaKey"))
        fun json(text: String): String? {
            val root = runCatching { JSONObject(text) }.getOrNull() ?: return null
            if (root.optString("src") == "diplay") return null
            if (root.optString("type").let { it.isNotEmpty() && !it.equals("music", true) }) return null
            return root.optJSONObject("data")?.optString("action")
        }
        if (extras?.containsKey("receiver") == true) {
            val action = when (val payload = extras.get("receiver")) {
                is ByteArray -> {
                    if (payload.size <= 2) return null
                    val length = (payload[0].toInt() and 255) * 100 + (payload[1].toInt() and 255)
                    if (length <= 0 || length > payload.size - 2) return null
                    json(String(payload, 2, length, Charsets.UTF_8))
                }
                is String -> json(payload)
                else -> null
            }
            return C11WheelProtocol.text(action)
        }
        if (extras?.containsKey("action") == true) {
            val raw = extras.get("action") as? String ?: return null
            return C11WheelProtocol.text(if (raw.trim().startsWith("{")) json(raw) else raw)
        }
        return C11WheelProtocol.action(intent.action)
    }
}
