"""
dashboard.py — Real-time Arduino Photodiode Dashboard
------------------------------------------------------
Requirements:
    pip install flask flask-socketio pyserial

Run:
    python dashboard.py --port COM3        (Windows)
    python dashboard.py --port /dev/ttyACM0 (Linux/Mac)

Then open http://localhost:5000 in your browser.
"""

import argparse
import json
import threading
import time
from collections import deque
from datetime import datetime

import serial
from flask import Flask, render_template_string
from flask_socketio import SocketIO

# ── Config ────────────────────────────────────────────────────────────────────
BAUD_RATE    = 9600
HISTORY_LEN  = 120          # points kept in rolling window (~60 s at 500 ms)

# ── App ───────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = "arduino-iot-secret"
socketio = SocketIO(app, cors_allowed_origins="*")

history: deque = deque(maxlen=HISTORY_LEN)
latest  = {}

# ── HTML (single-file dashboard) ──────────────────────────────────────────────
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IoT Light Sensor Dashboard</title>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@300;600;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:      #0a0e1a;
    --panel:   #0f1628;
    --border:  #1e2d55;
    --accent:  #00e5ff;
    --accent2: #ff6b35;
    --green:   #39ff14;
    --text:    #c8d8f0;
    --dim:     #4a6080;
    --warn:    #ffd600;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Exo 2', sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* Scanline overlay */
  body::before {
    content: '';
    position: fixed; inset: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0,229,255,0.015) 2px,
      rgba(0,229,255,0.015) 4px
    );
    pointer-events: none;
    z-index: 100;
  }

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 32px;
    border-bottom: 1px solid var(--border);
    background: linear-gradient(90deg, #0a0e1a 0%, #0d1530 100%);
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 14px;
  }

  .logo-icon {
    width: 38px; height: 38px;
    border: 2px solid var(--accent);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 0 12px var(--accent);
    font-size: 18px;
  }

  .logo h1 {
    font-size: 1.25rem;
    font-weight: 800;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: var(--accent);
    text-shadow: 0 0 14px rgba(0,229,255,.5);
  }

  .logo span { font-weight: 300; color: var(--dim); font-size: .78rem; display: block; letter-spacing: .2em; }

  .status-badge {
    display: flex; align-items: center; gap: 8px;
    padding: 7px 16px;
    border: 1px solid var(--border);
    border-radius: 20px;
    font-size: .78rem;
    font-family: 'Share Tech Mono', monospace;
    letter-spacing: .1em;
  }

  .dot {
    width: 9px; height: 9px; border-radius: 50%;
    background: var(--dim);
    transition: background .3s;
  }
  .dot.live { background: var(--green); box-shadow: 0 0 8px var(--green); animation: pulse 1.4s infinite; }
  .dot.warn { background: var(--warn); box-shadow: 0 0 8px var(--warn); }

  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

  .timestamp { font-family: 'Share Tech Mono', monospace; font-size: .78rem; color: var(--dim); }

  /* Grid ------------------------------------------------------------------ */
  .grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr) 1.4fr;
    grid-template-rows: auto 1fr auto;
    gap: 16px;
    padding: 24px 32px;
    max-width: 1400px;
    margin: 0 auto;
  }

  /* Stat cards ------------------------------------------------------------ */
  .card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 22px 24px;
    position: relative;
    overflow: hidden;
    transition: border-color .3s;
  }
  .card:hover { border-color: var(--accent); }
  .card::after {
    content: '';
    position: absolute; top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    opacity: .5;
  }

  .card-label {
    font-size: .68rem;
    letter-spacing: .22em;
    text-transform: uppercase;
    color: var(--dim);
    margin-bottom: 10px;
    font-family: 'Share Tech Mono', monospace;
  }

  .card-value {
    font-size: 2.6rem;
    font-weight: 800;
    line-height: 1;
    color: var(--accent);
    text-shadow: 0 0 20px rgba(0,229,255,.35);
    font-family: 'Share Tech Mono', monospace;
    transition: color .4s;
  }

  .card-unit {
    font-size: .82rem;
    color: var(--dim);
    margin-top: 6px;
    font-weight: 300;
  }

  .card-sub {
    font-size: .72rem;
    color: var(--dim);
    margin-top: 10px;
    font-family: 'Share Tech Mono', monospace;
  }

  /* Gauge bar ------------------------------------------------------------- */
  .gauge-wrap { margin-top: 14px; }
  .gauge-track {
    height: 6px;
    background: var(--border);
    border-radius: 3px;
    overflow: hidden;
  }
  .gauge-fill {
    height: 100%;
    border-radius: 3px;
    background: linear-gradient(90deg, #00e5ff, #39ff14);
    transition: width .5s cubic-bezier(.4,0,.2,1);
    box-shadow: 0 0 8px rgba(0,229,255,.5);
  }

  /* Chart panel ----------------------------------------------------------- */
  .chart-card {
    grid-column: 1 / 5;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 22px 24px;
    min-height: 260px;
  }

  .chart-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }

  .chart-title {
    font-size: .75rem;
    letter-spacing: .2em;
    text-transform: uppercase;
    color: var(--dim);
    font-family: 'Share Tech Mono', monospace;
  }

  .chart-legend {
    display: flex; gap: 18px;
    font-size: .72rem;
    font-family: 'Share Tech Mono', monospace;
  }
  .legend-item { display: flex; align-items: center; gap: 6px; }
  .legend-dot { width: 8px; height: 8px; border-radius: 50%; }

  /* Log panel ------------------------------------------------------------- */
  .log-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px 20px;
    font-family: 'Share Tech Mono', monospace;
    font-size: .72rem;
    line-height: 1.7;
    color: var(--dim);
    overflow-y: auto;
    max-height: 180px;
  }

  .log-card .log-line { color: var(--text); }
  .log-card .log-line span { color: var(--accent); }

  /* Alert bar ------------------------------------------------------------- */
  .alert-bar {
    grid-column: 1 / 5;
    padding: 10px 20px;
    border-radius: 10px;
    font-size: .78rem;
    font-family: 'Share Tech Mono', monospace;
    letter-spacing: .08em;
    border: 1px solid transparent;
    transition: all .4s;
    text-align: center;
  }
  .alert-normal  { background: rgba(57,255,20,.06);  border-color: rgba(57,255,20,.2);  color: var(--green); }
  .alert-bright  { background: rgba(255,214,0,.07);  border-color: rgba(255,214,0,.3);  color: var(--warn); }
  .alert-dark    { background: rgba(255,107,53,.07); border-color: rgba(255,107,53,.3); color: var(--accent2); }

  @media (max-width: 900px) {
    .grid { grid-template-columns: 1fr 1fr; padding: 16px; gap: 12px; }
    .chart-card, .alert-bar { grid-column: 1 / 3; }
  }
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-icon">💡</div>
    <div>
      <h1>LightSense IoT</h1>
      <span>Arduino Uno · Photodiode Node</span>
    </div>
  </div>
  <div class="status-badge">
    <div class="dot" id="liveDot"></div>
    <span id="statusText">CONNECTING</span>
  </div>
  <div class="timestamp" id="clock">--:--:--</div>
