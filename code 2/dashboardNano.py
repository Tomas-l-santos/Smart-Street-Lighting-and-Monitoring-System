import argparse
import re
import statistics
import threading
import time
from collections import deque
from datetime import datetime

import serial
from flask import Flask, render_template_string
from flask_socketio import SocketIO

BAUD_RATE = 9600
HISTORY_LEN = 180
SERIAL_TIMEOUT = 1
REFRESH_SECONDS = 0.2

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sensors-network-dashboard'
socketio = SocketIO(app, cors_allowed_origins='*')

history = deque(maxlen=HISTORY_LEN)
latest = {
    'sensor_value': None,
    'light_level': 'Waiting for data',
    'risk_text': 'No data yet',
    'big_led': 'Unknown',
    'small_leds_on': 0,
    'updated_at': '--:--:--',
    'avg': 0,
    'minimum': 0,
    'maximum': 0,
    'trend': 'Stable',
    'alert': 'Connecting to Arduino...',
    'alert_level': 'info'
}

SERIAL_PATTERN = re.compile(r'Sensor\s*Value\s*:\s*(\d+)', re.IGNORECASE)

HTML = r'''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Smart Street Lighting Dashboard</title>
  <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {
      --bg: #09111f;
      --panel: rgba(15, 24, 43, 0.88);
      --panel-2: rgba(23, 35, 63, 0.95);
      --border: rgba(124, 149, 205, 0.22);
      --text: #eaf1ff;
      --muted: #9fb3da;
      --accent: #5aa7ff;
      --accent-2: #6ef3d6;
      --warn: #ffb84d;
      --danger: #ff6b7a;
      --ok: #71f29a;
      --shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
      --radius: 22px;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: Inter, Arial, Helvetica, sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(90,167,255,0.18), transparent 28%),
        radial-gradient(circle at top right, rgba(110,243,214,0.11), transparent 22%),
        linear-gradient(160deg, #07101d 0%, #09111f 45%, #0d1730 100%);
      min-height: 100vh;
    }

    .shell {
      max-width: 1400px;
      margin: 0 auto;
      padding: 28px;
    }

    .hero {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 20px;
      margin-bottom: 24px;
      padding: 24px 28px;
      border: 1px solid var(--border);
      border-radius: 28px;
      background: linear-gradient(145deg, rgba(11,19,36,0.92), rgba(16,27,49,0.82));
      box-shadow: var(--shadow);
      backdrop-filter: blur(12px);
    }

    .hero h1 {
      margin: 0 0 8px;
      font-size: clamp(2rem, 3.6vw, 3.25rem);
      line-height: 1.05;
      letter-spacing: -0.03em;
    }

    .hero p {
      margin: 0;
      color: var(--muted);
      font-size: 1rem;
      max-width: 760px;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 12px 18px;
      border-radius: 999px;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.09);
      color: var(--text);
      font-weight: 700;
      white-space: nowrap;
    }

    .pill-dot {
      width: 11px;
      height: 11px;
      border-radius: 50%;
      background: var(--ok);
      box-shadow: 0 0 14px var(--ok);
    }

    .grid {
      display: grid;
      grid-template-columns: 1.25fr 1.25fr 1fr;
      gap: 18px;
    }

    .card {
      background: linear-gradient(180deg, var(--panel), var(--panel-2));
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 22px;
      backdrop-filter: blur(10px);
    }

    .span-2 { grid-column: span 2; }

    .label {
      color: var(--muted);
      font-size: 0.88rem;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      margin-bottom: 10px;
      font-weight: 700;
    }

    .big-number {
      font-size: clamp(2.8rem, 5vw, 4.8rem);
      font-weight: 800;
      line-height: 1;
      margin: 0;
    }

    .subtext {
      margin-top: 12px;
      color: var(--muted);
      font-size: 0.98rem;
    }

    .status-chip {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-top: 14px;
      padding: 10px 14px;
      border-radius: 999px;
      background: rgba(255,255,255,0.07);
      border: 1px solid rgba(255,255,255,0.08);
      font-weight: 700;
    }

    .mini-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 14px;
      margin-top: 10px;
    }

    .metric {
      padding: 16px;
      border-radius: 18px;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.07);
    }

    .metric h3 {
      margin: 0 0 8px;
      font-size: 0.88rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.1em;
    }

    .metric p {
      margin: 0;
      font-size: 1.6rem;
      font-weight: 800;
    }

    .bar {
      height: 16px;
      border-radius: 999px;
      background: rgba(255,255,255,0.08);
      overflow: hidden;
      margin-top: 12px;
      border: 1px solid rgba(255,255,255,0.05);
    }

    .bar-fill {
      height: 100%;
      width: 0%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--accent-2), var(--accent));
      transition: width 0.25s ease;
    }

    .led-strip {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 16px;
    }

    .led {
      width: 26px;
      height: 26px;
      border-radius: 50%;
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.1);
      box-shadow: inset 0 0 8px rgba(0,0,0,0.45);
      transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
    }

    .led.on {
      background: radial-gradient(circle at 35% 35%, #fef7b0, #ffd34d 58%, #e29c00 100%);
      box-shadow: 0 0 16px rgba(255, 202, 74, 0.55), 0 0 28px rgba(255, 202, 74, 0.2);
      transform: translateY(-1px);
    }

    .led.big {
      width: 42px;
      height: 42px;
      margin-top: 8px;
      border-width: 2px;
    }

    .alert {
      padding: 18px;
      border-radius: 18px;
      font-weight: 700;
      line-height: 1.45;
      border: 1px solid transparent;
      min-height: 78px;
      display: flex;
      align-items: center;
    }

    .alert.info {
      background: rgba(90, 167, 255, 0.12);
      border-color: rgba(90, 167, 255, 0.28);
      color: #dbeaff;
    }

    .alert.warning {
      background: rgba(255, 184, 77, 0.12);
      border-color: rgba(255, 184, 77, 0.28);
      color: #ffe8bf;
    }

    .alert.danger {
      background: rgba(255, 107, 122, 0.12);
      border-color: rgba(255, 107, 122, 0.28);
      color: #ffd9de;
    }

    .chart-wrap {
      height: 360px;
      margin-top: 8px;
    }

    .footer-note {
      margin-top: 14px;
      color: var(--muted);
      font-size: 0.92rem;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      overflow: hidden;
      border-radius: 14px;
    }

    th, td {
      padding: 12px 10px;
      text-align: left;
      border-bottom: 1px solid rgba(255,255,255,0.07);
      font-size: 0.95rem;
    }

    th {
      color: var(--muted);
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    tr:last-child td {
      border-bottom: none;
    }

    @media (max-width: 1180px) {
      .grid { grid-template-columns: 1fr 1fr; }
      .span-2 { grid-column: span 2; }
    }

    @media (max-width: 800px) {
      .hero { flex-direction: column; align-items: flex-start; }
      .grid { grid-template-columns: 1fr; }
      .span-2 { grid-column: span 1; }
      .shell { padding: 16px; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div>
        <h1>Smart Street Lighting Dashboard</h1>
        <p>Live monitoring for the Arduino light detector system. This dashboard visualises sensor readings, inferred street-light response, recent trends, and threshold-based alerts for the group report and live demo.</p>
      </div>
      <div class="pill"><span class="pill-dot"></span><span id="connectionState">Live serial stream</span></div>
    </section>

    <section class="grid">
      <div class="card">
        <div class="label">Current Sensor Reading</div>
        <p id="sensorValue" class="big-number">--</p>
        <div class="subtext">Raw analog value from the light detector on pin A1</div>
        <div class="bar"><div id="sensorBar" class="bar-fill"></div></div>
        <div id="updatedAt" class="status-chip">Last update: --:--:--</div>
      </div>

      <div class="card">
        <div class="label">Environment Classification</div>
        <p id="lightLevel" class="big-number" style="font-size:clamp(2rem,4vw,3.4rem)">Waiting</p>
        <div id="riskText" class="subtext">Awaiting live sensor input.</div>
        <div class="mini-grid">
          <div class="metric">
            <h3>Trend</h3>
            <p id="trend">Stable</p>
          </div>
          <div class="metric">
            <h3>Street Light</h3>
            <p id="bigLedState">Unknown</p>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="label">System Alert</div>
        <div id="alertBox" class="alert info">Connecting to Arduino...</div>
        <div class="footer-note">Threshold alerts support the rubric requirement for notifications when key conditions are met.</div>
      </div>

      <div class="card span-2">
        <div class="label">Real-Time Sensor Graph</div>
        <div class="chart-wrap"><canvas id="sensorChart"></canvas></div>
        <div class="footer-note">Rolling history of light readings used to show live system behaviour and support later analysis screenshots.</div>
      </div>

      <div class="card">
        <div class="label">Streetlight Response</div>
        <div class="subtext">Small indicator LEDs inferred from your existing Arduino logic</div>
        <div id="smallLedCount" class="status-chip">0 / 6 small LEDs on</div>
        <div class="led-strip" id="smallLedStrip">
          <div class="led"></div><div class="led"></div><div class="led"></div><div class="led"></div><div class="led"></div><div class="led"></div>
        </div>
        <div class="subtext" style="margin-top:18px;">Main street light (big LED)</div>
        <div class="led-strip"><div id="bigLedVisual" class="led big"></div></div>
      </div>

      <div class="card">
        <div class="label">Quick Statistics</div>
        <div class="mini-grid">
          <div class="metric"><h3>Minimum</h3><p id="minVal">0</p></div>
          <div class="metric"><h3>Maximum</h3><p id="maxVal">0</p></div>
          <div class="metric"><h3>Average</h3><p id="avgVal">0</p></div>
          <div class="metric"><h3>Samples</h3><p id="sampleCount">0</p></div>
        </div>
      </div>

      <div class="card">
        <div class="label">Recent Samples</div>
        <table>
          <thead>
            <tr><th>Time</th><th>Value</th><th>Condition</th></tr>
          </thead>
          <tbody id="sampleTable"></tbody>
        </table>
      </div>
    </section>
  </div>

<script>
  const socket = io();
  const chartCtx = document.getElementById('sensorChart').getContext('2d');
  const chart = new Chart(chartCtx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'Sensor Value',
        data: [],
        borderWidth: 3,
        tension: 0.28,
        pointRadius: 0,
        fill: true,
        backgroundColor: 'rgba(90, 167, 255, 0.18)',
        borderColor: '#70b5ff'
      }]
    },
    options: {
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        legend: { labels: { color: '#dfe9ff' } }
      },
      scales: {
        x: {
          ticks: { color: '#9fb3da' },
          grid: { color: 'rgba(255,255,255,0.05)' }
        },
        y: {
          min: 0,
          max: 1023,
          ticks: { color: '#9fb3da' },
          grid: { color: 'rgba(255,255,255,0.05)' }
        }
      }
    }
  });

  function setText(id, value) {
    document.getElementById(id).textContent = value;
  }

  function updateLeds(count, bigOn) {
    const leds = document.querySelectorAll('#smallLedStrip .led');
    leds.forEach((led, index) => {
      if (index < count) led.classList.add('on');
      else led.classList.remove('on');
    });

    const big = document.getElementById('bigLedVisual');
    if (bigOn) big.classList.add('on');
    else big.classList.remove('on');
  }

  function updateTable(samples) {
    const body = document.getElementById('sampleTable');
    body.innerHTML = '';
    samples.slice(-6).reverse().forEach(sample => {
      const row = document.createElement('tr');
      row.innerHTML = `<td>${sample.time}</td><td>${sample.value}</td><td>${sample.level}</td>`;
      body.appendChild(row);
    });
  }

  socket.on('connect', () => {
    setText('connectionState', 'Live serial stream connected');
  });

  socket.on('dashboard_update', payload => {
    setText('sensorValue', payload.sensor_value ?? '--');
    setText('lightLevel', payload.light_level);
    setText('riskText', payload.risk_text);
    setText('trend', payload.trend);
    setText('bigLedState', payload.big_led);
    setText('updatedAt', `Last update: ${payload.updated_at}`);
    setText('smallLedCount', `${payload.small_leds_on} / 6 small LEDs on`);
    setText('minVal', payload.minimum);
    setText('maxVal', payload.maximum);
    setText('avgVal', payload.avg);
    setText('sampleCount', payload.sample_count);

    const pct = payload.sensor_value !== null ? (payload.sensor_value / 1023) * 100 : 0;
    document.getElementById('sensorBar').style.width = `${pct}%`;

    const alertBox = document.getElementById('alertBox');
    alertBox.textContent = payload.alert;
    alertBox.className = `alert ${payload.alert_level}`;

    chart.data.labels = payload.chart_labels;
    chart.data.datasets[0].data = payload.chart_values;
    chart.update();

    updateLeds(payload.small_leds_on, payload.big_led === 'ON');
    updateTable(payload.samples);
  });
</script>
</body>
</html>
'''


