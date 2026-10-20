package local.c11.wheelbridge;
public final class WheelProtocolTest {
    static int checks;
    static void check(boolean value) { checks++; if (!value) throw new AssertionError("check " + checks); }
    public static void main(String[] args) {
        check(WheelProtocol.c11("steeringWheel", "1") == WheelProtocol.Command.PREVIOUS);
        check(WheelProtocol.c11("steeringWheel", 2) == WheelProtocol.Command.NEXT);
        check(WheelProtocol.c11("steeringWheel", "3") == WheelProtocol.Command.TOGGLE);
        check(WheelProtocol.c11("backRow", "1") == null);
        check(WheelProtocol.c11("voice", "3") == null);
        check(WheelProtocol.c11("steeringWheel", "999") == null);
        check(WheelProtocol.c11("steeringWheel", 4294967297L) == null);
        check(WheelProtocol.c11("steeringWheel", null) == null);
        check(WheelProtocol.c11("steeringWheel", 1.5) == null);
        check(WheelProtocol.extra(1, 0) == WheelProtocol.Command.PREVIOUS);
        check(WheelProtocol.extra("2", null) == WheelProtocol.Command.NEXT);
        check(WheelProtocol.extra(null, "1") == WheelProtocol.Command.TOGGLE);
        check(WheelProtocol.extra(null, null) == null);
        check(WheelProtocol.text("preOne") == WheelProtocol.Command.PREVIOUS);
        check(WheelProtocol.text("nextOne") == WheelProtocol.Command.NEXT);
        check(WheelProtocol.text("play_pause") == WheelProtocol.Command.TOGGLE);
        check(WheelProtocol.text("play") == null);
        check(WheelProtocol.text("pause") == null);
        check(WheelProtocol.text("stop") == null);
        check(WheelProtocol.text("volumeup") == null);
        check(WheelProtocol.action("com.leapmotor.customkey.music.next") == WheelProtocol.Command.NEXT);
        check(WheelProtocol.action("unknown.next") == null);
        check(WheelProtocol.action("com.leapmotor.command.fmradio") == null);
        check(WheelProtocol.action(null) == null);
        check(WheelProtocol.isExtra("com.leapmotor.ICU2MMICtrl"));
        check(WheelProtocol.isC11("com.leapmotor.action.METER.CTRL"));
        java.util.Set<String> unique = new java.util.HashSet<>();
        for (String action : WheelProtocol.ACTIONS) check(unique.add(action));
        check(unique.contains("com.leapmotor.ICU2MMICtrl"));
        check(unique.contains("com.leapmotor.customkey.music.pauseplay"));
        WheelProtocol.Debounce d = new WheelProtocol.Debounce();
        check(d.accept(WheelProtocol.Command.NEXT, 1000));
        check(!d.accept(WheelProtocol.Command.NEXT, 1100));
        check(d.accept(WheelProtocol.Command.NEXT, 1250));
        check(d.accept(WheelProtocol.Command.PREVIOUS, 1251));
        check(d.accept(WheelProtocol.Command.TOGGLE, 1252));
        check(!d.accept(WheelProtocol.Command.TOGGLE, 1253));
        System.out.println("Passed " + checks + " protocol/duplicate/invalid-input checks.");
    }
}
