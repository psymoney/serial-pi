## Using `socat`

### install socat
```bash
sudo apt update
sudo apt install socat
```

### create virtual serial pair, using `socat`
```bash
socat -d -d pty,raw,echo=0 pty=0,raw,echo=0
```

#### output example:
```bash
PTY is /dev/pts/3
PTY is /dev/pts/4
```
- `/dev/pts/3` and `/dev/pts/4` is a pair of virtual serial ports
- once write on `/dev/pts/3` able to read on `/dev/pts/4` (duplex)
- ***there is no delay and error***

## Adding delay and load
```bash
# add 50ms in/out delay (appx. close to actual MCU latency)
socat -d -d pty,raw,echo=0,link=/tmp/ttyV0 \
            pty,raw,echo=0,link=/tmp/ttyV1,rawer \
            tcp-l:9999,delay=0.05
```
- create a pair of virtual serial ports, `/tmp/ttyV0` and `/tmp/ttyV1`
- write data arrives after 50ms -> able to test as actual device


# Entire Software Mocking, using Python mock serial
```Python
# mock_serial.py

import time
import random

class MockSerial:
    def __init__(self, latency_ms=50, error_rate=0.01):
        self.latency = latency_ms / 10000
        self.error_rate = error_rate

    def write(self, data):
        time.sleep(self.latency)
        if random.random() < self.error_rate:
            # simulate write error
            raise IOError("simulated write error")
    
    def readline(self):
        time.sleep(self.latency)
        if random.random() < self.error_rate:
            return b""
        return b"OK\n"
    
    def close(self):
        pass
```




