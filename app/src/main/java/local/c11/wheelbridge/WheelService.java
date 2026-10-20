package local.c11.wheelbridge;

import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.media.session.MediaController;
import android.media.session.MediaSessionManager;
import android.media.session.PlaybackState;
import android.os.Build;
import android.os.Bundle;
import android.os.SystemClock;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;
import android.view.KeyEvent;
import org.json.JSONObject;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public final class WheelService extends NotificationListenerService {
    private static final String TARGET = "com.shihab.diplay";
    private static final ArrayDeque<String> LOG = new ArrayDeque<>();
    static volatile boolean connected;
    private final WheelProtocol.Debounce debounce = new WheelProtocol.Debounce();
    private boolean registered;
    static synchronized void note(String message) {
        LOG.addLast(new SimpleDateFormat("HH:mm:ss", Locale.ROOT).format(new Date()) + " " + message);
        while (LOG.size() > 100) LOG.removeFirst();
    }
    static synchronized String report() {
        StringBuilder text = new StringBuilder("C11 方控桥接 " + BuildConfig.VERSION_NAME + "\n");
        text.append("Android ").append(Build.VERSION.RELEASE).append(" API ").append(Build.VERSION.SDK_INT).append('\n');
        text.append("品牌/型号 ").append(Build.MANUFACTURER).append('/').append(Build.MODEL).append('\n');
        text.append("监听状态 ").append(connected ? "已连接" : "未连接").append('\n');
        for (String line : LOG) text.append(line).append('\n');
        return text.toString();
    }
    static boolean enabled(Context context) {
        return context.getSharedPreferences("bridge", MODE_PRIVATE).getBoolean("enabled", false);
    }
    private final BroadcastReceiver receiver = new BroadcastReceiver() {
        @Override public void onReceive(Context context, Intent intent) {
            try { receive(intent); }
            catch (RuntimeException e) { note("忽略无效广播：" + e.getClass().getSimpleName()); }
        }
    };
    @Override public void onListenerConnected() {
        super.onListenerConnected();
        connected = true;
        if (!registered) {
            IntentFilter filter = new IntentFilter();
            for (String action : WheelProtocol.ACTIONS) filter.addAction(action);
            try {
                if (Build.VERSION.SDK_INT >= 33) registerReceiver(receiver, filter, Context.RECEIVER_EXPORTED);
                else registerReceiver(receiver, filter);
                registered = true;
                note("已注册方控广播；转发默认关闭");
            } catch (RuntimeException e) { note("广播注册失败：" + e.getClass().getSimpleName()); }
        }
    }
    @Override public void onListenerDisconnected() {
        connected = false;
        unregister();
        note("通知访问连接已断开");
        super.onListenerDisconnected();
    }
    @Override public void onDestroy() {
        connected = false;
        unregister();
        super.onDestroy();
    }
    private void unregister() {
        if (registered) {
            unregisterReceiver(receiver);
            registered = false;
        }
    }
    // Notification contents are deliberately not read or stored.
    @Override public void onNotificationPosted(StatusBarNotification ignored) { }
    @Override public void onNotificationRemoved(StatusBarNotification ignored) { }
    private static Object extra(Bundle extras, String key) {
        return extras == null ? null : extras.get(key);
    }
    private static Object first(Bundle extras, String one, String two) {
        Object value = extra(extras, one);
        return value != null ? value : extra(extras, two);
    }
    private static String jsonAction(String text) {
        try {
            JSONObject root = new JSONObject(text);
            if ("diplay".equals(root.optString("src"))) return null;
            String type = root.optString("type");
            if (!type.isEmpty() && !"music".equalsIgnoreCase(type)) return null;
            JSONObject data = root.optJSONObject("data");
            return data == null ? null : data.optString("action");
        } catch (Exception ignored) { return null; }
    }
    private void receive(Intent intent) {
        String action = intent.getAction();
        Bundle extras = intent.getExtras();
        WheelProtocol.Command command = null;
        if (WheelProtocol.isC11(action)) {
            Object type = extra(extras, "keyEventType"), value = extra(extras, "value");
            command = WheelProtocol.c11(type, value);
            note("C11 事件 type=" + safe(type) + " value=" + safe(value));
        } else if (WheelProtocol.isExtra(action)) {
            Object sw = first(extras, "ICU_MediaSwitch", "mediaSwitch");
            Object key = first(extras, "ICU_MediaKey", "mediaKey");
            command = WheelProtocol.extra(sw, key);
            note("ICU 事件 switch=" + safe(sw) + " key=" + safe(key));
        } else {
            Object payload = extra(extras, "receiver");
            String raw = null;
            boolean explicitPayload = payload != null;
            if (payload instanceof byte[]) {
                byte[] bytes = (byte[]) payload;
                if (bytes.length > 2) {
                    int length = (bytes[0] & 255) * 100 + (bytes[1] & 255);
                    if (length > 0 && length <= bytes.length - 2)
                        raw = jsonAction(new String(bytes, 2, length, StandardCharsets.UTF_8));
                }
            } else if (payload instanceof String) { raw = jsonAction((String) payload); }
            if (!explicitPayload) {
                Object value = extra(extras, "action");
                if (value instanceof String) {
                    explicitPayload = true;
                    String text = ((String) value).trim();
                    raw = text.startsWith("{") ? jsonAction(text) : text;
                }
            }
            command = explicitPayload ? WheelProtocol.text(raw) : WheelProtocol.action(action);
        }
        note("广播 " + action + " → " + (command == null ? "未匹配" : command));
        if (command == null || !enabled(this)) return;
        if (!debounce.accept(command, SystemClock.elapsedRealtime())) { note("重复事件已合并"); return; }
        forward(command);
    }
    private static String safe(Object value) {
        if (value == null) return "缺失";
        if (!(value instanceof String) && !(value instanceof Number)) return value.getClass().getSimpleName();
        String text = String.valueOf(value).replace('\n', ' ');
        return text.substring(0, Math.min(text.length(), 48)) + "(" + value.getClass().getSimpleName() + ")";
    }
    private void forward(WheelProtocol.Command command) {
        try {
            MediaSessionManager manager = (MediaSessionManager) getSystemService(MEDIA_SESSION_SERVICE);
            List<MediaController> matches = new ArrayList<>();
            for (MediaController controller : manager.getActiveSessions(new ComponentName(this, WheelService.class)))
                if (TARGET.equals(controller.getPackageName())) matches.add(controller);
            // Never select a different player's session or guess between multiple DiPlay sessions.
            if (matches.size() != 1) { note("未转发：DiPlay 活动媒体会话数量=" + matches.size()); return; }
            MediaController controller = matches.get(0);
            PlaybackState state = controller.getPlaybackState();
            long supported = state == null ? 0 : state.getActions();
            MediaController.TransportControls controls = controller.getTransportControls();
            if (command == WheelProtocol.Command.NEXT && (supported & PlaybackState.ACTION_SKIP_TO_NEXT) != 0)
                controls.skipToNext();
            else if (command == WheelProtocol.Command.PREVIOUS && (supported & PlaybackState.ACTION_SKIP_TO_PREVIOUS) != 0)
                controls.skipToPrevious();
            else if (command == WheelProtocol.Command.TOGGLE && state != null
                    && state.getState() == PlaybackState.STATE_PLAYING && (supported & PlaybackState.ACTION_PAUSE) != 0)
                controls.pause();
            else if (command == WheelProtocol.Command.TOGGLE && state != null
                    && state.getState() == PlaybackState.STATE_PAUSED && (supported & PlaybackState.ACTION_PLAY) != 0)
                controls.play();
            else {
                int code = command == WheelProtocol.Command.NEXT ? KeyEvent.KEYCODE_MEDIA_NEXT
                    : command == WheelProtocol.Command.PREVIOUS ? KeyEvent.KEYCODE_MEDIA_PREVIOUS
                    : KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE;
                boolean down = controller.dispatchMediaButtonEvent(new KeyEvent(KeyEvent.ACTION_DOWN, code));
                boolean up = controller.dispatchMediaButtonEvent(new KeyEvent(KeyEvent.ACTION_UP, code));
                note("已提交媒体按键 " + command + " accepted=" + down + "/" + up);
                return;
            }
            note("已提交媒体控制 " + command + "（需实车确认执行结果）");
        } catch (RuntimeException e) { note("转发失败：" + e.getClass().getSimpleName()); }
    }
}
