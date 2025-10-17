import socket, sys, time

host, port = sys.argv[1], int(sys.argv[2])
deadline = time.time() + 30
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=1):
            print("ready")
            sys.exit(0)
    except Exception:
        time.sleep(0.5)
print("timeout")
sys.exit(1)
