"""C11 bounded input interception, independent video geometry and capture recovery."""

def apply(target, replace):
    java = target/'common/src/main/java/com/shilapi/xcertplay'
    base = target/'shared/src/main/java/com/shilapi/xcertplay/media'
    presentation = java/'ClusterMapPresentation.kt'
    replace(presentation, '            root.addView(textureView, videoParams)\n            videoView = textureView\n        } else if (plan != null)', '''            val blended = C11ClusterBlendLayout(context)
            blended.addView(textureView, FrameLayout.LayoutParams(-1, -1))
            root.addView(blended, videoParams)
            videoView = textureView
        } else if (plan != null)''')

    replace(presentation, '            val textureView = TextureView(context)\n            textureView.surfaceTextureListener',
        '            val textureView = TextureView(context).apply { isOpaque = false }\n            textureView.surfaceTextureListener')

    # Pass the requested alt-screen dimensions all the way to that decoder, including mirrors.
    sink = base/'AndroidMediaSink.kt'
    replace(sink, '    private val mtkDecoderTuningEnabled: Boolean = false,\n) : MediaSink {', '''    private val mtkDecoderTuningEnabled: Boolean = false,
    private val clusterVideoWidth: Int = videoWidth,
    private val clusterVideoHeight: Int = videoHeight,
) : MediaSink {''')
    replace(sink, '        videoWidth,\n        videoHeight,', '''        if (type == 111) clusterVideoWidth else videoWidth,
        if (type == 111) clusterVideoHeight else videoHeight,''')
    host = java/'CarPlayHostActivity.kt'
    replace(host, '                if (C11ClusterRoute.plan(size.x, size.y) != null) {',
        '                if (C11ClusterRoute.plan(size.x, size.y) != null) {\n                    C11ClusterRoute.normalizeLegacyCenter(this)')
    replace(host, '; window=right720")',
        '; window=right720 safeArea=${it.safeArea} content=${it.initialUrl} requestedMarker=${AirPlayPersistence.loadClusterMarkerXPercent(this)},${AirPlayPersistence.loadClusterMarkerYPercent(this)}")')
    replace(host, '            videoHeight = airPlayConfig.main.heightPixels,', '''            videoHeight = airPlayConfig.main.heightPixels,
            clusterVideoWidth = airPlayConfig.cluster?.widthPixels ?: airPlayConfig.main.widthPixels,
            clusterVideoHeight = airPlayConfig.cluster?.heightPixels ?: airPlayConfig.main.heightPixels,''')
    replace(host, '        videoHeight: Int,\n        controllerGeneration:', '''        videoHeight: Int,
        clusterVideoWidth: Int = videoWidth,
        clusterVideoHeight: Int = videoHeight,
        controllerGeneration:''')
    # The sink factory uses positional width/height; add named independent dimensions at its end.
    replace(host, '            mtkDecoderTuningEnabled = AirPlayPersistence.loadMtkDecoderTuning(this),', '''            mtkDecoderTuningEnabled = AirPlayPersistence.loadMtkDecoderTuning(this),
            clusterVideoWidth = clusterVideoWidth,
            clusterVideoHeight = clusterVideoHeight,''')

    # Legacy BYD defaults are not C11 measurements. Preserve every explicit marker setting.
    persistence = java/'AirPlayPersistence.kt'
    replace(persistence, '        val step = prefs.getInt(KEY_CLUSTER_MARKER_X, 0)\n        return', '''        if (!prefs.contains(KEY_CLUSTER_MARKER_X) && C11ClusterRoute.platformSupported()) return C11ClusterRoute.DEFAULT_MARKER_X
        val step = prefs.getInt(KEY_CLUSTER_MARKER_X, 0)
        return''')
    replace(persistence, '        val step = prefs.getInt(KEY_CLUSTER_MARKER_Y, 0)\n        return', '''        if (!prefs.contains(KEY_CLUSTER_MARKER_Y) && C11ClusterRoute.platformSupported()) return C11ClusterRoute.DEFAULT_MARKER_Y
        val step = prefs.getInt(KEY_CLUSTER_MARKER_Y, 0)
        return''')

    keys = java/'CarPlayMediaKeys.kt'
    replace(keys, '    private fun send(index: Int, source: String) {', '''    /** Keep hardware media keys addressed to CarPlay even before the first music packet. */
    @Synchronized
    internal fun holdC11Session() {
        val context = appContext ?: return
        if (!C11ClusterRoute.platformSupported() || controller == null) return
        val mode = context.getSystemService(AudioManager::class.java)?.mode
        if (com.shilapi.xcertplay.hud.BydNavigationOutputs.carPlayCall() != null ||
            mode == AudioManager.MODE_IN_CALL || mode == AudioManager.MODE_RINGTONE) return
        if (session == null) { start(context); publishPlaybackStateLocked() }
    }

    private fun send(index: Int, source: String): Boolean {''')

    replace(keys, '        if (!C11WheelKeys.claim(index)) return', '        if (!C11WheelKeys.claim(index)) return C11WheelKeys.duplicateWasDelivered()')
    replace(keys, '            return\n        }\n        val sent = synchronized(this) { controller }?.sendMediaButton(index)',
        '            return C11WheelKeys.deliveryResult(index, true)\n        }\n        val sent = synchronized(this) { controller }?.sendMediaButton(index)')
    replace(keys, '        WheelKeyLog.note("media key $source -> CarPlay $index sent=$sent")\n    }',
        '        WheelKeyLog.note("media key $source -> CarPlay $index sent=$sent")\n        return C11WheelKeys.deliveryResult(index, sent)\n    }')
    replace(keys, '        send = ::send,', '        send = { index, source -> send(index, source); Unit },')

    settings = java/'DiPlayActivity.kt'
    replace(settings, '                                AirPlayPersistence.saveClusterMarkerXPercent(this, 50)\n                                AirPlayPersistence.saveClusterMarkerYPercent(this, 45)',
        '                                AirPlayPersistence.saveClusterMarkerXPercent(this, if (C11ClusterRoute.platformSupported()) C11ClusterRoute.DEFAULT_MARKER_X else 50)\n                                AirPlayPersistence.saveClusterMarkerYPercent(this, if (C11ClusterRoute.platformSupported()) C11ClusterRoute.DEFAULT_MARKER_Y else 45)')

    # Recovery is deliberately C11-only and keeps the user's recording source unchanged.
    replace(sink, '                    telephonySourceOverride = C11MicrophoneProfile.source(appContext),', '''                    telephonySourceOverride = C11MicrophoneProfile.source(appContext),
                    recoverSilentCapture = C11MicrophoneProfile.supported(),''')
    mic = base/'MicrophoneUplink.kt'
    replace(mic, '    private val telephonySourceOverride: Int? = null,', '''    private val telephonySourceOverride: Int? = null,
    private val recoverSilentCapture: Boolean = false,
    private val silentCaptureMillis: Long = 2_000L,''')
    replace(mic, '        var lastAudioNs = System.nanoTime()', '''        var lastAudioNs = System.nanoTime()
        val silenceRecovery = C11CaptureRecovery(silentCaptureMillis)
        var effectsBypassed = false''')
    replace(mic, '                lastAudioNs = System.nanoTime()\n                var offset = 0', '''                lastAudioNs = System.nanoTime()
                if (recoverSilentCapture && silenceRecovery.inspect(readBuffer, count, lastAudioNs / 1_000_000L)) {
                    // Positive reads containing digital zeros never entered upstream's no-audio recovery.
                    // Bypass only effects attached by this recorder; never mute/unmute the system mic.
                    effects.forEach { effect -> runCatching { effect.setEnabled(false) } }
                    effectsBypassed = true
                    val restarted = restartRecording(recorder)
                    filled = 0
                    runCatching { onDiagnostic("C11 microphone silent capture recovery attempt=${silenceRecovery.attempts} " +
                        "effectsBypassed=true restarted=$restarted routedDeviceType=${routeType(recorder)} source=${recorder.audioSource}") }
                    continue
                }
                var offset = 0''')
    # Do not re-enable the same problematic effects if the optional software canceller later exits.
    replace(mic, '                                restorePlatformEchoCancellation()\n                                canceller = null', '''                                if (!effectsBypassed) restorePlatformEchoCancellation()
                                canceller = null''')

    replace(sink, '"softwareEchoRequested=$callEchoCancellation carPhoneAudio=${PhoneAudioRoute.carPlayCallsUseCarAudio()}")',
        '"softwareEchoRequested=$callEchoCancellation carPhoneAudio=${PhoneAudioRoute.carPlayCallsUseCarAudio()} " +\n                        "bluetoothSco=${audio?.isBluetoothScoOn} inputs=${audio?.getDevices(AudioManager.GET_DEVICES_INPUTS)?.joinToString { \"${it.id}:${it.type}\" }}")')

    replace(java/'DiPlayActivity.kt', '        appendLine(C11MusicGuard.diagnostic(appContext))',
        '        appendLine(C11MusicGuard.diagnostic(appContext))\n        appendLine(C11AudioDiagnostics.report(appContext))')

    import card_size
    card_size.apply(target, replace)
