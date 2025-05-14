import sys
import time
from serial import Serial


port = sys.argv[1]
interval = float(sys.argv[2]) if len(sys.argv) > 2 else 0.1

with Serial(port, 9600) as serial:
    while True:
        data = b"\x59\x59\x12\x03\x00\x00\x00\x00\xc7"
        serial.write(data)
        time.sleep(interval)
