if __name__ == "__main__":
    import socket, sys, time
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    # do your CLI-only work heredeadline = time.time() + 30
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=1):
            print("ready")
            sys.exit(0)
    except Exception:
        time.sleep(0.5)
print("timeout")
sys.exit(1)




