"""Apply bounded C11 changes to a checked-out upstream release; fail if anchors change."""
from pathlib import Path
import argparse,re,shutil,json
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parent

def replace(path, old, new, count=1):
    text=path.read_text()
    if text.count(old)!=count:raise RuntimeError(f'Upstream anchor changed: {path.name}: {old[:70]}')
    path.write_text(text.replace(old,new))

def prepare(target, version, revision):
    if not re.fullmatch(r'\d+\.\d+\.\d+',version) or revision<1 or revision>999:
        raise ValueError('Invalid upstream version or C11 revision')
    for path in (ROOT/'overlay').rglob('*'):
        if path.is_file():
            out=target/path.relative_to(ROOT/'overlay');out.parent.mkdir(parents=True,exist_ok=True);shutil.copy(path,out)
    java=target/'common/src/main/java/com/shilapi/xcertplay'
    replace(java/'CarPlayHostActivity.kt','        CarPlayMediaKeys.attach(this, next)',
            '        CarPlayMediaKeys.attach(this, next)\n        C11WheelKeys.attach(this, next)')
    replace(java/'CarPlayHostActivity.kt','        CarPlayMediaKeys.detach(oldController)',
            '        C11WheelKeys.detach(oldController)\n        CarPlayMediaKeys.detach(oldController)',2)
    replace(java/'CarPlayMediaKeys.kt','    private fun send(index: Int, source: String) {',
            '    private fun send(index: Int, source: String) {\n        if (!C11WheelKeys.claim(index)) return')
    replace(java/'CarPlayMediaKeys.kt','    internal fun onExternalMediaKey(index: Int)',
            '    internal fun onC11MediaKey(index: Int) = send(index, "c11-wheel")\n\n    internal fun onExternalMediaKey(index: Int)')
    replace(java/'DiPlayActivity.kt','    private fun wheelKeysSettings(card: LinearLayout) {', '''    private fun wheelKeysSettings(card: LinearLayout) {
        toggle(card, getString(R.string.settings_c11_wheel), getString(R.string.settings_c11_wheel_description),
            C11WheelKeys.enabled(this)) { C11WheelKeys.setEnabled(this, it) }''')
    translations={
        'values':('C11 steering-wheel media keys (experimental)','Off by default. Applies immediately during CarPlay; no notification access or ADB needed. Test while parked. If one press acts twice, turn this off. Diagnostics record received broadcasts even while forwarding is off.'),
        'values-zh-rCN':('C11 方控（实验性）','默认关闭。CarPlay 会话内立即生效，无需通知使用权或 ADB。停车测试；重复切歌时关闭。转发关闭时也会记录收到的广播，请在诊断报告中查看。'),
        'values-zh-rTW':('C11 方向盤按鍵（實驗性）','預設關閉。CarPlay 連線期間立即生效，無需通知存取權或 ADB。請停車測試；重複切歌時關閉。關閉轉發時仍會記錄收到的廣播，請查看診斷報告。'),
        'values-ar':('أزرار المقود C11 (تجريبي)','معطّل افتراضيًا. يسري فورًا أثناء CarPlay، دون إذن الإشعارات أو ADB. اختبر أثناء الوقوف وأوقفه عند تكرار الأوامر. تُسجّل البثوث في التشخيص حتى عند تعطيل التمرير.'),
        'values-it':('Tasti al volante C11 (sperimentale)','Disattivati per impostazione predefinita. Effetto immediato durante CarPlay, senza accesso alle notifiche o ADB. Provare da fermi; disattivare in caso di comandi duplicati. Le trasmissioni ricevute sono registrate nella diagnostica anche senza inoltro.'),
        'values-es':('Botones del volante C11 (experimental)','Desactivados de forma predeterminada. Se aplican durante CarPlay sin acceso a notificaciones ni ADB. Prueba con el vehículo estacionado; desactiva si hay acciones duplicadas. Los eventos recibidos quedan en el diagnóstico aunque el reenvío esté desactivado.'),
        'values-ja':('C11 ステアリングキー（実験的機能）','初期設定はオフです。CarPlay 接続中に即時反映され、通知へのアクセスや ADB は不要です。停車中にテストし、操作が重複したらオフにしてください。転送がオフでも受信イベントは診断に記録されます。'),
        'values-ru':('Кнопки руля C11 (экспериментально)','По умолчанию выключено. Действует сразу во время CarPlay без доступа к уведомлениям и ADB. Проверяйте на стоянке; при двойном срабатывании выключите. Полученные события записываются в диагностику и без передачи.'),
        'values-uk':('Кнопки керма C11 (експериментально)','Типово вимкнено. Діє відразу під час CarPlay без доступу до сповіщень або ADB. Перевіряйте на стоянці; у разі подвійного спрацювання вимкніть. Отримані події записуються в діагностику навіть без передавання.'),
    }
    for folder,(title,description) in translations.items():
        path=target/'common/src/main/res'/folder/'strings.xml'
        def value(text):return escape(text).replace("'","\\'")
        replace(path,'</resources>',f'    <string name="settings_c11_wheel">{value(title)}</string>\n    <string name="settings_c11_wheel_description">{value(description)}</string>\n</resources>')
    mobile=target/'mobile/build.gradle.kts'
    replace(mobile,'applicationId = "com.shihab.diplay"','applicationId = "com.c11.diplay"')
    text=mobile.read_text();match=re.search(r'versionCode = (\d+)',text)
    if not match:raise RuntimeError('Missing upstream versionCode')
    text=text.replace(match[0],f'versionCode = {int(match[1])*1000+revision}')
    text,n=re.subn(r'versionName = "[^"]+"',f'versionName = "{version}-c11.{revision}"',text,count=1)
    if n!=1:raise RuntimeError('Missing versionName')
    mobile.write_text(text)
    for path in list((target/'mobile/src/main/res').glob('values*/strings.xml'))+list((target/'common/src/main/res').glob('values*/strings.xml')):
        s=path.read_text();s=re.sub(r'(<string name="app_name">)[^<]*(</string>)',r'\g<1>DiPlay C11\2',s);path.write_text(s)
    replace(java/'update/UpdateClient.kt','https://api.github.com/repos/shihabal3amri/DiPlay/releases?per_page=3',
            'https://api.github.com/repos/meiti789789/DiPlay-C11/releases?per_page=30')
    replace(java/'update/UpdateCatalog.kt','            if (release.optBoolean("draft")) continue',
            '''            if (release.optBoolean("draft")) continue
            // Historical companion/combo releases carry incompatible APKs; never offer those.
            val tag = release.optString("tag_name")
            if (tag.startsWith("bridge-") || tag.startsWith("c11-upstream-")) continue''')
    replace(java/'update/UpdateVersion.kt','        return target.third > current.third', '''        if (target.third != current.third) return target.third > current.third
        fun revision(value: String): Int = Regex("-c11\\\\.(\\\\d+)").find(value)?.groupValues?.get(1)?.toIntOrNull() ?: 0
        return revision(remote) > revision(installed)''')
    # Preserve all upstream tests. Add only new scenario coverage and rendered settings evidence.
    ui=target/'common/src/test/java/com/shilapi/xcertplay/AdaptiveSettingsUiTest.kt'
    replace(ui,'    private fun openSettings(): DiPlayActivity', '''    @Test @org.robolectric.annotation.GraphicsMode(org.robolectric.annotation.GraphicsMode.Mode.NATIVE)
    @Config(sdk = [29], qualifiers = "zh-rCN-w320dp-h600dp")
    fun c11SettingsCompactLargeFont() = captureC11("compact-zh")
    @Test @org.robolectric.annotation.GraphicsMode(org.robolectric.annotation.GraphicsMode.Mode.NATIVE)
    @Config(sdk = [29], qualifiers = "en-w1000dp-h700dp")
    fun c11SettingsExpandedLargeFont() = captureC11("expanded-en")
    @Test @org.robolectric.annotation.GraphicsMode(org.robolectric.annotation.GraphicsMode.Mode.NATIVE)
    @Config(sdk = [29], qualifiers = "ar-ldrtl-w320dp-h600dp")
    fun c11SettingsArabicLargeFont() = captureC11("compact-ar")
    private fun captureC11(name: String) {
        RuntimeEnvironment.setFontScale(1.3f)
        val screen = openSettings()
        ReflectionHelpers.setField(screen, "settingsCategory", SettingsCategory.VEHICLE)
        ReflectionHelpers.callInstanceMethod<Unit>(screen, "render")
        layoutRoot(screen)
        val title = texts(screen).first { it.text == screen.getString(R.string.settings_c11_wheel) }
        title.requestRectangleOnScreen(Rect(0, 0, title.width, title.height), true)
        layoutRoot(screen)
        assertTrue("C11 control must be visible", title.getGlobalVisibleRect(Rect()))
        val root = screen.findViewById<ViewGroup>(android.R.id.content).getChildAt(0)
        val bitmap = Bitmap.createBitmap(root.width, root.height, Bitmap.Config.ARGB_8888)
        try {
            root.draw(Canvas(bitmap))
            val output = Paths.get("build/reports/c11-ui/$name.png")
            Files.createDirectories(output.parent)
            Files.newOutputStream(output).use { assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG, 100, it)) }
        } finally { bitmap.recycle() }
    }

    private fun openSettings(): DiPlayActivity''')
    (target/'C11-ADAPTATION.md').write_text((ROOT/'说明.md').read_text())
    print(f'Prepared integrated C11 {version}-c11.{revision}; source anchors checked, keys excluded.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('upstream',type=Path);p.add_argument('--version',required=True);p.add_argument('--revision',type=int,required=True);args=p.parse_args()
    prepare(args.upstream,args.version,args.revision)
