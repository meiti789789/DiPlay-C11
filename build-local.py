#!/usr/bin/env python3
"""Build the standalone companion locally. Never connects to a device or invokes ADB."""
from pathlib import Path
import os, subprocess
project = Path(__file__).resolve().parent
tools = project.parent / "DiPlay-build-tools"
jdks = sorted(path for path in tools.glob("jdk-*") if (path / "bin/java").is_file())
if not jdks:
    raise SystemExit("Missing local JDK: finish downloading the verified toolchain first.")
env = os.environ.copy()
env["JAVA_HOME"] = str(jdks[-1])
env["PATH"] = str(jdks[-1] / "bin") + os.pathsep + env.get("PATH", "")
env["ANDROID_HOME"] = str(tools / "android-sdk")
env["GRADLE_USER_HOME"] = str(tools / "gradle-cache")
classes = project / "build/protocol-tests"
classes.mkdir(parents=True, exist_ok=True)
subprocess.run([str(jdks[-1] / "bin/javac"), "-d", str(classes),
    str(project / "app/src/main/java/local/c11/wheelbridge/WheelProtocol.java"),
    str(project / "tests/WheelProtocolTest.java")], check=True, env=env)
subprocess.run([str(jdks[-1] / "bin/java"), "-cp", str(classes),
    "local.c11.wheelbridge.WheelProtocolTest"], check=True, env=env)
sdkmanager = tools / "android-sdk/cmdline-tools/latest/bin/sdkmanager"
if not ((tools / "android-sdk/platforms/android-35/android.jar").is_file()
        and (tools / "android-sdk/build-tools/34.0.0/aapt").is_file()):
    subprocess.run([str(sdkmanager), "--sdk_root=" + env["ANDROID_HOME"],
        "platforms;android-35", "build-tools;34.0.0"], input="y\n" * 100,
        text=True, check=True, env=env)

gradle = tools / "gradle-download/gradle-8.9/bin/gradle"
subprocess.run([str(gradle), "--no-daemon", "--console=plain", ":app:lintDebug", ":app:assembleDebug"],
    check=True, cwd=project, env=env)
print("Built:", project / "app/build/outputs/apk/debug/app-debug.apk")
