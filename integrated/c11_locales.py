"""Complete C11 settings in locales introduced by upstream 0.2.22."""
from xml.sax.saxutils import escape

KEYS = '''wheel wheel_description music_guard music_guard_description music_restore music_restore_description music_access music_access_unavailable cluster_display cluster_none cluster_description probe_title probe_description probe_confirm probe_disconnect probe_failed mic_source mic_default mic_recognition mic_plain mic_description'''.split()
TEXT = {
'ko': [
'C11 스티어링 휠 미디어 버튼 (실험적 기능)',
'기본값은 꺼짐입니다. CarPlay 연결 중 즉시 적용됩니다. 알림 접근이나 ADB는 필요하지 않습니다. 주차 후 테스트하고 한 번 눌러 두 번 동작하면 끄세요. 전달이 꺼져 있어도 수신 방송은 진단에 기록됩니다.',
'CarPlay 사용 중 차량 음악 일시 정지 (실험적 기능)',
'기본값은 꺼짐입니다. 아래의 알림 접근 권한이 필요합니다. CarPlay 사용 중 지원되는 NetEase, QQ Music, Kuwo 세션을 일시 정지하며 시스템 음량은 변경하지 않습니다. 지원되지 않는 플레이어는 동시에 재생될 수 있습니다. 즉시 적용됩니다.',
'연결 해제 후 이전 음악 재개',
'모니터링 시작 시 재생 중이었고 이 기능이 일시 정지한 세션이 아직 있을 때만 재개합니다. 통화가 우선입니다. CarPlay 사용 중 새로 시작한 음악은 정지 상태를 유지합니다.',
'알림 접근 설정 열기',
'시스템 알림 접근 설정을 직접 열어 이 앱을 허용하세요.',
'C11 계기판 디스플레이 (실험적 기능)',
'선택 안 함; 투사하지 않음',
'계기판임을 확인한 공개 1920×720 디스플레이만 선택하세요. 동승석 화면은 선택하지 마세요. 선택 후 CarPlay를 다시 연결하세요. 창은 오른쪽 720×720 영역에 유지됩니다. 후보가 없으면 진단을 내보내고 강제 접근하지 마세요.',
'화면 #%1$d 식별',
'먼저 주차하고 CarPlay를 연결 해제하세요. 오른쪽 위에 C11 번호가 4초간 표시됩니다. 동승석이 아닌 계기판에서 확인한 경우에만 승인하세요. 확실하지 않으면 취소하세요. 식별 중 지도는 표시되지 않습니다.',
'표시가 계기판에 나타났음',
'화면 식별 전에 CarPlay를 연결 해제하세요.',
'표시를 띄울 수 없습니다. 계기판 투사를 꺼 두세요.',
'C11 통화 마이크 소스 (실험적 기능)',
'업스트림 기본값',
'음성 인식 소스',
'일반 마이크 소스',
'다음 통화부터 적용됩니다. 변경 전에 통화를 종료하세요. 녹음이 무음이면 음성 인식을 시도하고 실패하면 기본값으로 복원하세요. 앱 녹음기만 변경하며 시스템 라우팅이나 음량은 변경하지 않습니다. 실차 미검증입니다.'
],
'tr': [
'C11 direksiyon medya tuşları (deneysel)',
'Varsayılan olarak kapalıdır. CarPlay sırasında hemen uygulanır; bildirim erişimi veya ADB gerekmez. Park halinde deneyin. Tek basış iki kez işlenirse kapatın. İletim kapalıyken de alınan yayınlar tanılamaya kaydedilir.',
'CarPlay sırasında araç müziğini duraklat (deneysel)',
'Varsayılan olarak kapalıdır. Aşağıdaki bildirim erişimi gerekir. CarPlay sırasında desteklenen NetEase, QQ Music ve Kuwo oturumlarını duraklatır; sistem sesini değiştirmez. Desteklenmeyen oynatıcılar aynı anda çalabilir. Hemen uygulanır.',
'Bağlantı kesilince önceki müziği sürdür',
'Yalnızca izleme başladığında çalan, bu özellik tarafından duraklatılan ve hâlâ mevcut olan oturumu sürdürür. Aramalar önceliklidir. CarPlay sırasında başlatılan müzik duraklatılmış kalır.',
'Bildirim erişimini aç',
'Sistemin bildirim erişimi ayarlarını elle açıp bu uygulamaya izin verin.',
'C11 gösterge ekranı (deneysel)',
'Seçilmedi; yansıtma yapma',
'Yalnızca gösterge paneli olduğu doğrulanan herkese açık 1920×720 ekranı seçin; yolcu ekranını seçmeyin. Seçimden sonra CarPlay bağlantısını yeniden kurun. Pencere sağdaki 720×720 alanda kalır. Aday yoksa tanılamayı dışa aktarın; erişimi zorlamayın.',
'#%1$d ekranını tanımla',
'Önce park edin ve CarPlay bağlantısını kesin. Sağ üstte dört saniye küçük bir C11 numarası görünür. Yalnızca gösterge panelinde gördüyseniz onaylayın; yolcu ekranında değil. Emin değilseniz iptal edin. Tanımlama sırasında harita yansıtılmaz.',
'İşaret gösterge panelindeydi',
'Ekranı tanımlamadan önce CarPlay bağlantısını kesin.',
'İşaret gösterilemedi. Gösterge yansıtmasını kapalı tutun.',
'C11 arama mikrofon kaynağı (deneysel)',
'Üst kaynak varsayılanı',
'Ses tanıma kaynağı',
'Normal mikrofon kaynağı',
'Yalnızca sonraki aramada uygulanır. Değiştirmeden önce aramayı bitirin. Kayıt sessizse ses tanımayı deneyin; işe yaramazsa varsayılana dönün. Yalnızca uygulamanın kaydedicisini değiştirir; sistem yönlendirmesini veya sesini değiştirmez. Araçta doğrulanmadı.'
]}


def apply(target):
    for locale, values in TEXT.items():
        assert len(KEYS) == len(values)
        folder = target/'common/src/main/res'/f'values-{locale}'
        if not folder.is_dir():
            continue
        rows = ['<resources>']
        for key, value in zip(KEYS, values):
            rows.append('    <string name="settings_c11_' + key + '">' + escape(value).replace("'", "\\'") + '</string>')
        rows.append('</resources>')
        (folder/'c11_strings.xml').write_text('\n'.join(rows) + '\n')
