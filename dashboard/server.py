from flask import Flask, render_template
from flask_socketio import SocketIO
from influxdb import InfluxDBClient
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# InfluxDB
client = InfluxDBClient(host="localhost", port=8086)
client.switch_database("rasa_slices")


def fetch_data():
    query = "SELECT * FROM slice_sim_result ORDER BY time DESC LIMIT 20"
    result = client.query(query)

    data = []
    for point in result.get_points():
        data.append({
            "name": point.get("slice_name"),
            "load": point.get("load_ratio"),
            "success": point.get("success"),
            "bandwidth": point.get("used_bandwidth"),
            "time":      point.get("time"), 
        })
    return data


def background_thread():
    while True:
        data = fetch_data()
        socketio.emit("update", data)
        time.sleep(2)


@app.route("/")
def index():
    return render_template("dashboard.html")


if __name__ == "__main__":
    socketio.start_background_task(background_thread)
    socketio.run(app, host="0.0.0.0", port=5000)