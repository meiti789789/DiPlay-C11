"""A single C11 marker editor, wired to the actual type-111 preferences."""
from xml.sax.saxutils import escape

def apply(target, replace):
    java = target/'common/src/main/java/com/shilapi/xcertplay'
    ui = java/'DiPlayActivity.kt'
    text = ui.read_text()
    start = text.index('                        if (!diLink4 || AirPlayPersistence.loadClusterSafeAreaRect(this) == null) {')
    end = text.index('                        if (!diLink4) {\n                            toggle(card, getString(R.string.dashboard_map_only_in_small_and_full_navi)', start)
    original = text[start:end]
    c11 = '''                        if (C11ClusterRoute.platformSupported()) {
                            // Complete the one-time legacy migration before accepting a manual edit.
                            C11ClusterRoute.normalizeLegacyCenter(this)
                            val c11MarkerControls = LinearLayout(this).apply {
                                orientation = LinearLayout.VERTICAL
                                tag = "c11-marker-controls"
                            }
                            card.addView(c11MarkerControls)
                            c11MarkerControls.addView(label(getString(R.string.settings_c11_marker_description), 14, MUTED))
                            c11MarkerControls.addView(overlaySliderRow(
                                getString(R.string.settings_c11_marker_horizontal),
                                C11ClusterRoute.markerXPercents,
                                AirPlayPersistence.loadClusterMarkerXPercent(this).coerceIn(C11ClusterRoute.markerXPercents.first(), C11ClusterRoute.markerXPercents.last()),
                            ) { overlayOffsetLabel(it, getString(R.string.marker_left), getString(R.string.marker_right), 50) }
                                .also { it.onSave = { v -> AirPlayPersistence.saveClusterMarkerXPercent(this, v) } }
                                .also { it.onCommit = { markReconnectNeeded() } })
                            c11MarkerControls.addView(overlaySliderRow(
                                getString(R.string.settings_c11_marker_vertical),
                                CarPlayClusterDisplay.markerYPercents,
                                AirPlayPersistence.loadClusterMarkerYPercent(this),
                            ) { overlayOffsetLabel(it, getString(R.string.marker_up), getString(R.string.marker_down), 50) }
                                .also { it.onSave = { v -> AirPlayPersistence.saveClusterMarkerYPercent(this, v) } }
                                .also { it.onCommit = { markReconnectNeeded() } })
                            c11MarkerControls.addView(button(getString(R.string.reset_car_marker_to_centre), false) {
                                AirPlayPersistence.saveClusterMarkerXPercent(this, C11ClusterRoute.DEFAULT_MARKER_X)
                                AirPlayPersistence.saveClusterMarkerYPercent(this, C11ClusterRoute.DEFAULT_MARKER_Y)
                                render()
                                markReconnectNeeded()
                            }, matchButton(SETTINGS_HEADER_COMPACT_GAP_DP))
                        } else {
'''
    ui.write_text(text[:start] + c11 + original + '                        }\n' + text[end:])
    # OEM small/full-screen monitoring is unrelated to C11's fixed right-side presentation.
    replace(ui, '                        if (!diLink4) {\n                            toggle(card, getString(R.string.dashboard_map_only_in_small_and_full_navi)',
        '                        if (!diLink4 && !C11ClusterRoute.platformSupported()) {\n                            toggle(card, getString(R.string.dashboard_map_only_in_small_and_full_navi)')
    route = java/'C11ClusterRoute.kt'
    replace(route, '    const val DEFAULT_MARKER_Y = 50',
        '    const val DEFAULT_MARKER_Y = 50\n    val markerXPercents = ((FADE_PERCENT + 5)..95).toList()')
    translations = {
        'values': ('C11 instrument marker · horizontal', 'C11 instrument marker · vertical', 'Adjusts the requested marker position in the right-side instrument map only. Saved across restarts. Reconnect CarPlay to apply; no ADB or usage access needed. The iPhone may also reposition its official turn card; this is not a live pixel translation.'),
        'values-zh-rCN': ('C11 仪表车标 · 左右', 'C11 仪表车标 · 上下', '只调整仪表右侧地图的车标位置请求，保存后重启保留。点击“立即重连”后生效，不需要 ADB 或使用情况访问。iPhone 可能同时调整官方转向卡布局；这不是实时平移画面。'),
        'values-zh-rTW': ('C11 儀表車標 · 左右', 'C11 儀表車標 · 上下', '只調整儀表右側地圖的車標位置請求，儲存後重新啟動保留。點選「立即重新連線」後生效，不需要 ADB 或使用情況存取。iPhone 可能同時調整官方轉向卡版面；這不是即時平移畫面。'),
        'values-ar': ('موضع السيارة في عدادات C11 · أفقي', 'موضع السيارة في عدادات C11 · رأسي', 'يعدل موضع السيارة المطلوب في خريطة العدادات اليمنى فقط ويحفظه بعد إعادة التشغيل. أعد توصيل CarPlay للتطبيق. لا يحتاج إلى ADB أو إذن الاستخدام. قد يغير iPhone تخطيط بطاقة الانعطاف أيضا؛ لا يحرك الصورة مباشرة.'),
        'values-it': ('Indicatore quadro C11 · orizzontale', 'Indicatore quadro C11 · verticale', 'Regola solo la posizione richiesta nella mappa destra del quadro e la conserva dopo il riavvio. Ricollega CarPlay per applicare. Non richiede ADB o accesso utilizzo. iPhone può anche spostare la scheda di svolta; non trasla i pixel in tempo reale.'),
        'values-es': ('Marcador del cuadro C11 · horizontal', 'Marcador del cuadro C11 · vertical', 'Ajusta solo la posición solicitada en el mapa derecho del cuadro y la conserva tras reiniciar. Reconecta CarPlay para aplicar. No necesita ADB ni acceso de uso. iPhone puede mover también la tarjeta de giro; no desplaza los píxeles en directo.'),
        'values-ru': ('Маркер приборной панели C11 · горизонталь', 'Маркер приборной панели C11 · вертикаль', 'Меняет только запрошенную позицию на правой карте приборной панели и сохраняет ее после перезапуска. Переподключите CarPlay для применения. ADB и доступ к статистике не нужны. iPhone может также переместить карточку поворота; это не прямой сдвиг изображения.'),
        'values-uk': ('Маркер панелі C11 · горизонталь', 'Маркер панелі C11 · вертикаль', 'Змінює лише запитану позицію на правій карті панелі та зберігає її після перезапуску. Перепідключіть CarPlay для застосування. ADB і доступ до статистики не потрібні. iPhone може також перемістити картку повороту; це не прямий зсув зображення.'),
        'values-ja': ('C11 メーター車両位置 · 左右', 'C11 メーター車両位置 · 上下', 'メーター右側地図の車両位置の要求だけを調整し、再起動後も保存します。CarPlay を再接続すると適用されます。ADB や使用状況へのアクセスは不要です。iPhone が公式案内カードも配置し直す場合があります。映像をリアルタイムに移動する機能ではありません。'),
    }
    for folder, values in translations.items():
        path = target/'common/src/main/res'/folder/'strings.xml'
        keys = ['settings_c11_marker_horizontal', 'settings_c11_marker_vertical', 'settings_c11_marker_description']
        xml = ''.join('    <string name="'+key+'">'+escape(value).replace("'", "\\'")+'</string>\n' for key, value in zip(keys, values))
        replace(path, '</resources>', xml+'</resources>')