def infer_state(sensor_value: int):
    if sensor_value > 800:
        small_leds_on = 0
        light_level = 'Very Bright'
        risk_text = 'High natural light detected. Small LED indicators remain off.'
        alert = 'Very bright conditions detected. Artificial lighting demand is minimal.'
        alert_level = 'info'
    elif sensor_value > 650:
        small_leds_on = 1
        light_level = 'Bright'
        risk_text = 'Daylight is still strong. Only the first meter LED is active.'
        alert = 'Bright ambient light. System stays mostly inactive for energy saving.'
        alert_level = 'info'
    elif sensor_value > 500:
        small_leds_on = 2
        light_level = 'Moderate'
        risk_text = 'Ambient light is falling. The system begins indicating reduced brightness.'
        alert = 'Moderate light level. Monitor for further decrease in ambient light.'
        alert_level = 'info'
    elif sensor_value > 350:
        small_leds_on = 3
        light_level = 'Dim'
        risk_text = 'Conditions are getting darker. More indicator LEDs are triggered.'
        alert = 'Dim conditions detected. Street-light response is becoming more active.'
        alert_level = 'warning'
    elif sensor_value > 250:
        small_leds_on = 4
        light_level = 'Dark'
        risk_text = 'Low light level detected. The system is nearing full lighting support.'
        alert = 'Dark conditions detected. Artificial lighting support is strongly needed.'
        alert_level = 'warning'
    elif sensor_value > 150:
        small_leds_on = 5
        light_level = 'Very Dark'
        risk_text = 'Very low ambient light. Nearly all indicator LEDs are active.'
        alert = 'Very dark environment. Street lighting system should remain highly active.'
        alert_level = 'danger'
    else:
        small_leds_on = 6
        light_level = 'Extremely Dark'
        risk_text = 'Extremely low light detected. All indicator LEDs are active.'
        alert = 'Critical darkness detected. Full lighting support is required.'
        alert_level = 'danger'

    big_led_on = sensor_value <= 500
    big_led = 'ON' if big_led_on else 'OFF'
    return small_leds_on, big_led, light_level, risk_text, alert, alert_level


