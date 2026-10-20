from pathlib import Path
import subprocess
root = Path(__file__).resolve().parents[1]
classes = root / 'build/protocol-tests'
classes.mkdir(parents=True, exist_ok=True)
subprocess.run(['javac', '-d', str(classes), str(root/'app/src/main/java/local/c11/wheelbridge/WheelProtocol.java'), str(root/'tests/WheelProtocolTest.java')], check=True)
subprocess.run(['java', '-cp', str(classes), 'local.c11.wheelbridge.WheelProtocolTest'], check=True)
