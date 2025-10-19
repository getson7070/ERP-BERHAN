if __name__ == "__main__":
    import socket, sys, time
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    # do your CLI-only work here
    deadline = time.time() + 30