def compute_trend(values):
    if len(values) < 6:
        return 'Stable'
    recent = list(values)[-6:]
    delta = recent[-1] - recent[0]
    if delta > 40:
        return 'Brightening'
    if delta < -40:
        return 'Darkening'
    return 'Stable'


def serial_reader(port_name):
    global latest
    while True:
        try:
            with serial.Serial(port_name, BAUD_RATE, timeout=SERIAL_TIMEOUT) as ser:
                time.sleep(2)
                latest['alert'] = f'Connected to {port_name}. Waiting for incoming readings...'
                latest['alert_level'] = 'info'
                while True:
                    raw = ser.readline().decode(errors='ignore').strip()
                    if not raw:
                        continue
                    match = SERIAL_PATTERN.search(raw)
                    if not match:
                        continue

                    sensor_value = int(match.group(1))
                    small_leds_on, big_led, light_level, risk_text, alert, alert_level = infer_state(sensor_value)
                    now_str = datetime.now().strftime('%H:%M:%S')

                    history.append({
                        'time': now_str,
                        'value': sensor_value,
                        'level': light_level
                    })

                    values = [item['value'] for item in history]
                    latest = {
                        'sensor_value': sensor_value,
                        'light_level': light_level,
                        'risk_text': risk_text,
                        'big_led': big_led,
                        'small_leds_on': small_leds_on,
                        'updated_at': now_str,
                        'avg': round(statistics.mean(values), 1),
                        'minimum': min(values),
                        'maximum': max(values),
                        'trend': compute_trend(values),
                        'alert': alert,
                        'alert_level': alert_level,
                    }
        except Exception as exc:
            latest['alert'] = f'Serial connection issue on {port_name}: {exc}'
            latest['alert_level'] = 'danger'
            time.sleep(2)


def broadcaster():
    while True:
        payload = dict(latest)
        payload['chart_labels'] = [item['time'] for item in history]
        payload['chart_values'] = [item['value'] for item in history]
        payload['samples'] = list(history)
        payload['sample_count'] = len(history)
        socketio.emit('dashboard_update', payload)
        socketio.sleep(REFRESH_SECONDS)


@app.route('/')
def index():
    return render_template_string(HTML)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Smart Street Lighting Dashboard')
    parser.add_argument('--port', required=True, help='Serial port, e.g. COM3 or /dev/ttyACM0')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--web-port', type=int, default=5000)
    args = parser.parse_args()

    threading.Thread(target=serial_reader, args=(args.port,), daemon=True).start()
    socketio.start_background_task(broadcaster)
    socketio.run(app, host=args.host, port=args.web_port, debug=False)
