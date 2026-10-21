from xml.sax.saxutils import escape

def apply(target, replace):
    base=target/'shared/src/main/java/com/shilapi/xcertplay/media'
    replace(base/'MicrophoneUplink.kt', '    private val noAudioRestartMillis: Long = NO_AUDIO_RESTART_MILLIS,',
        '    private val noAudioRestartMillis: Long = NO_AUDIO_RESTART_MILLIS,\n    private val telephonySourceOverride: Int? = null,')
    replace(base/'MicrophoneUplink.kt', '        val source = when {',
        '        val source = telephonySourceOverride?.takeIf { config.audioType == "telephony" } ?: when {')
    replace(base/'MicrophoneUplink.kt', '        val bufferSize = maxOf(minBuffer * 2, config.frameBytes * 4)',
        '''        stats.useSourceName(when (source) {
            MediaRecorder.AudioSource.VOICE_RECOGNITION -> "VOICE_RECOGNITION"
            MediaRecorder.AudioSource.VOICE_COMMUNICATION -> "VOICE_COMMUNICATION"
            MediaRecorder.AudioSource.MIC -> "MIC"
            else -> "DEFAULT"
        })
        val bufferSize = maxOf(minBuffer * 2, config.frameBytes * 4)''')
    replace(base/'MicrophoneCaptureStats.kt', '    fun useVoiceCommunicationSource()',
        '    fun useSourceName(source: String) { metadata = "type=$type source=$source $format" }\n\n    fun useVoiceCommunicationSource()')
    replace(base/'AndroidMediaSink.kt', '                    speakerphoneCall = speakerphoneCall,',
        '                    speakerphoneCall = speakerphoneCall,\n                    telephonySourceOverride = C11MicrophoneProfile.source(appContext),')
    java=target/'common/src/main/java/com/shilapi/xcertplay'
    replace(java/'DiPlayActivity.kt', '        filteredSection(content, SettingsSection.ADVANCED_MEDIA,',
        '        filteredSection(content, SettingsSection.ADVANCED_MEDIA,') # Keep the existing bounded anchor check.
    # Inject at the beginning of the existing Advanced media card.
    path=java/'DiPlayActivity.kt';text=path.read_text();start=text.index('        filteredSection(content, SettingsSection.ADVANCED_MEDIA,');end=text.index('{ card ->',start)+len('{ card ->')
    text=text[:end]+'''
            if (C11ClusterRoute.platformSupported()) {
                choice(card, getString(R.string.settings_c11_mic_source), listOf(
                    getString(R.string.settings_c11_mic_default), getString(R.string.settings_c11_mic_recognition),
                    getString(R.string.settings_c11_mic_plain)), com.shilapi.xcertplay.media.C11MicrophoneProfile.selected(this),
                    reconnects = false, announcesReconnect = false) {
                    com.shilapi.xcertplay.media.C11MicrophoneProfile.save(this, it)
                }
                card.addView(label(getString(R.string.settings_c11_mic_description), 14, MUTED))
            }
'''+text[end:];path.write_text(text)
    replace(java/'DiPlayActivity.kt', '        appendLine(C11MusicGuard.diagnostic(appContext))',
        '        appendLine(C11MusicGuard.diagnostic(appContext))\n        appendLine("C11 call microphone sourceSelection=${com.shilapi.xcertplay.media.C11MicrophoneProfile.selected(appContext)}")')
    copy={
     'values':('C11 call microphone source (experimental)','Upstream default','Voice recognition source','Plain microphone source','Applies to the next call only. Hang up before changing. Start with voice recognition if calls record silence; return to default if it fails. This changes only this app recorder, not system routing or volume. Not vehicle-verified.'),
     'values-zh-rCN':('C11 通话录音源（实验性）','沿用上游默认','语音识别录音源','普通麦克风录音源','下次通话生效，请先挂断再更改。录音全零时先试语音识别；无效可恢复默认。只改变本应用录音器，不修改系统路由或音量。尚未实车验证。'),
     'values-zh-rTW':('C11 通話錄音來源（實驗性）','沿用上游預設','語音辨識錄音來源','一般麥克風錄音來源','下次通話生效，請先掛斷再更改。錄音全零時先試語音辨識；無效可恢復預設。只改本應用程式錄音器，不修改系統路由或音量。尚未實車驗證。'),
     'values-ar':('مصدر ميكروفون مكالمات C11 (تجريبي)','الافتراضي الأصلي','مصدر التعرف على الصوت','مصدر الميكروفون العادي','يسري في المكالمة التالية. أنه المكالمة قبل التغيير. جرّب التعرف على الصوت عند الصمت ثم ارجع للافتراضي إن فشل. يغير مسجل التطبيق فقط، لا توجيه النظام أو الصوت. غير مختبر في السيارة.'),
     'values-it':('Sorgente microfono chiamate C11 (sperimentale)','Predefinita originale','Riconoscimento vocale','Microfono normale','Dalla prossima chiamata. Riagganciare prima. In caso di silenzio provare riconoscimento vocale; ripristinare se non funziona. Cambia solo il registratore della app, non volume o instradamento del sistema. Non verificato in auto.'),
     'values-es':('Fuente de micrófono C11 (experimental)','Predeterminada original','Reconocimiento de voz','Micrófono normal','Se aplica a la próxima llamada. Cuelga antes de cambiar. Si graba silencio, prueba reconocimiento de voz; restaura si falla. Solo cambia la grabadora de la app, no rutas ni volumen del sistema. Sin verificar en el coche.'),
     'values-ja':('C11 通話録音ソース（実験的機能）','上流の初期設定','音声認識ソース','通常のマイクソース','次の通話から反映。変更前に通話を終了してください。無音の場合は音声認識を試し、無効なら初期設定に戻してください。本アプリの録音器のみ変更し、システム経路や音量は変更しません。実車未検証。'),
     'values-ru':('Источник микрофона C11 (экспериментально)','Исходный по умолчанию','Распознавание речи','Обычный микрофон','Со следующего звонка. Завершите звонок перед изменением. При тишине попробуйте распознавание речи; при неудаче верните исходный. Меняется только рекордер приложения, не маршруты или громкость системы. В машине не проверено.'),
     'values-uk':('Джерело мікрофона C11 (експериментально)','Початкове типове','Розпізнавання мовлення','Звичайний мікрофон','З наступного дзвінка. Завершіть виклик перед зміною. При тиші спробуйте розпізнавання мовлення; за невдачі поверніть типове. Змінює лише рекордер застосунку, не системні маршрути чи гучність. В авто не перевірено.'),
    }
    keys=['settings_c11_mic_source','settings_c11_mic_default','settings_c11_mic_recognition','settings_c11_mic_plain','settings_c11_mic_description']
    for folder,values in copy.items():
        entries=''.join('    <string name="'+k+'">'+escape(v).replace("'","\\'")+'</string>\n' for k,v in zip(keys,values))
        replace(target/'common/src/main/res'/folder/'strings.xml','</resources>',entries+'</resources>')