</header>

<div class="grid">

  <!-- Lux card -->
  <div class="card">
    <div class="card-label">Illuminance</div>
    <div class="card-value" id="luxVal">—</div>
    <div class="card-unit">lux (estimated)</div>
    <div class="gauge-wrap">
      <div class="gauge-track"><div class="gauge-fill" id="luxGauge" style="width:0%"></div></div>
    </div>
    <div class="card-sub" id="luxRange">range: 0 – 1000 lux</div>
  </div>

  <!-- Voltage card -->
  <div class="card">
    <div class="card-label">Voltage</div>
    <div class="card-value" id="voltVal">—</div>
    <div class="card-unit">volts (0 – 5 V)</div>
    <div class="gauge-wrap">
      <div class="gauge-track"><div class="gauge-fill" id="voltGauge" style="width:0%"></div></div>
    </div>
    <div class="card-sub" id="voltSub">&nbsp;</div>
  </div>

  <!-- Raw ADC card -->
  <div class="card">
    <div class="card-label">ADC Raw</div>
    <div class="card-value" id="rawVal">—</div>
    <div class="card-unit">10-bit (0 – 1023)</div>
    <div class="gauge-wrap">
      <div class="gauge-track"><div class="gauge-fill" id="rawGauge" style="width:0%"></div></div>
    </div>
    <div class="card-sub" id="rawSub">&nbsp;</div>
  </div>

  <!-- Uptime card -->
  <div class="card">
    <div class="card-label">Arduino Uptime</div>
    <div class="card-value" id="uptimeVal" style="font-size:1.6rem">—</div>
    <div class="card-unit">hh:mm:ss</div>
    <div class="card-sub" id="sampleCount">samples: 0</div>
  </div>

  <!-- Alert bar -->
  <div class="alert-bar alert-normal" id="alertBar">⬤ SYSTEM NOMINAL — waiting for data</div>

  <!-- Chart -->
  <div class="chart-card">
    <div class="chart-header">
      <span class="chart-title">Live Sensor History (last 60 s)</span>
      <div class="chart-legend">
        <div class="legend-item"><div class="legend-dot" style="background:#00e5ff"></div>Lux</div>
        <div class="legend-item"><div class="legend-dot" style="background:#ff6b35"></div>Voltage×200</div>
      </div>
    </div>
    <canvas id="sensorChart" height="200"></canvas>
  </div>

  <!-- Log -->
  <div class="log-card" id="logBox" style="grid-column:1/5">
    <div style="color:var(--accent);margin-bottom:4px">// Serial log</div>
  </div>

