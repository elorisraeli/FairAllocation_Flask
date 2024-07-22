from flask_files import app
import socket

def find_open_port(start_port, end_port):
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('0.0.0.0', port)) != 0:
                return port
    raise Exception("No available ports found in the specified range.")

start_port = 2577
end_port = 2599

try:
    open_port = find_open_port(start_port, end_port)
    app.run(debug=True, host="0.0.0.0", port=open_port)
    print(f"Running on port {open_port}")
except Exception as e:
    print(str(e))
