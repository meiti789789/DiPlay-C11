from xml.sax.saxutils import escape

def apply(target, replace):
    copy = {
        'values': ('Identify screen #%1$d', 'Park and disconnect CarPlay first. A small C11 number appears in the bottom-right corner for four seconds. Confirm only if you saw it on the instrument panel, never the passenger screen. If unsure, cancel. No map is projected during identification.', 'Marker was on the instrument panel', 'Disconnect CarPlay before identifying a display.', 'Could not show the marker. Keep instrument projection off.'),
        'values-zh-rCN': ('识别屏幕 #%1$d', '请停车并先断开 CarPlay。所选屏幕右下角短暂显示 C11 编号，4 秒后消失。只有亲眼确认标记在仪表上才能确认；副驾屏或看不清时请取消。识别时不投地图。', '标记在仪表上，确认', '请先断开 CarPlay，再识别屏幕。', '无法显示标记，请保持仪表投屏关闭。'),
        'values-zh-rTW': ('辨認螢幕 #%1$d', '請停車並先中斷 CarPlay。所選螢幕右下角顯示 C11 編號，4 秒後消失。只有確認標記在儀表上才能確認；副駕駛螢幕或不確定時請取消。辨認時不投影地圖。', '標記在儀表上，確認', '請先中斷 CarPlay，再辨認螢幕。', '無法顯示標記，請保持儀表投影關閉。'),
        'values-ar': ('تحديد الشاشة #%1$d', 'أوقف السيارة وافصل CarPlay. تظهر علامة C11 أسفل اليمين لأربع ثوان. أكد فقط إن رأيتها على العدادات، وليس شاشة الراكب. ألغ عند الشك. لا تعرض الخريطة أثناء التحديد.', 'العلامة على العدادات؛ تأكيد', 'افصل CarPlay قبل تحديد الشاشة.', 'تعذر إظهار العلامة. اترك عرض العدادات معطلاً.'),
        'values-it': ('Identifica schermo #%1$d', 'Parcheggiare e scollegare CarPlay. Un numero C11 appare in basso a destra per quattro secondi. Confermare solo sul quadro strumenti, mai sul passeggero. Nel dubbio annullare. Nessuna mappa durante questa prova.', 'Segno sul quadro strumenti; conferma', 'Scollegare CarPlay prima della prova.', 'Impossibile mostrare il segno. Tenere la proiezione disattivata.'),
        'values-es': ('Identificar pantalla #%1$d', 'Estaciona y desconecta CarPlay. Aparece un número C11 abajo a la derecha durante cuatro segundos. Confirma solo si está en el cuadro de instrumentos, nunca en la pantalla del pasajero. Si dudas, cancela. No se proyecta un mapa.', 'Marca en los instrumentos; confirmar', 'Desconecta CarPlay antes de identificar.', 'No se pudo mostrar la marca. Mantén la proyección desactivada.'),
        'values-ja': ('画面 #%1$d を識別', '停車し CarPlay を切断してください。右下に C11 番号を4秒間表示します。メーターで確認できた場合のみ確定し、助手席や不明な場合はキャンセルしてください。識別中は地図を投影しません。', 'メーター上の表示を確認', '画面識別の前に CarPlay を切断してください。', '番号を表示できません。メーター投影はオフのままにしてください。'),
        'values-ru': ('Определить экран #%1$d', 'Припаркуйтесь и отключите CarPlay. Внизу справа на четыре секунды появится номер C11. Подтвердите только на приборной панели, не на экране пассажира. При сомнении отмените. Карта не выводится.', 'Метка на приборах; подтвердить', 'Отключите CarPlay перед проверкой экрана.', 'Метка недоступна. Оставьте проекцию выключенной.'),
        'values-uk': ('Визначити екран #%1$d', 'Зупиніться та відключіть CarPlay. Унизу праворуч на чотири секунди з’явиться номер C11. Підтвердіть лише на приладах, не на екрані пасажира. Якщо сумніваєтеся, скасуйте. Карта не відображається.', 'Позначка на приладах; підтвердити', 'Відключіть CarPlay перед перевіркою екрана.', 'Позначка недоступна. Залиште проєкцію вимкненою.'),
    }
    keys=['settings_c11_probe_title','settings_c11_probe_description','settings_c11_probe_confirm','settings_c11_probe_disconnect','settings_c11_probe_failed']
    for locale, values in copy.items():
        entries=''.join('    <string name="'+k+'">'+escape(v).replace("'", "\\'")+'</string>\n' for k,v in zip(keys,values))
        replace(target/'common/src/main/res'/locale/'strings.xml','</resources>',entries+'</resources>')
