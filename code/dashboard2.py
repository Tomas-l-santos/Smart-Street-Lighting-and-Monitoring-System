<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Smart Street Light Dashboard</title>
  <style>
    :root{
      --bg:#0f172a;
      --panel:#1e293b;
      --panel2:#334155;
      --text:#f8fafc;
      --muted:#cbd5e1;
      --green:#22c55e;
      --yellow:#f59e0b;
      --red:#ef4444;
      --blue:#38bdf8;
      --border:#475569;
      --shadow:0 8px 24px rgba(0,0,0,0.25);
      --radius:16px;
    }

    *{
      box-sizing:border-box;
      margin:0;
      padding:0;
      font-family:Arial, Helvetica, sans-serif;
    }

    body{
      background:linear-gradient(135deg,#020617,#0f172a,#1e293b);
      color:var(--text);
      min-height:100vh;
      padding:24px;
    }

    .container{
      max-width:1100px;
      margin:0 auto;
    }

    .title{
      margin-bottom:20px;
    }

    .title h1{
      font-size:2rem;
      margin-bottom:6px;
    }

    .title p{
      color:var(--muted);
      font-size:1rem;
    }

    .grid{
      display:grid;
      grid-template-columns:repeat(auto-fit, minmax(260px, 1fr));
      gap:18px;
      margin-bottom:20px;
    }

    .card{
      background:rgba(30,41,59,0.92);
      border:1px solid var(--border);
      border-radius:var(--radius);
      padding:20px;
      box-shadow:var(--shadow);
    }

    .card h2{
      font-size:1rem;
      color:var(--muted);
      margin-bottom:12px;
    }

    .big-value{
      font-size:2.2rem;
      font-weight:700;
    }

    .sub{
      margin-top:8px;
      color:var(--muted);
      font-size:0.95rem;
    }

    .status-pill{
      display:inline-block;
      margin-top:10px;
      padding:8px 14px;
      border-radius:999px;
      font-weight:700;
      font-size:0.95rem;
    }

    .status-bright{
      background:rgba(34,197,94,0.15);
      color:var(--green);
      border:1px solid rgba(34,197,94,0.45);
    }

    .status-dim{
      background:rgba(245,158,11,0.15);
      color:var(--yellow);
      border:1px solid rgba(245,158,11,0.45);
    }

    .status-dark{
      background:rgba(239,68,68,0.15);
      color:#fca5a5;
      border:1px solid rgba(239,68,68,0.45);
    }

    .bar-wrap{
      margin-top:14px;
      background:#0f172a;
      border-radius:999px;
      height:18px;
      overflow:hidden;
      border:1px solid var(--border);
    }

    .bar{
      height:100%;
      width:0%;
      background:linear-gradient(90deg,var(--blue),#60a5fa);
      transition:width 0.25s ease;
    }

    .led-visual-wrap{
      display:flex;
      align-items:center;
      justify-content:center;
      min-height:180px;
    }

    .led-bulb{
      width:110px;
      height:110px;
      border-radius:50%;
      background:#111827;
      border:3px solid #64748b;
      box-shadow:inset 0 0 20px rgba(255,255,255,0.05);
      transition:all 0.25s ease;
    }

    .section{
      margin-top:20px;
    }

    .logic-table{
      width:100%;
      border-collapse:collapse;
      overflow:hidden;
      border-radius:14px;
    }

    .logic-table th,
    .logic-table td{
      padding:14px;
      text-align:left;
      border-bottom:1px solid var(--border);
      background:rgba(30,41,59,0.92);
    }

    .logic-table th{
      color:var(--muted);
      font-size:0.95rem;
    }

    .controls{
      display:flex;
      flex-direction:column;
      gap:12px;
    }

    .controls label{
      font-weight:700;
      color:var(--muted);
    }

    input[type="range"]{
      width:100%;
    }

    .small-note{
      color:var(--muted);
      font-size:0.92rem;
      margin-top:10px;
      line-height:1.5;
    }

    .pin-box{
      display:flex;
      gap:10px;
      flex-wrap:wrap;
      margin-top:10px;
    }

    .pin{
      padding:8px 12px;
      border-radius:10px;
      background:#0f172a;
      border:1px solid var(--border);
      color:var(--text);
      font-weight:700;
    }

    @media (max-width:700px){
      .title h1{
        font-size:1.6rem;
      }
      .big-value{
        font-size:1.8rem;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="title">
      <h1>Smart Street Light Dashboard</h1>
      <p>Dashboard matched to the Arduino Uno script for the photoresistor and PWM LED brightness control.</p>
    </div>

    <div class="grid">
      <div class="card">
        <h2>Photoresistor Reading</h2>
        <div class="big-value" id="ldrValue">900</div>
        <div class="sub">Analog input from <strong>A1</strong></div>
        <div class="bar-wrap">
          <div class="bar" id="ldrBar"></div>
        </div>
      </div>

      <div class="card">
        <h2>LED Brightness</h2>
        <div class="big-value" id="brightnessValue">0</div>
        <div class="sub">PWM output on <strong>Pin 5</strong> (0–255)</div>
        <div class="bar-wrap">
          <div class="bar" id="brightnessBar"></div>
        </div>
      </div>

      <div class="card">
        <h2>Lighting Status</h2>
        <div class="big-value" id="statusText">Bright</div>
        <div class="status-pill status-bright" id="statusPill">LED OFF</div>
        <div class="sub">Uses the same thresholds as the Arduino code</div>
      </div>

      <div class="card">
        <h2>System Pins</h2>
        <div class="pin-box">
          <div class="pin">LDR: A1</div>
          <div class="pin">LED: 5</div>
          <div class="pin">Bright: 900</div>
          <div class="pin">Dark Start: 400</div>
          <div class="pin">Very Dark: 100</div>
        </div>
      </div>
    </div>

    <div class="grid">
      <div class="card">
        <h2>LED Visual Output</h2>
        <div class="led-visual-wrap">
          <div class="led-bulb" id="ledBulb"></div>
        </div>
        <div class="small-note">
          This visual circle changes intensity to represent the brightness value being sent to the LED using PWM.
        </div>
      </div>

      <div class="card">
        <h2>Manual Sensor Test</h2>
        <div class="controls">
          <label for="ldrSlider">Simulated LDR Value: <span id="sliderOutput">900</span></label>
          <input type="range" id="ldrSlider" min="0" max="1023" value="900">
        </div>
        <div class="small-note">
          Move the slider to simulate the photoresistor.  
          This follows the same logic as your Arduino script:
          above 400 = LED off, between 400 and 100 = gradual increase, 100 or below = maximum brightness.
        </div>
      </div>
    </div>

    <div class="section">
      <table class="logic-table">
        <thead>
          <tr>
            <th>LDR Range</th>
            <th>Condition</th>
            <th>LED Behaviour</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>400 and above</td>
            <td>Bright environment</td>
            <td>LED OFF (brightness = 0)</td>
          </tr>
          <tr>
            <td>101 to 399</td>
            <td>Medium / getting dark</td>
            <td>LED gradually increases using map()</td>
          </tr>
          <tr>
            <td>100 or below</td>
            <td>Very dark</td>
            <td>LED at maximum brightness (255)</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <script>
    const darkStart = 400;
    const veryDark = 100;

    const ldrSlider = document.getElementById("ldrSlider");
    const sliderOutput = document.getElementById("sliderOutput");

    const ldrValueEl = document.getElementById("ldrValue");
    const brightnessValueEl = document.getElementById("brightnessValue");
    const statusTextEl = document.getElementById("statusText");
    const statusPillEl = document.getElementById("statusPill");
    const ldrBar = document.getElementById("ldrBar");
    const brightnessBar = document.getElementById("brightnessBar");
    const ledBulb = document.getElementById("ledBulb");

    function mapValue(x, inMin, inMax, outMin, outMax) {
      return Math.round((x - inMin) * (outMax - outMin) / (inMax - inMin) + outMin);
    }

    function updateDashboard(ldrValue) {
      let brightness = 0;
      let statusText = "";
      let pillText = "";
      let pillClass = "";

      if (ldrValue >= darkStart) {
        brightness = 0;
        statusText = "Bright";
        pillText = "LED OFF";
        pillClass = "status-bright";
      } else if (ldrValue < darkStart && ldrValue > veryDark) {
        brightness = mapValue(ldrValue, darkStart, veryDark, 0, 255);
        statusText = "Getting Dark";
        pillText = "LED DIMMING UP";
        pillClass = "status-dim";
      } else if (ldrValue <= veryDark) {
        brightness = 255;
        statusText = "Very Dark";
        pillText = "MAX BRIGHTNESS";
        pillClass = "status-dark";
      }

      ldrValueEl.textContent = ldrValue;
      brightnessValueEl.textContent = brightness;
      statusTextEl.textContent = statusText;
      sliderOutput.textContent = ldrValue;

      statusPillEl.textContent = pillText;
      statusPillEl.className = "status-pill " + pillClass;

      ldrBar.style.width = `${(ldrValue / 1023) * 100}%`;
      brightnessBar.style.width = `${(brightness / 255) * 100}%`;

      const glow = brightness / 255;
      ledBulb.style.background = `rgba(255, 255, 180, ${0.08 + glow})`;
      ledBulb.style.boxShadow = `
        0 0 ${10 + glow * 50}px rgba(255, 255, 150, ${0.2 + glow * 0.8}),
        0 0 ${20 + glow * 80}px rgba(255, 230, 120, ${0.1 + glow * 0.6}),
        inset 0 0 20px rgba(255,255,255,0.15)
      `;
      ledBulb.style.borderColor = glow > 0 ? "#facc15" : "#64748b";
    }

    ldrSlider.addEventListener("input", () => {
      updateDashboard(parseInt(ldrSlider.value));
    });

    updateDashboard(parseInt(ldrSlider.value));
  </script>
</body>
</html>