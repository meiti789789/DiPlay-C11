package local.c11.wheelbridge;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.provider.Settings;
import android.service.notification.NotificationListenerService;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Switch;
import android.widget.TextView;

public final class MainActivity extends Activity {
    private final Handler handler = new Handler();
    private TextView report;
    private final Runnable refresh = new Runnable() {
        @Override public void run() { report.setText(WheelService.report()); handler.postDelayed(this, 1000); }
    };
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        int pad = (int) (16 * getResources().getDisplayMetrics().density);
        layout.setPadding(pad, pad, pad, pad);
        TextView intro = new TextView(this);
        intro.setText("2023 C11 方控桥接 · 实车验证版\n独立于 DiPlay 安装。先保持转发关闭，连接 CarPlay 后依次按上一首、下一首、暂停，查看下方记录。只处理媒体键。\n需要手动允许“通知使用权”以连接 DiPlay 媒体会话；本应用不读取通知内容、不联网。若原车方控或其他桥接已经生效，请关闭本应用转发，避免重复。系统 OTA 与未来 DiPlay 接口兼容性尚未实车验证。");
        layout.addView(intro);
        Button permission = new Button(this);
        permission.setText("打开通知使用权设置");
        permission.setOnClickListener(v -> {
            try { startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)); }
            catch (RuntimeException e) { WheelService.note("车机未提供通知使用权设置入口"); }
        });
        layout.addView(permission);
        Button reconnect = new Button(this);
        reconnect.setText("重新请求连接（已授权后）");
        reconnect.setOnClickListener(v -> {
            try { NotificationListenerService.requestRebind(new ComponentName(this, WheelService.class)); }
            catch (RuntimeException e) { WheelService.note("重新连接失败：" + e.getClass().getSimpleName()); }
        });
        layout.addView(reconnect);
        Switch enable = new Switch(this);
        enable.setText("启用方控转发（仅在收到事件后开启测试）");
        enable.setChecked(WheelService.enabled(this));
        enable.setOnCheckedChangeListener((button, checked) -> {
            getSharedPreferences("bridge", MODE_PRIVATE).edit().putBoolean("enabled", checked).apply();
            WheelService.note(checked ? "用户开启转发" : "用户关闭转发");
        });
        layout.addView(enable);
        Button share = new Button(this);
        share.setText("分享诊断记录");
        share.setOnClickListener(v -> {
            Intent intent = new Intent(Intent.ACTION_SEND).setType("text/plain")
                .putExtra(Intent.EXTRA_TEXT, WheelService.report());
            try { startActivity(Intent.createChooser(intent, "分享方控诊断")); }
            catch (RuntimeException e) { WheelService.note("没有可分享的应用，可拍摄屏幕记录"); }
        });
        layout.addView(share);
        ScrollView scroll = new ScrollView(this);
        report = new TextView(this);
        report.setTextIsSelectable(true);
        scroll.addView(report);
        layout.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(layout);
    }
    @Override protected void onResume() { super.onResume(); handler.post(refresh); }
    @Override protected void onPause() { handler.removeCallbacks(refresh); super.onPause(); }
}