</div>

<script>
const socket = io();
let samples = 0;

// Clock
setInterval(() => {
  document.getElementById('clock').textContent =
    new Date().toLocaleTimeString('en-GB');
}, 1000);

// Chart setup
const ctx = document.getElementById('sensorChart').getContext('2d');
const MAX_POINTS = 120;

const chartData = {
  labels: [],
  datasets: [
    {
      label: 'Lux',
      data: [],
      borderColor: '#00e5ff',
      backgroundColor: 'rgba(0,229,255,0.07)',
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.4,
      fill: true,
    },
    {
      label: 'Voltage ×200',
      data: [],
      borderColor: '#ff6b35',
      backgroundColor: 'rgba(255,107,53,0.06)',
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.4,
      fill: true,
    }
  ]
};

const chart = new Chart(ctx, {
  type: 'line',
  data: chartData,
  options: {
    animation: false,
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        ticks: { color: '#4a6080', font: { family: 'Share Tech Mono', size: 10 }, maxTicksLimit: 10 },
        grid: { color: 'rgba(30,45,85,.6)' }
      },
      y: {
        min: 0,
        ticks: { color: '#4a6080', font: { family: 'Share Tech Mono', size: 10 } },
        grid: { color: 'rgba(30,45,85,.6)' }
      }
    },
    plugins: { legend: { display: false } }
  }
});

function pushChart(ts, lux, voltage) {
  if (chartData.labels.length >= MAX_POINTS) {
    chartData.labels.shift();
    chartData.datasets[0].data.shift();
    chartData.datasets[1].data.shift();
  }
  chartData.labels.push(ts);
  chartData.datasets[0].data.push(lux.toFixed(1));
  chartData.datasets[1].data.push((voltage * 200).toFixed(1));
  chart.update('none');
}

// Format uptime ms → hh:mm:ss
function fmtUptime(ms) {
  const s = Math.floor(ms / 1000);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return [h,m,sec].map(v => String(v).padStart(2,'0')).join(':');
}

// Socket events
socket.on('connect', () => {
  document.getElementById('liveDot').classList.add('live');
  document.getElementById('statusText').textContent = 'LIVE';
});

