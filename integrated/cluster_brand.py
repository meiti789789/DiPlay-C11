"""C11 public-display route and Leapmotor visual branding; no system/vehicle writes."""
from pathlib import Path
import re
from xml.sax.saxutils import escape

def apply(target,replace):
    java=target/'common/src/main/java/com/shilapi/xcertplay'
    replace(java/'AirPlayPersistence.kt', '    const val DEFAULT_OEM_LABEL = "BYD"', '    const val DEFAULT_OEM_LABEL = "零跑"')
    replace(java/'AirPlayPersistence.kt',
        '.getString(KEY_OEM_LABEL, DEFAULT_OEM_LABEL)\n            // iOS hides the car icon without a label.\n            .orEmpty().ifBlank { DEFAULT_OEM_LABEL }',
        '.getString(KEY_OEM_LABEL, DEFAULT_OEM_LABEL)\n            // Keep custom names; migrate only the inherited BYD default.\n            .orEmpty().let { if (it.isBlank() || it.equals("BYD", true) || it == "比亚迪" || it == "比亞迪") DEFAULT_OEM_LABEL else it }')
    presentation=java/'ClusterMapPresentation.kt'
    replace(presentation,'        val adaptive = DiLink51ClusterLayout.supported()',
        '        val c11 = C11ClusterRoute.plan(size.x, size.y)\n        val adaptive = DiLink51ClusterLayout.supported()')
    replace(presentation,'setBackgroundColor(if (plan == null) placeholder else if (plan.fullMap) backdrop else Color.TRANSPARENT)',
        'setBackgroundColor(if (c11 != null) Color.TRANSPARENT else if (plan == null) placeholder else if (plan.fullMap) backdrop else Color.TRANSPARENT)')
    replace(presentation,'        if (plan != null) {\n            window?.setBackgroundDrawable',
        '        if (plan != null || c11 != null) {\n            window?.setBackgroundDrawable')
    replace(presentation,'        val videoParams = if (plan == null) FrameLayout.LayoutParams(-1, -1) else',
        '        val videoParams = if (c11 != null) FrameLayout.LayoutParams(c11.width, c11.height, Gravity.TOP or Gravity.LEFT)\n            else if (plan == null) FrameLayout.LayoutParams(-1, -1) else')
    replace(presentation,'        setContentView(root)\n    }',
        '''        setContentView(root)
        C11ClusterRoute.configureWindow(window, display)
    }

    override fun onStart() {
        super.onStart()
        C11ClusterRoute.configureWindow(window, display)
    }''')
    anchor='''        fun findDisplay(context: Context, theme: DiLink51ClusterLayout.Theme = DiLink51ClusterLayout.theme(context)): Display? {
            val displays'''
    replace(presentation,anchor,'''        fun findDisplay(context: Context, theme: DiLink51ClusterLayout.Theme = DiLink51ClusterLayout.theme(context)): Display? {
            if (C11ClusterRoute.platformSupported()) return C11ClusterRoute.findDisplay(context)
            val displays''')
    replace(presentation,'            appendLine("clusterEnabled=${AirPlayPersistence.loadClusterMapEnabled(context)}")',
        '            appendLine("clusterEnabled=${AirPlayPersistence.loadClusterMapEnabled(context)}")\n            appendLine(C11ClusterRoute.diagnostic(context))')
    replace(java/'CarPlayHostActivity.kt','''            if (size.x > 0 && size.y > 0) {
                clusterStreamOnDisplay = true''',
        '''            if (size.x > 0 && size.y > 0) {
                clusterStreamOnDisplay = true
                if (C11ClusterRoute.plan(size.x, size.y) != null) {
                    return C11ClusterRoute.streamConfig(AirPlayPersistence.loadClusterContent(this),
                        scalePercent = AirPlayPersistence.loadClusterMapScalePercent(this),
                        markerXPercent = AirPlayPersistence.loadClusterMarkerXPercent(this),
                        markerYPercent = AirPlayPersistence.loadClusterMarkerYPercent(this)).also {
                        MapMirrors.streamAspect = 1.0
                        appendLog("C11 cluster: ${it.widthPixels}x${it.heightPixels} stream on explicitly selected ${display.displayId}:${display.name}; window=right720")
                    }
                }''')
    replace(java/'DiPlayActivity.kt','''            getString(R.string.carplay_map_on_instrument_cluster_experimental), R.drawable.ic_dp_dashboard) { card ->''',
        '''            getString(R.string.carplay_map_on_instrument_cluster_experimental), R.drawable.ic_dp_dashboard) { card ->
            if (C11ClusterRoute.platformSupported()) {
                val candidates = C11ClusterRoute.candidates(this)
                val selected = C11ClusterRoute.findDisplay(this)
                card.addView(label(getString(R.string.settings_c11_cluster_display) + " · " +
                    (selected?.let { "#${it.displayId} ${it.name}" } ?: getString(R.string.settings_c11_cluster_none)), 16, TEXT))
                candidates.forEach { candidate ->
                    card.addView(button(getString(R.string.settings_c11_probe_title, candidate.displayId) + " · " + candidate.name.take(32), false) {
                        C11DisplayProbe.show(this, candidate) { markReconnectNeeded(); render() }
                    }, matchButton(0, 60))
                }
                card.addView(button(getString(R.string.settings_c11_cluster_none), false) {
                    C11ClusterRoute.select(this, null); markReconnectNeeded(); render()
                }, matchButton(0, 60))
                card.addView(label(getString(R.string.settings_c11_cluster_description), 14, MUTED))
            }''')
    replace(java/'DiPlayActivity.kt', '        // The joystick and map zoom use BYD\'s media and custom keys.',
        '        if (C11ClusterRoute.platformSupported()) return\n        // The joystick and map zoom use BYD\'s media and custom keys.')
    replace(java/'AdbClusterRouter.kt', '    fun enabled(context: Context): Boolean {',
        '    fun enabled(context: Context): Boolean {\n        if (C11ClusterRoute.platformSupported()) return false')
    replace(java/'DiPlayActivity.kt', '            val diLink3 = DiLinkGeneration.current(this) == DiLinkGeneration.DILINK_3',
        '            val diLink3 = C11ClusterRoute.platformSupported() || DiLinkGeneration.current(this) == DiLinkGeneration.DILINK_3')
    replace(java/'DiPlayActivity.kt', '        if (settingsSectionFilter?.contains(key) == false) return',
        '        if (C11ClusterRoute.platformSupported() && key in setOf(SettingsSection.BYD_ADB,\n                SettingsSection.BYD_NAVIGATION, SettingsSection.AMBIENT_LIGHTING, SettingsSection.NAVIGATION_WHEEL)) return\n        if (settingsSectionFilter?.contains(key) == false) return')
    translations={
        'values':('C11 instrument display (experimental)','Not selected; do not project','Only choose a public 1920×720 display confirmed to be the instrument panel, never the passenger panel. Reconnect CarPlay after selecting. The window stays in the right 720×720 area. No candidates? Export diagnostics; do not force access.','Leapmotor instrument navigation: select the verified public instrument display under Advanced → instrument map. HUD support is not established.','Choose gestures that do not conflict with this head unit. Test while parked.'),
        'values-zh-rCN':('C11 仪表屏幕（实验性）','未选择，不投屏','仅选择已确认属于仪表的公开 1920×720 屏幕，不要选择副驾屏。选择后需重新连接 CarPlay。窗口限制在右侧 720×720。无候选屏幕时请导出诊断，不强行授权。','零跑仪表导航：请在“高级→仪表地图”中选择已确认的公开仪表屏幕。尚未适配 HUD。','选择不会与原车功能冲突的手势数量，请停车测试。'),
        'values-zh-rTW':('C11 儀表螢幕（實驗性）','未選擇，不投影','僅選擇已確認屬於儀表的公開 1920×720 螢幕，勿選副駕駛螢幕。選擇後須重新連線 CarPlay。視窗限於右側 720×720。無候選時請匯出診斷，勿強制授權。','零跑儀表導航：請在進階的儀表地圖中選擇已確認的公開儀表螢幕。尚未適配 HUD。','請選擇不與原車功能衝突的手勢數量，停車時測試。'),
        'values-ar':('شاشة عدادات C11 (تجريبي)','غير محددة؛ لا عرض','اختر فقط شاشة عامة 1920×720 مؤكدة للعدادات، وليس شاشة الراكب. أعد توصيل CarPlay بعد الاختيار. النافذة في المنطقة اليمنى 720×720. عند غياب شاشة صدّر التشخيص دون فرض الصلاحيات.','ملاحة Leapmotor: اختر شاشة العدادات العامة المؤكدة ضمن الإعدادات المتقدمة. دعم HUD غير مثبت.','اختر إيماءات لا تتعارض مع وظائف السيارة واختبر أثناء الوقوف.'),
        'values-it':('Display strumenti C11 (sperimentale)','Nessuna selezione; nessuna proiezione','Selezionare solo un display pubblico 1920×720 confermato come quadro strumenti, mai quello del passeggero. Ricollegare CarPlay. Finestra limitata a destra a 720×720. Senza candidati esportare la diagnostica, senza forzare permessi.','Navigazione Leapmotor: selezionare il display strumenti verificato nelle impostazioni avanzate. HUD non verificato.','Scegliere gesti senza conflitti con il veicolo e provare da fermi.'),
        'values-es':('Pantalla de instrumentos C11 (experimental)','Sin selección; sin proyección','Elige solo una pantalla pública 1920×720 confirmada como cuadro de instrumentos, nunca la del pasajero. Reconecta CarPlay. Ventana derecha de 720×720. Sin candidatos, exporta el diagnóstico sin forzar permisos.','Navegación Leapmotor: elige la pantalla pública de instrumentos verificada en ajustes avanzados. HUD sin verificar.','Elige gestos sin conflictos con el vehículo y prueba estacionado.'),
        'values-ja':('C11 メーターディスプレイ（実験的機能）','未選択・投影しない','メーターと確認済みの公開 1920×720 画面のみ選択し、助手席画面は選ばないでください。選択後は CarPlay を再接続してください。表示は右側 720×720 に制限します。候補がなければ権限を強制せず診断を保存してください。','零跑のメーター表示は詳細設定で確認済みの公開画面を選択してください。HUD は未対応です。','車両の機能と競合しないジェスチャーを選び、停車中にテストしてください。'),
        'values-ru':('Экран приборов C11 (экспериментально)','Не выбран; без проекции','Выберите только подтверждённый публичный экран приборов 1920×720, не экран пассажира. Переподключите CarPlay. Окно справа 720×720. Нет кандидатов — сохраните диагностику, не выдавайте принудительно права.','Навигация Leapmotor: выберите подтверждённый экран приборов в расширенных настройках. HUD не проверен.','Выбирайте жесты без конфликтов с машиной и проверяйте на стоянке.'),
        'values-uk':('Екран приладів C11 (експериментально)','Не вибрано; без проєкції','Виберіть лише підтверджений публічний екран приладів 1920×720, не екран пасажира. Перепідключіть CarPlay. Вікно праворуч 720×720. Немає кандидатів — збережіть діагностику, не примушуйте дозволи.','Навігація Leapmotor: виберіть підтверджений екран приладів у розширених налаштуваннях. HUD не перевірено.','Вибирайте жести без конфліктів із машиною та перевіряйте на стоянці.'),
    }
    def xml(text):return escape(text).replace("'","\\'")
    speaker_notes={'values': 'Audio channels vary by firmware. Do not assume a number identifies the driver speaker.', 'values-zh-rCN': '声道编号取决于车机固件，不能按数字猜测主驾扬声器。', 'values-zh-rTW': '聲道編號取決於車機韌體，勿憑數字猜測駕駛座揚聲器。', 'values-ar': 'تختلف قنوات الصوت حسب البرنامج الثابت. لا تفترض أن رقمًا يحدد سماعة السائق.', 'values-it': 'I canali audio dipendono dal firmware. Non presumere quale numero identifichi lo speaker del conducente.', 'values-es': 'Los canales de audio dependen del firmware. No supongas qué número corresponde al altavoz del conductor.', 'values-ja': '音声チャンネルはファームウェアによって異なります。番号だけで運転席スピーカーを判断しないでください。', 'values-ru': 'Аудиоканалы зависят от прошивки. Не определяйте динамик водителя только по номеру.', 'values-uk': 'Аудіоканали залежать від прошивки. Не визначайте динамік водія лише за номером.'}
    for folder,values in translations.items():
        path=target/'common/src/main/res'/folder/'strings.xml'
        entries=''.join(f'    <string name="{key}">{xml(value)}</string>\n' for key,value in zip(
            ['settings_c11_cluster_display','settings_c11_cluster_none','settings_c11_cluster_description'],values[:3]))
        replace(path,'</resources>',entries+'</resources>')
        # Replace generic visible BYD branding with accurate C11 wording, not false capability claims.
        for resource in (target/'common/src/main/res'/folder).glob('*.xml'):
            text=resource.read_text()
            for key,value in [('settings_byd_navigation_unavailable',values[3]),('settings_gesture_fingers_hint',values[4]),('tap_a_number_to_test_14_driver_speaker_on_byd',speaker_notes[folder])]:
                text=re.sub(r'(<string name="'+key+r'">).*?(</string>)',lambda m:m[1]+xml(value)+m[2],text,flags=re.S)
            text=re.sub(r'(<string name="app_name">).*?(</string>)',
                lambda m:m[1]+('零跑 C11' if 'zh' in folder else 'Leapmotor C11')+m[2],text,flags=re.S)
            resource.write_text(text)
    for resource in (target/'mobile/src/main/res').glob('values*/strings.xml'):
        text=resource.read_text();text=re.sub(r'(<string name="app_name">).*?(</string>)',
            lambda m:m[1]+('零跑 C11' if 'zh' in str(resource.parent) else 'Leapmotor C11')+m[2],text,flags=re.S);resource.write_text(text)
    # Default locale is English; localized Chinese override is in common resources.
    original=target/'common/src/main/res/drawable/ic_carplay.png'
    if original.exists():original.unlink()
    (target/'C11-BRAND-NOTICE.md').write_text((Path(__file__).parent/'BRAND_NOTICE.md').read_text())

    ui = target/'common/src/test/java/com/shilapi/xcertplay/AdaptiveSettingsUiTest.kt'
    replace(ui, '    private fun openSettings(): DiPlayActivity',
        (Path(__file__).parent/'preview_tests.txt').read_text() + '    private fun openSettings(): DiPlayActivity')
