"""Optional single-APK media-session suppression, without system audio or vehicle writes."""
def apply(target, replace):
    java = target / 'common/src/main/java/com/shilapi/xcertplay'
    replace(java/'CarPlayHostActivity.kt', '                    activeAirPlaySession = session',
        '                    activeAirPlaySession = session\n                    C11MusicGuard.start(this@CarPlayHostActivity, session)')
    replace(java/'CarPlayHostActivity.kt', '                    startupRetryBudget.disconnected()\n                    activeAirPlaySession = null',
        '                    C11MusicGuard.stop(session)\n                    startupRetryBudget.disconnected()\n                    activeAirPlaySession = null')
    replace(java/'DiPlayActivity.kt', '        toggle(card, getString(R.string.settings_c11_wheel),',
        '''        toggle(card, getString(R.string.settings_c11_music_guard), getString(R.string.settings_c11_music_guard_description),
            C11MusicGuard.enabled(this)) { C11MusicGuard.setEnabled(this, it) }
        toggle(card, getString(R.string.settings_c11_music_restore), getString(R.string.settings_c11_music_restore_description),
            C11MusicGuard.restoreEnabled(this)) { C11MusicGuard.setRestore(this, it) }
        card.addView(button(getString(R.string.settings_c11_music_access), false) {
            runCatching { startActivity(android.content.Intent(android.provider.Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)) }
                .onFailure { android.widget.Toast.makeText(this, getString(R.string.settings_c11_music_access_unavailable), android.widget.Toast.LENGTH_LONG).show() }
        }, matchButton(0, 60))
        toggle(card, getString(R.string.settings_c11_wheel),''')
    replace(java/'DiPlayActivity.kt', '        appendLine(ClusterMapPresentation.diagnosticReport(appContext))',
        '        appendLine(ClusterMapPresentation.diagnosticReport(appContext))\n        appendLine(C11MusicGuard.diagnostic(appContext))')
    manifest = target/'common/src/main/AndroidManifest.xml'
    replace(manifest, '    <application>', '''    <application>
        <service android:name="com.shilapi.xcertplay.C11MusicAccessService"
            android:label="@string/app_name" android:exported="true"
            android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE">
            <intent-filter><action android:name="android.service.notification.NotificationListenerService" /></intent-filter>
        </service>''')
    from xml.sax.saxutils import escape
    copy = {
      'values': ('Pause head-unit music during CarPlay (experimental)', 'Off by default. Requires notification access below. Pauses supported NetEase, QQ Music and Kuwo media sessions during CarPlay; does not change system volume. Unsupported players may still overlap. Applies immediately.', 'Restore previous music after disconnect', 'Only resumes a still-available session that was playing when CarPlay monitoring started and was paused by this feature. Calls take priority. Music first started during CarPlay stays paused.', 'Open notification access', 'Open the system notification access settings manually; enable this app.'),
      'values-zh-rCN': ('CarPlay 原车音乐互斥（实验性）', '默认关闭。需在下方开启通知使用权。连接 CarPlay 时暂停可识别的网易云、QQ 音乐与酷我媒体会话，不调整系统音量。不支持的播放器仍可能重叠。开关立即生效。', '断开后恢复原车音乐', '仅恢复开始监听时正在播放、被本功能暂停且仍可用的会话。通话优先。连接期间新启动的音乐不自动恢复。', '打开通知使用权设置', '请手动打开系统通知使用权设置，为本应用开启权限。'),
      'values-zh-rTW': ('CarPlay 原車音樂互斥（實驗性）', '預設關閉。須開啟通知存取權。連線時暫停支援的網易雲、QQ 音樂及酷我媒體工作階段，不調整系統音量。不支援的播放器仍可能重疊。立即生效。', '斷線後恢復原車音樂', '只恢復開始監聽時正在播放、由此功能暫停且仍可用的工作階段。通話優先。連線期間新啟動的音樂不自動恢復。', '開啟通知存取權設定', '請手動開啟系統通知存取權設定，為本應用程式授權。'),
      'values-ar': ('إيقاف موسيقى السيارة أثناء CarPlay (تجريبي)', 'معطل افتراضيًا. يتطلب إذن الإشعارات. يوقف جلسات NetEase وQQ وKuwo المدعومة دون تغيير مستوى النظام. قد تتداخل التطبيقات غير المدعومة. يسري فورًا.', 'استعادة الموسيقى بعد الفصل', 'يستأنف فقط الجلسة المتاحة التي كانت تعمل عند بدء المراقبة وأوقفها هذا الخيار. المكالمات لها الأولوية. لا يستأنف الموسيقى الجديدة.', 'فتح إذن الإشعارات', 'افتح إعدادات الوصول للإشعارات يدويًا واسمح لهذا التطبيق.'),
      'values-it': ('Pausa musica auto con CarPlay (sperimentale)', 'Disattivato. Richiede accesso alle notifiche. Mette in pausa sessioni NetEase, QQ e Kuwo supportate, senza cambiare il volume. Altri lettori possono sovrapporsi. Effetto immediato.', 'Ripristina musica dopo disconnessione', 'Riprende solo la sessione ancora disponibile che era in riproduzione e che questa funzione ha sospeso. Priorità alle chiamate. Non riprende nuova musica.', 'Apri accesso notifiche', 'Aprire manualmente accesso notifiche nelle impostazioni e autorizzare questa app.'),
      'values-es': ('Pausar música del coche con CarPlay (experimental)', 'Desactivado. Requiere acceso a notificaciones. Pausa sesiones compatibles de NetEase, QQ y Kuwo sin cambiar el volumen. Otros reproductores pueden superponerse. Efecto inmediato.', 'Restaurar música al desconectar', 'Solo reanuda la sesión disponible que ya sonaba y fue pausada por esta función. Las llamadas tienen prioridad. No reanuda música nueva.', 'Abrir acceso a notificaciones', 'Abre manualmente el acceso a notificaciones y autoriza esta aplicación.'),
      'values-ja': ('CarPlay 中に車載音楽を一時停止（実験的機能）', '初期設定はオフ。通知アクセスが必要です。対応する NetEase、QQ、Kuwo のセッションを一時停止します。システム音量は変更しません。未対応アプリは重複する場合があります。即時反映。', '切断後に元の音楽を再開', '監視開始時に再生中で、この機能が停止した利用可能なセッションのみ再開します。通話優先。接続中に新しく始まった音楽は再開しません。', '通知アクセス設定を開く', 'システムの通知アクセス設定を手動で開き、このアプリを許可してください。'),
      'values-ru': ('Пауза музыки машины при CarPlay (экспериментально)', 'Выключено. Нужен доступ к уведомлениям. Приостанавливает поддерживаемые сеансы NetEase, QQ и Kuwo без изменения громкости. Другие плееры могут звучать одновременно. Действует сразу.', 'Возобновлять музыку после отключения', 'Возобновляет только доступный сеанс, который играл до наблюдения и был приостановлен функцией. Звонки приоритетны. Новая музыка не возобновляется.', 'Доступ к уведомлениям', 'Откройте системный доступ к уведомлениям вручную и разрешите этому приложению.'),
      'values-uk': ('Пауза музики авто під час CarPlay (експериментально)', 'Вимкнено. Потрібен доступ до сповіщень. Призупиняє підтримувані сеанси NetEase, QQ і Kuwo без зміни гучності. Інші плеєри можуть накладатися. Діє одразу.', 'Відновлювати музику після відключення', 'Відновлює лише доступний сеанс, що грав до спостереження та був зупинений функцією. Дзвінки мають пріоритет. Нова музика не відновлюється.', 'Доступ до сповіщень', 'Відкрийте системний доступ до сповіщень вручну та дозвольте цей застосунок.'),
    }
    keys = ['settings_c11_music_guard','settings_c11_music_guard_description','settings_c11_music_restore','settings_c11_music_restore_description','settings_c11_music_access','settings_c11_music_access_unavailable']
    for locale, values in copy.items():
        entries = ''.join('    <string name="'+k+'">'+escape(v).replace("'", "\\'")+'</string>\n' for k,v in zip(keys,values))
        replace(target/'common/src/main/res'/locale/'strings.xml', '</resources>', entries+'</resources>')
