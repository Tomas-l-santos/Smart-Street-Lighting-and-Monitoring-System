"""
dashboard.py — Real-time Arduino LDR + LED Dashboard
-----------------------------------------------------
Requirements:
    pip install flask flask-socketio pyserial

Run:
    python dashboard.py --port COM3         (Windows)
    python dashboard.py --port /dev/ttyACM0 (Linux/Mac)

Then open:
    http://localhost:5000

Reads JSON lines from the Arduino in this format:
    {"raw":512,"voltage":2.500,"ldr_ohms":9765,"lux":51.2,"uptime":4321}
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
BAUD_RATE   = 9600
HISTORY_LEN = 120   # ~60 s at 500 ms interval

# ── App ───────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = "arduino-ldr-dashboard"
socketio = SocketIO(app, cors_allowed_origins="*")

history: deque = deque(maxlen=HISTORY_LEN)
latest = {}

# ── Dashboard HTML ────────────────────────────────────────────────────────────
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IoT LDR Dashboard</title>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@300;600;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:     #0a0f1f;
    --panel:  #11182b;
    --border: #1e2d55;
    --accent: #00e5ff;
    --amber:  #ffb703;
    --green:  #39ff14;
    --red:    #ff5a5f;
    --text:   #d7e3ff;
    --dim:    #4a6080;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Exo 2', sans-serif;
    min-height: 100vh;
  }
  body::before {
    content: '';
    position: fixed; inset: 0;
    background: repeating-linear-gradient(0deg, transparent, transparent 2px,
      rgba(0,229,255,.015) 2px, rgba(0,229,255,.015) 4px);
    pointer-events: none; z-index: 100;
  }

  header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 16px 28px; border-bottom: 1px solid var(--border);
    background: linear-gradient(90deg, #0a0f1f, #0d1731);
    flex-wrap: wrap; gap: 12px;
  }
  .logo { display: flex; align-items: center; gap: 14px; }
  .logo-icon {
    width: 40px; height: 40px; border: 2px solid var(--accent);
    border-radius: 10px; display: flex; align-items: center;
    justify-content: center; box-shadow: 0 0 12px var(--accent); font-size: 20px;
  }
  .logo h1 { font-size: 1.15rem; font-weight: 800; letter-spacing: .1em;
              text-transform: uppercase; color: var(--accent); }
  .logo span { font-weight: 300; color: var(--dim); font-size: .78rem; letter-spacing: .14em; }
  .header-right { display: flex; align-items: center; gap: 14px; }
  .status-badge {
    display: flex; align-items: center; gap: 8px;
    padding: 7px 14px; border: 1px solid var(--border);
    border-radius: 999px; font-size: .76rem;
    font-family: 'Share Tech Mono', monospace; letter-spacing: .08em;
  }
  .dot { width: 9px; height: 9px; border-radius: 50%; background: var(--dim); }
  .dot.live { background: var(--green); box-shadow: 0 0 8px var(--green); animation: pulse 1.4s infinite; }
  .dot.warn { background: var(--red);   box-shadow: 0 0 8px var(--red); }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
  .clock { font-family: 'Share Tech Mono', monospace; font-size: .78rem; color: var(--dim); }

  .grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px; padding: 24px 28px;
    max-width: 1400px; margin: 0 auto;
  }

  .card {
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 14px; padding: 20px; position: relative; overflow: hidden;
  }
  .card::after {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    opacity: .5;
  }
  .card-label { font-size: .68rem; letter-spacing: .22em; text-transform: uppercase;
                color: var(--dim); margin-bottom: 10px; font-family: 'Share Tech Mono', monospace; }
  .card-value { font-size: 2.4rem; font-weight: 800; line-height: 1;
                color: var(--accent); font-family: 'Share Tech Mono', monospace;
                text-shadow: 0 0 18px rgba(0,229,255,.3); }
  .card-unit  { font-size: .8rem; color: var(--dim); margin-top: 6px; }
  .card-sub   { font-size: .72rem; color: var(--dim); margin-top: 10px;
                font-family: 'Share Tech Mono', monospace; line-height: 1.5; }

  .gauge-wrap  { margin-top: 14px; }
  .gauge-track { height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
  .gauge-fill  {
    height: 100%; width: 0%; border-radius: 3px;
    background: linear-gradient(90deg, #00e5ff, #39ff14);
    transition: width .4s cubic-bezier(.4,0,.2,1);
    box-shadow: 0 0 8px rgba(0,229,255,.5);
  }

  .led-panel   { grid-column: span 2; }
  .led-wrap    { display: flex; justify-content: center; align-items: center; min-height: 160px; }
  .led-bulb    {
    width: 110px; height: 110px; border-radius: 50%;
    background: #111827; border: 3px solid #4a6080;
    box-shadow: inset 0 0 20px rgba(255,255,255,.05);
    transition: all .25s ease;
  }

  .state-panel { grid-column: span 2; }
  .state-pill  {
    display: inline-block; margin-top: 12px;
    padding: 8px 16px; border-radius: 999px;
    font-size: .84rem; font-weight: 700;
    font-family: 'Share Tech Mono', monospace; letter-spacing: .06em;
  }
  .pill-bright { color: var(--green); border: 1px solid rgba(57,255,20,.4);  background: rgba(57,255,20,.08); }
  .pill-dim    { color: var(--amber); border: 1px solid rgba(255,183,3,.4);  background: rgba(255,183,3,.08); }
  .pill-dark   { color: var(--red);   border: 1px solid rgba(255,90,95,.4);  background: rgba(255,90,95,.08); }

  .alert-bar {
    grid-column: 1 / 5;
    padding: 10px 20px; border-radius: 10px;
    font-size: .78rem; font-family: 'Share Tech Mono', monospace;
    letter-spacing: .08em; border: 1px solid transparent;
    text-align: center; transition: all .4s;
  }
  .alert-normal { background: rgba(57,255,20,.06);  border-color: rgba(57,255,20,.2);  color: var(--green); }
  .alert-bright { background: rgba(255,214,0,.07);  border-color: rgba(255,214,0,.3);  color: var(--amber); }
  .alert-dark   { background: rgba(255,90,95,.07);  border-color: rgba(255,90,95,.3);  color: var(--red); }

  .chart-card {
    grid-column: 1 / 5;
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 14px; padding: 20px; min-height: 280px;
  }
  .chart-header { display: flex; justify-content: space-between;
                  align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 12px; }
  .chart-title  { font-size: .75rem; letter-spacing: .18em; text-transform: uppercase;
                  color: var(--dim); font-family: 'Share Tech Mono', monospace; }
  .chart-legend { display: flex; gap: 16px; font-size: .74rem; font-family: 'Share Tech Mono', monospace; }
  .legend-item  { display: flex; align-items: center; gap: 6px; }
  .legend-dot   { width: 8px; height: 8px; border-radius: 50%; }

  .log-card {
    grid-column: 1 / 5;
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 14px; padding: 18px;
    font-family: 'Share Tech Mono', monospace; font-size: .73rem;
    line-height: 1.7; color: var(--dim);
    overflow-y: auto; max-height: 200px;
  }
  .log-line { color: var(--text); }
  .log-line span { color: var(--accent); }

  @media (max-width: 1000px) {
    .grid { grid-template-columns: repeat(2, 1fr); }
    .led-panel, .state-panel, .alert-bar, .chart-card, .log-card { grid-column: 1 / 3; }
  }
  @media (max-width: 600px) {
    .grid { grid-template-columns: 1fr; padding: 16px; }
    .led-panel, .state-panel, .alert-bar, .chart-card, .log-card { grid-column: 1 / 2; }
  }
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-icon">💡</div>
    <div>
      <h1>LDR Sensor Dashboard</h1>
      <span>Arduino Uno · Photoresistor on A0 · Blink LED on D7</span>
    </div>
  </div>
  <div class="header-right">
    <div class="status-badge">
      <div class="dot" id="liveDot"></div>
      <span id="statusText">CONNECTING</span>
    </div>
    <div class="clock" id="clock">--:--:--</div>
  </div>
</header>

<div class="grid">

  <div class="card">
    <div class="card-label">ADC Raw</div>
    <div class="card-value" id="rawVal">—</div>
    <div class="card-unit">10-bit value (0 – 1023)</div>
    <div class="gauge-wrap"><div class="gauge-track"><div class="gauge-fill" id="rawGauge"></div></div></div>
    <div class="card-sub" id="rawSub">Waiting for data…</div>
  </div>

  <div class="card">
    <div class="card-label">Voltage</div>
    <div class="card-value" id="voltVal">—</div>
    <div class="card-unit">volts (0 – 5 V)</div>
    <div class="gauge-wrap"><div class="gauge-track"><div class="gauge-fill" id="voltGauge"></div></div></div>
    <div class="card-sub" id="voltSub">Voltage divider midpoint</div>
  </div>

  <div class="card">
    <div class="card-label">LDR Resistance</div>
    <div class="card-value" id="ohmsVal">—</div>
    <div class="card-unit">ohms</div>
    <div class="gauge-wrap"><div class="gauge-track"><div class="gauge-fill" id="ohmsGauge"></div></div></div>
    <div class="card-sub" id="ohmsSub">High Ω = dark · Low Ω = bright</div>
  </div>

  <div class="card">
    <div class="card-label">Illuminance</div>
    <div class="card-value" id="luxVal">—</div>
    <div class="card-unit">lux (estimated)</div>
    <div class="gauge-wrap"><div class="gauge-track"><div class="gauge-fill" id="luxGauge"></div></div></div>
    <div class="card-sub" id="luxSub">GL5528 approximation</div>
  </div>

  <div class="alert-bar alert-normal" id="alertBar">⬤  SYSTEM NOMINAL — awaiting first reading</div>

  <div class="card led-panel">
    <div class="card-label">Sensor Light Level (visual)</div>
    <div class="led-wrap"><div class="led-bulb" id="ledBulb"></div></div>
    <div class="card-sub" style="text-align:center">Brightness reflects current lux reading</div>
  </div>

  <div class="card state-panel">
    <div class="card-label">Light Condition</div>
    <div class="card-value" id="stateText">—</div>
    <div class="state-pill pill-bright" id="statePill">WAITING</div>
    <div class="card-sub" style="margin-top:14px">
      &gt; 200 lux → Bright<br>
      50 – 200 lux → Dim / indoor<br>
      &lt; 50 lux → Dark / night
    </div>
    <div class="card-sub" style="margin-top:10px" id="uptimeSub">Uptime: —</div>
  </div>

  <div class="chart-card">
    <div class="chart-header">
      <span class="chart-title">Live Line Chart — Lux · Voltage · Raw ADC (last 30 s)</span>
      <div class="chart-legend">
        <div class="legend-item"><div class="legend-dot" style="background:#00e5ff"></div>Lux</div>
        <div class="legend-item"><div class="legend-dot" style="background:#ffb703"></div>Voltage ×200</div>
        <div class="legend-item"><div class="legend-dot" style="background:#a78bfa"></div>Raw ADC</div>
      </div>
    </div>
    <canvas id="sensorChart" height="220"></canvas>
  </div>

  <div class="log-card" id="logBox">
    <div style="color:var(--accent);margin-bottom:4px">// Serial JSON log</div>
  </div>

</div>

<script>
const socket = io();
let samples = 0;

setInterval(() => {
  document.getElementById('clock').textContent = new Date().toLocaleTimeString('en-GB');
}, 1000);

const ctx = document.getElementById('sensorChart').getContext('2d');
const MAX = 60; // 60 slots = 30 s at 500 ms per reading

// Pre-fill all slots with empty labels and null values so the chart
// renders at full fixed width immediately — length never changes,
// so the chart never resizes or scrolls vertically.
const lineData = {
  labels: Array(MAX).fill(''),
  datasets: [
    { label: 'Lux', data: Array(MAX).fill(null),
      borderColor: '#00e5ff', backgroundColor: 'rgba(0,229,255,0.08)',
      borderWidth: 2, pointRadius: 0, tension: 0.4, fill: true, spanGaps: false },
    { label: 'Voltage×200', data: Array(MAX).fill(null),
      borderColor: '#ffb703', backgroundColor: 'rgba(255,183,3,0.06)',
      borderWidth: 2, pointRadius: 0, tension: 0.4, fill: true, spanGaps: false },
    { label: 'Raw ADC', data: Array(MAX).fill(null),
      borderColor: '#a78bfa', backgroundColor: 'rgba(167,139,250,0.05)',
      borderWidth: 1.5, pointRadius: 0, tension: 0.4, fill: false, spanGaps: false },
  ]
};

const chart = new Chart(ctx, {
  type: 'line',
  data: lineData,
  options: {
    animation: false,
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        ticks: { color: '#4a6080', font: { family: 'Share Tech Mono', size: 10 }, maxTicksLimit: 8 },
        grid:  { color: 'rgba(30,45,85,.6)' }
      },
      y: {
        min: 0,
        ticks: { color: '#4a6080', font: { family: 'Share Tech Mono', size: 10 } },
        grid:  { color: 'rgba(30,45,85,.6)' }
      }
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (c) => ` ${c.dataset.label}: ${c.parsed.y}`
        }
      }
    }
  }
});

// Shift one slot off the left, push the new value onto the right.
// Array length stays fixed at MAX the entire time, so the chart
// width is constant — data scrolls in from the right.
function pushChart(ts, lux, voltage, raw) {
  lineData.labels.shift();              lineData.labels.push(ts);
  lineData.datasets[0].data.shift();    lineData.datasets[0].data.push(parseFloat(lux).toFixed(1));
  lineData.datasets[1].data.shift();    lineData.datasets[1].data.push((voltage * 200).toFixed(1));
  lineData.datasets[2].data.shift();    lineData.datasets[2].data.push(raw);
  chart.update('none');
}

function fmtUptime(ms) {
  const s = Math.floor(ms / 1000);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return [h, m, sec].map(v => String(v).padStart(2,'0')).join(':');
}

socket.on('connect', () => {
  document.getElementById('liveDot').className = 'dot live';
  document.getElementById('statusText').textContent = 'LIVE';
});
socket.on('disconnect', () => {
  document.getElementById('liveDot').className = 'dot warn';
  document.getElementById('statusText').textContent = 'DISCONNECTED';
});

socket.on('sensor_data', (d) => {
  samples++;
  const ts  = new Date().toLocaleTimeString('en-GB');
  const lux = parseFloat(d.lux);

  // Stat cards
  document.getElementById('rawVal').textContent  = d.raw;
  document.getElementById('voltVal').textContent = parseFloat(d.voltage).toFixed(3);
  document.getElementById('ohmsVal').textContent =
    d.ldr_ohms >= 999999 ? '∞' :
    d.ldr_ohms >= 1000   ? (d.ldr_ohms / 1000).toFixed(1) + 'k' :
                            Math.round(d.ldr_ohms);
  document.getElementById('luxVal').textContent  = lux.toFixed(1);

  // Gauges
  document.getElementById('rawGauge').style.width  = (d.raw / 1023 * 100) + '%';
  document.getElementById('voltGauge').style.width = (d.voltage / 5 * 100) + '%';
  document.getElementById('ohmsGauge').style.width = Math.min(d.ldr_ohms / 100000 * 100, 100) + '%';
  document.getElementById('luxGauge').style.width  = Math.min(lux / 1000 * 100, 100) + '%';

  // Sub labels
  document.getElementById('rawSub').textContent  = `${(d.raw / 1023 * 100).toFixed(1)}% of full scale`;
  document.getElementById('voltSub').textContent = `${(d.voltage / 5 * 100).toFixed(1)}% of Vcc`;
  document.getElementById('ohmsSub').textContent =
    d.ldr_ohms >= 999999 ? 'No light detected' : `${Math.round(d.ldr_ohms).toLocaleString()} Ω`;
  document.getElementById('luxSub').textContent  = `Sample #${samples}`;
  document.getElementById('uptimeSub').textContent = `Uptime: ${fmtUptime(d.uptime)}  |  Samples: ${samples}`;

  // Light state + alert
  const stateText = document.getElementById('stateText');
  const statePill = document.getElementById('statePill');
  const alertBar  = document.getElementById('alertBar');

  if (lux > 200) {
    stateText.textContent = 'Bright';
    statePill.textContent = 'BRIGHT LIGHT';
    statePill.className   = 'state-pill pill-bright';
    alertBar.className    = 'alert-bar alert-normal';
    alertBar.textContent  = `⬤  BRIGHT — ${lux.toFixed(0)} lux, good ambient light`;
  } else if (lux >= 50) {
    stateText.textContent = 'Dim';
    statePill.textContent = 'LOW LIGHT';
    statePill.className   = 'state-pill pill-dim';
    alertBar.className    = 'alert-bar alert-bright';
    alertBar.textContent  = `⚠  DIM — ${lux.toFixed(0)} lux, reduced visibility`;
  } else {
    stateText.textContent = 'Dark';
    statePill.textContent = 'VERY DARK';
    statePill.className   = 'state-pill pill-dark';
    alertBar.className    = 'alert-bar alert-dark';
    alertBar.textContent  = `⬤  DARK — ${lux.toFixed(0)} lux, near darkness`;
  }

  // LED glow bulb (brighter = more lux)
  const glow = Math.min(lux / 1000, 1);
  const bulb = document.getElementById('ledBulb');
  bulb.style.background   = `rgba(255,245,180,${0.05 + glow * 0.9})`;
  bulb.style.boxShadow    = `0 0 ${8+glow*50}px rgba(255,240,120,${0.15+glow*0.7}),
                              0 0 ${20+glow*90}px rgba(255,220,80,${0.1+glow*0.5}),
                              inset 0 0 20px rgba(255,255,255,.1)`;
  bulb.style.borderColor  = glow > 0.05 ? '#ffd166' : '#4a6080';

  // Chart
  pushChart(ts, lux, parseFloat(d.voltage), d.raw);

  // Log
  const log  = document.getElementById('logBox');
  const line = document.createElement('div');
  line.className = 'log-line';
  line.innerHTML = `<span>${ts}</span>  raw=${String(d.raw).padStart(4)}  `
                 + `volt=${parseFloat(d.voltage).toFixed(3)}V  `
                 + `ohms=${d.ldr_ohms >= 999999 ? '    inf' : String(Math.round(d.ldr_ohms)).padStart(7)}  `
                 + `lux=${lux.toFixed(1)}`;
  log.appendChild(line);
  if (log.children.length > 31) log.removeChild(log.children[1]);
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

# ── Serial reader ─────────────────────────────────────────────────────────────
def serial_reader(port: str):
    print(f"[serial] Connecting to {port} @ {BAUD_RATE} baud …")
    while True:
        try:
            with serial.Serial(port, BAUD_RATE, timeout=2) as ser:
                print("[serial] Connected ✓")
                ser.reset_input_buffer()
                while True:
                    raw_line = ser.readline().decode("utf-8", errors="ignore").strip()
                    if not raw_line:
                        continue
                    try:
                        # Expected: {"raw":512,"voltage":2.500,"ldr_ohms":9765,"lux":51.2,"uptime":4321}
                        data = json.loads(raw_line)
                        required = {"raw", "voltage", "ldr_ohms", "lux", "uptime"}
                        if not required.issubset(data.keys()):
                            print(f"[serial] incomplete packet: {raw_line}")
                            continue
                        data["timestamp"] = datetime.now().isoformat()
                        history.append(data)
                        socketio.emit("sensor_data", data)
                    except json.JSONDecodeError:
                        print(f"[serial] non-JSON line: {raw_line}")

        except serial.SerialException as e:
            print(f"[serial] Error: {e} — retrying in 3 s …")
            time.sleep(3)

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arduino LDR IoT Dashboard")
    parser.add_argument("--port",    default="COM3",  help="Serial port (e.g. COM3 or /dev/ttyACM0)")
    parser.add_argument("--host",    default="0.0.0.0")
    parser.add_argument("--webport", default=5000, type=int)
    args = parser.parse_args()

    t = threading.Thread(target=serial_reader, args=(args.port,), daemon=True)
    t.start()

    print(f"[web] Dashboard → http://localhost:{args.webport}")
    socketio.run(app, host=args.host, port=args.webport, debug=False)