socket.on('disconnect', () => {
  document.getElementById('liveDot').className = 'dot warn';
  document.getElementById('statusText').textContent = 'DISCONNECTED';
});

socket.on('sensor_data', (d) => {
  samples++;
  const ts = new Date().toLocaleTimeString('en-GB');

  // Update stat cards
  document.getElementById('luxVal').textContent   = d.lux.toFixed(1);
  document.getElementById('voltVal').textContent  = d.voltage.toFixed(3);
  document.getElementById('rawVal').textContent   = d.raw;
  document.getElementById('uptimeVal').textContent = fmtUptime(d.uptime);
  document.getElementById('sampleCount').textContent = `samples: ${samples}`;

  // Gauges (% of max)
  document.getElementById('luxGauge').style.width  = Math.min(d.lux / 10, 100) + '%';
  document.getElementById('voltGauge').style.width = (d.voltage / 5 * 100) + '%';
  document.getElementById('rawGauge').style.width  = (d.raw / 1023 * 100) + '%';

  // Sub-labels
  document.getElementById('voltSub').textContent  = `${(d.voltage/5*100).toFixed(1)}% of Vcc`;
  document.getElementById('rawSub').textContent   = `res: ${(d.raw/1023*100).toFixed(1)}%`;

  // Alert bar
  const ab = document.getElementById('alertBar');
  if (d.lux > 800) {
    ab.className = 'alert-bar alert-bright';
    ab.textContent = '⚠ HIGH LIGHT LEVEL — sensor near saturation';
  } else if (d.lux < 20) {
    ab.className = 'alert-bar alert-dark';
    ab.textContent = '⬤ LOW LIGHT — minimal ambient illumination';
  } else {
    ab.className = 'alert-bar alert-normal';
    ab.textContent = `⬤ NOMINAL — ${d.lux.toFixed(0)} lux @ ${d.voltage.toFixed(3)} V`;
  }

  // Chart
  pushChart(ts, d.lux, d.voltage);

  // Log
  const log = document.getElementById('logBox');
  const line = document.createElement('div');
  line.className = 'log-line';
  line.innerHTML = `<span>${ts}</span>  raw=${String(d.raw).padStart(4)}  volt=${d.voltage.toFixed(3)}V  lux=${d.lux.toFixed(1)}`;
  log.appendChild(line);
  if (log.children.length > 30) log.removeChild(log.children[1]);
  log.scrollTop = log.scrollHeight;
});
</script>
</body>
</html>
"""

# ── Flask route ───────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(DASHBOARD_HTML)

# ── Serial reader thread ──────────────────────────────────────────────────────
def serial_reader(port: str):
    print(f"[serial] Connecting to {port} @ {BAUD_RATE} baud …")
    while True:
        try:
            with serial.Serial(port, BAUD_RATE, timeout=2) as ser:
                print(f"[serial] Connected ✓")
                ser.reset_input_buffer()
                while True:
                    raw_line = ser.readline().decode("utf-8", errors="ignore").strip()
                    if not raw_line:
                        continue
                    try:
                        data = json.loads(raw_line)
                        ts   = datetime.now().isoformat()
                        data["timestamp"] = ts
                        history.append(data)
                        socketio.emit("sensor_data", data)
                    except json.JSONDecodeError:
                        pass   # skip malformed lines
        except serial.SerialException as e:
            print(f"[serial] Error: {e} — retrying in 3 s …")
            time.sleep(3)

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arduino IoT Dashboard")
    parser.add_argument("--port", default="COM3",  help="Serial port (e.g. COM3 or /dev/ttyACM0)")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--webport", default=5000, type=int)
    args = parser.parse_args()

    t = threading.Thread(target=serial_reader, args=(args.port,), daemon=True)
    t.start()

    print(f"[web] Dashboard → http://localhost:{args.webport}")
    socketio.run(app, host=args.host, port=args.webport, debug=False)
