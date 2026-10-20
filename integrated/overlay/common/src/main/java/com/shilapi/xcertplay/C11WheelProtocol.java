package com.shilapi.xcertplay;

import java.util.Locale;

/** No volume, voice, gear or vehicle-control commands. */
final class C11WheelProtocol {
    enum Command { PREVIOUS, NEXT, TOGGLE }
    static final String[] ACTIONS = {
        "com.leapmotor.action.METER.CTRL", "com.leapmotor.action.VOICE.CTRL",
        "com.leapmotor.ICU2MMICtrl", "com.leapmotor.customkey.music.pauseplay",
        "car.meter.music.BROADCAST", "car.hmi.music.BROADCAST",
        "com.leapmotor.command.music", "com.leapmotor.command.multimedia",
        "com.leapmotor.command.media", "com.leapmotor.command.playpause",
        "com.leapmotor.command.next", "com.leapmotor.command.previous",
        "com.leapmotor.command.key", "com.leapmotor.command.mediaKey",
        "com.leapmotor.multimedia.mediaKey", "com.leapmotor.multimedia.MediaKey",
        "com.leapmotor.media.keyevent", "com.leapmotor.media.KEY_EVENT",
        "com.leapmotor.audio.key", "com.leapmotor.audio.KEY_EVENT",
        "com.leapmotor.audiocenter.mediaKey", "com.leapmotor.vehicle.keyevent",
        "com.leapmotor.vehicle.mediaKey", "car.hmi.media.KEY_EVENT",
        "car.hmi.keyevent", "car.media.keyevent", "car.media.next", "car.media.previous",
        "com.leapmotor.ICUMainCtrl", "com.leapmotor.ICUCtrl",
        "com.leapmotor.customkey.media.next", "com.leapmotor.customkey.media.prev",
        "com.leapmotor.customkey.media.pauseplay", "com.leapmotor.customkey.music.next",
        "com.leapmotor.customkey.music.prev"
    };
    static boolean isC11(String action) {
        return "com.leapmotor.action.METER.CTRL".equals(action)
            || "com.leapmotor.action.VOICE.CTRL".equals(action);
    }
    static boolean isExtra(String action) {
        return "com.leapmotor.ICU2MMICtrl".equals(action)
            || "com.leapmotor.customkey.music.pauseplay".equals(action);
    }
    static Command c11(Object type, Object value) {
        if (!"steeringWheel".equals(type)) return null;
        Integer number = number(value);
        if (number == null) return null;
        switch (number) {
            case 1: return Command.PREVIOUS;
            case 2: return Command.NEXT;
            case 3: return Command.TOGGLE;
            default: return null;
        }
    }
    static Integer number(Object value) {
        if (value instanceof Integer || value instanceof Short || value instanceof Byte)
            return ((Number) value).intValue();
        if (!(value instanceof String)) return null;
        try { return Integer.valueOf(((String) value).trim()); }
        catch (NumberFormatException e) { return null; }
    }
    static Command extra(Object mediaSwitch, Object mediaKey) {
        if (Integer.valueOf(1).equals(number(mediaKey))) return Command.TOGGLE;
        Integer value = number(mediaSwitch);
        if (Integer.valueOf(1).equals(value)) return Command.PREVIOUS;
        if (Integer.valueOf(2).equals(value)) return Command.NEXT;
        return null;
    }
    static Command text(String value) {
        if (value == null) return null;
        switch (value.trim().toLowerCase(Locale.ROOT)) {
            case "next": case "nextone": case "nexttrack": return Command.NEXT;
            case "prev": case "preone": case "previous": case "previoustrack":
                return Command.PREVIOUS;
            case "playpause": case "pauseplay": case "toggleplay":
            case "toggleplaypause": case "play_pause": return Command.TOGGLE;
            default: return null;
        }
    }
    static Command action(String value) {
        if (value == null) return null;
        // Only exact published button actions; never arbitrary suffixes or play/pause broadcasts.
        switch (value) {
            case "com.leapmotor.command.next": case "car.media.next":
            case "com.leapmotor.customkey.media.next":
            case "com.leapmotor.customkey.music.next": return Command.NEXT;
            case "com.leapmotor.command.previous": case "car.media.previous":
            case "com.leapmotor.customkey.media.prev":
            case "com.leapmotor.customkey.music.prev": return Command.PREVIOUS;
            case "com.leapmotor.command.playpause":
            case "com.leapmotor.customkey.media.pauseplay": return Command.TOGGLE;
            default: return null;
        }
    }
    static final class Debounce {
        private Command last;
        private long time;
        boolean accept(Command command, long now) {
            if (command == last && now - time >= 0 && now - time < 250) return false;
            last = command;
            time = now;
            return true;
        }
    }
}
