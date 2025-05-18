from time import sleep


def test_serial_pair():
    with run_virtual_serial_pair() as (proc, w, r):
        print(f"virt_ser_pid={proc.pid}\nwriter_port={w}\nreader_port={r}")
        for line in proc.stdout:
            print("socat: ", line)


def test_serial_writer_native(w):
    from tests.helper.serial_writer import serial_write
    serial_write(w, interval=0.001)


def test_serial_writer(w):
    with run_serial_writer(w) as w_proc:
        print(f"writer_pid={w_proc.pid}")
        while True:
            sleep(1)


def test_together():
    with run_virtual_serial_pair() as (proc, w, r):
        print(f"virt_ser_pid={proc.pid}\nwriter_port={w}\nreader_port={r}")
        with run_serial_writer(w) as w_proc:
            print(f"writer_pid={w_proc.pid}")
            while True:
                sleep(1)


if __name__ == "__main__":
    from time import sleep
    from tests.helper.subprocess_managers import (
        run_virtual_serial_pair,
        run_serial_writer,
    )
    import sys

    print(sys.argv)
    case = sys.argv[1]

    match case:
        case "1":
            test_serial_writer_native(sys.argv[2])
            # test_serial_writer(sys.argv[2])
        case "2":
            test_serial_pair()
        case "3":
            test_together()
        case default:
            print("no arg")
