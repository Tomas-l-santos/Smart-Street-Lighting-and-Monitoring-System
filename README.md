# Arduino IoT Light Sensor Dashboard

Real-time monitoring of a photodiode connected to an Arduino Nano,
displayed on a live web dashboard via Python + Flask-SocketIO.

---

## Hardware Setup

### Components
| Component       | Qty |
|-----------------|-----|
| Arduino Nano     | 1   |
| Photodiode      | 1   |
| LED (any colour)| 1   |
| Resistor 10 kΩ  | 1   | ← pull-down for photodiode
| Resistor 220 Ω  | 1   | ← current-limit for LED
| Breadboard + wires | — |

### Wiring

```
Photodiode (anode) ──── A0 (Arduino)
Photodiode (cathode) ── GND
10 kΩ resistor ──────── A0 → GND   (pull-down)

LED (anode) ─── 220 Ω ─ D7 (Arduino)
LED (cathode) ──────────  GND
```

The LED on D7 blinks with every reading so you can visually verify
the loop is running. The onboard LED (D13) stays ON as a power indicator.

---

## Software Setup

### 1 — Upload the Arduino sketch

Open `sensor.ino` in the Arduino IDE and upload it to the Uno.
Open the Serial Monitor at 9600 baud to confirm JSON output like:

```json
{"raw":512,"voltage":2.500,"lux":500.3,"uptime":4321}
```

### 2 — Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3 — Run the dashboard

**Windows:**
```bash
python dashboard.py --port COM3
```

**Linux / Mac:**
```bash
python dashboard.py --port /dev/ttyACM0
```

Then open **http://localhost:5000** in your browser.

---

## Dashboard Features

| Panel          | Description                              |
|----------------|------------------------------------------|
| Illuminance    | Estimated lux with live gauge bar        |
| Voltage        | ADC voltage (0–5 V) with % of Vcc        |
| ADC Raw        | 10-bit value (0–1023) with gauge         |
| Uptime         | Arduino millis() formatted as hh:mm:ss   |
| Live Chart     | 60-second rolling Lux + Voltage history  |
| Alert Bar      | Colour-coded light-level status          |
| Serial Log     | Last 30 raw readings with timestamps     |

---

## IoT Communication Protocol

- **Transport:** USB Serial (UART) at 9600 baud
- **Format:** JSON per line — easy to extend or swap for MQTT/BLE
- **Push:** Flask-SocketIO WebSocket pushes each reading to all browser clients in < 5 ms

---

## Extending the Project

- **MQTT:** Replace the `socketio.emit` call with `paho-mqtt` publish to broker
- **ThingSpeak:** POST to `https://api.thingspeak.com/update` with the field values
- **Grafana:** Write to InfluxDB in the serial thread; connect Grafana as a data source
- **Multiple sensors:** Add more `analogRead()` lines and extra JSON fields — the dashboard auto-scales
