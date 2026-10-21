"""Read-only capture and viewport evidence; no audio routing or map adjustment."""
def apply(target, replace):
    base = target/'shared/src/main/java/com/shilapi/xcertplay/media'
    replace(base/'MicrophoneCaptureStats.kt', '    private var peakSample = 0', '    private var peakSample = 0\n    private var inputPeakSample = 0')
    replace(base/'MicrophoneCaptureStats.kt', '    fun level(pcm: ByteArray) {', '''    fun inputLevel(pcm: ByteArray) {
        var index = 0
        while (index + 1 < pcm.size) {
            val sample = (pcm[index].toInt() and 0xff) or (pcm[index + 1].toInt() shl 8)
            inputPeakSample = maxOf(inputPeakSample, kotlin.math.abs(sample))
            index += 2
        }
    }

    fun level(pcm: ByteArray) {''')
    replace(base/'MicrophoneCaptureStats.kt', 'peakDbfs=${peakDbfs(peakSample)} ended=$ended',
        'inputPeakDbfs=${peakDbfs(inputPeakSample)} peakDbfs=${peakDbfs(peakSample)} ended=$ended')
    replace(base/'MicrophoneCaptureStats.kt', '        peakSample = 0', '        peakSample = 0\n        inputPeakSample = 0')
    replace(base/'MicrophoneUplink.kt', '                    if (filled == frame.size) {',
        '                    if (filled == frame.size) {\n                        stats.inputLevel(frame) // Before the optional software echo canceller.')
    replace(base/'AndroidMediaSink.kt', '            val uplink = microphoneUplinks.computeIfAbsent(id) {', '''            val uplink = microphoneUplinks.computeIfAbsent(id) {
                if (config.audioType == "telephony" && C11MicrophoneProfile.supported()) runCatching {
                    val audio = appContext?.getSystemService(Context.AUDIO_SERVICE) as? AudioManager
                    onAudioDiagnostic("C11 call context sourceSelection=${appContext?.let(C11MicrophoneProfile::selected)} " +
                        "audioMode=${audio?.mode} systemMicMuted=${audio?.isMicrophoneMute} " +
                        "softwareEchoRequested=$callEchoCancellation carPhoneAudio=${PhoneAudioRoute.carPlayCallsUseCarAudio()}")
                }''')

    engine = target/'shared/src/main/java/com/shilapi/xcertplay/airplay/CarPlayMediaEngine.kt'
    replace(engine, '            session.logDebug("Video: $it")',
        '            session.logDebug("Video: $it")\n            if (it.startsWith("output format")) session.logDebug("Video stream=$type: $it")')
