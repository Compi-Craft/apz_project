print("Starting run.py")
from app import app, port

if __name__ == '__main__':
    app.run(host = "0.0.0.0", port = port, debug=True)
