# Smart Street Lighting System

### Arduino Nano · Photodiode Sensor · Serial Communication · Python · Flask · Real-Time Dashboard

A real-time smart street lighting prototype that monitors ambient light using a photodiode sensor, automatically controls lighting based on environmental conditions, and displays live sensor data through a Python-powered web dashboard.

> **University of Greenwich — Sensors & Networks (ELEE1148)**  
> **Two-person engineering project · 2026**  
> **Result: 72% — First Class**

---

## Project Overview

Traditional street lighting can consume unnecessary energy when lights remain active regardless of environmental conditions.

This project explores a simple smart-lighting solution where ambient light is continuously monitored and used to automatically control a simulated street light.

The completed system combines:

- **Photodiode light sensing**
- **Arduino Nano sensor acquisition**
- **Threshold-based embedded control**
- **Six-LED light-level indicator**
- **Automatic street-light activation**
- **USB Serial / UART communication**
- **Python data processing**
- **Flask-SocketIO real-time communication**
- **Browser-based live dashboard**
- **Real-time graphs, statistics and system alerts**

The project demonstrates the complete data path from a **physical environmental sensor** to an **embedded control decision** and finally to **live software visualisation**.

---

## System Architecture

```text
                   AMBIENT LIGHT
                        │
                        ▼
                ┌────────────────┐
                │   Photodiode   │
                │  Light Sensor  │
                └───────┬────────┘
                        │
                 Analogue Reading
                        │
                        ▼
                ┌────────────────┐
                │  Arduino Nano  │
                │      A1        │
                └───────┬────────┘
                        │
             ┌──────────┴──────────┐
             │                     │
             ▼                     ▼
    Threshold Processing      Serial Output
             │                 9600 Baud
      ┌──────┴──────┐              │
      │             │              ▼
      ▼             ▼        ┌──────────────┐
 Six-LED Light   Main LED     │    Python    │
 Level Display   D7 Control   │   PySerial   │
                              └──────┬───────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │    Flask +   │
                              │ Flask-SocketIO│
                              └──────┬───────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │  Real-Time   │
                              │ Web Dashboard│
                              └──────────────┘
```

The Arduino performs sensor acquisition and lighting control, while Python handles serial communication, data processing and dashboard visualisation.

---

# Hardware

## Components

| Component | Purpose |
|---|---|
| Arduino Nano | Main embedded controller |
| Photodiode / light sensor | Measures ambient light |
| 6 × LEDs | Physical light-level indicator |
| 1 × Large LED | Simulated street light |
| Resistors | LED current limiting / sensor circuit |
| Breadboard | Prototype circuit |
| Jumper wires | Electrical connections |
| USB cable | Arduino power and serial communication |

---

## Pin Configuration

| Component | Arduino Connection |
|---|---:|
| Photodiode sensor | **A1** |
| Indicator LED 1 | **D13** |
| Indicator LED 2 | **D2** |
| Indicator LED 3 | **D3** |
| Indicator LED 4 | **D4** |
| Indicator LED 5 | **D5** |
| Indicator LED 6 | **D6** |
| Main street-light LED | **D7** |
| Arduino → Computer | **USB Serial @ 9600 baud** |

---

# Embedded Control Logic

The Arduino continuously reads the analogue signal from the photodiode.

The Arduino's analogue-to-digital converter represents the sensor signal as a value between:

```text
0 ─────────────────────────────── 1023
Darker                              Brighter
```

The system was calibrated so that increasing ambient brightness produces higher sensor readings.

A set of thresholds converts those readings into physical lighting behaviour.

---

## LED Light-Level Indicator

The six LEDs create a physical representation of the measured ambient-light level.

```text
BRIGHT ENVIRONMENT

Sensor > 800

○ ○ ○ ○ ○ ○
Street Light: OFF


↓ Environment becomes darker ↓


651 – 800

● ○ ○ ○ ○ ○
Street Light: OFF


501 – 650

● ● ○ ○ ○ ○
Street Light: OFF


351 – 500

● ● ● ○ ○ ○
Street Light: ON


251 – 350

● ● ● ● ○ ○
Street Light: ON


151 – 250

● ● ● ● ● ○
Street Light: ON


≤ 150

● ● ● ● ● ●
Street Light: ON

DARK ENVIRONMENT
```

As the environment becomes darker, progressively more LEDs illuminate.

This provides an immediate physical representation of the sensor reading without requiring the dashboard.

---

## Lighting Thresholds

| Sensor Value | Light Condition | Indicator LEDs | Street Light |
|---:|---|---:|:---:|
| `> 800` | Very Bright | 0 | OFF |
| `651 – 800` | Bright | 1 | OFF |
| `501 – 650` | Moderate | 2 | OFF |
| `351 – 500` | Low Light | 3 | ON |
| `251 – 350` | Dark | 4 | ON |
| `151 – 250` | Very Dark | 5 | ON |
| `≤ 150` | Extremely Dark | 6 | ON |

The simulated street light switches **ON when the sensor value reaches 500 or below**.

---

# Serial Communication

The Arduino transfers sensor readings to the computer through **USB serial communication at 9600 baud**.

Example output:

```text
Sensor Value: 823
Sensor Value: 716
Sensor Value: 592
Sensor Value: 438
Sensor Value: 287
Sensor Value: 128
```

The Python application continuously monitors the serial port and extracts each sensor reading.

The communication path is therefore:

```text
Arduino
   │
   │ USB Serial / UART
   │ 9600 baud
   ▼
PySerial
   │
   ▼
Python Application
   │
   ▼
Flask-SocketIO
   │
   ▼
Web Browser
```

This provides a simple and reliable wired communication system between the embedded hardware and monitoring application.

---

# Real-Time Dashboard

The dashboard was developed using:

- **Python**
- **PySerial**
- **Flask**
- **Flask-SocketIO**
- **HTML**
- **CSS**
- **JavaScript**
- **Chart.js**

The Python application receives the Arduino readings and processes them before sending live updates to the browser.

---

## Dashboard Features

| Feature | Description |
|---|---|
| Live Sensor Reading | Displays the latest photodiode value |
| Light-Level Classification | Converts the sensor value into an understandable lighting condition |
| Street-Light Status | Shows whether the main LED should be ON or OFF |
| LED Status | Displays the current indicator LED state |
| Alert System | Provides visual feedback based on current lighting conditions |
| Live Graph | Plots changing sensor readings using Chart.js |
| Minimum Reading | Lowest reading within the current history |
| Maximum Reading | Highest reading within the current history |
| Average Reading | Mean value of recent sensor samples |
| Trend Detection | Indicates how the sensor reading is changing |
| Recent Samples | Displays recently received sensor readings |
| Rolling History | Stores up to 180 recent readings for visualisation |

The dashboard updates continuously while the Arduino is connected.

---

# Software Setup

## Requirements

Before running the project, ensure that you have:

- Python 3
- Arduino IDE
- A connected Arduino Nano
- The required Python packages

---

## 1. Upload the Arduino Program

Open the Arduino `.ino` file in the Arduino IDE.

Select:

```text
Board: Arduino Nano
```

Then select the COM port assigned to the Arduino and upload the program.

You can verify the Arduino output using the Serial Monitor at:

```text
9600 baud
```

You should see readings similar to:

```text
Sensor Value: 684
Sensor Value: 672
Sensor Value: 651
Sensor Value: 625
```

---

## 2. Install Python Dependencies

Open a terminal inside the project directory.

Install the required packages:

```bash
pip install flask flask-socketio pyserial
```

If the repository contains a `requirements.txt` file, you can instead use:

```bash
pip install -r requirements.txt
```

---

## 3. Identify the Arduino COM Port

On Windows, the Arduino may appear as:

```text
COM3
```

or:

```text
COM4
```

You can check this through:

```text
Arduino IDE → Tools → Port
```

---

## 4. Start the Dashboard

For example:

```bash
python dashboardNano.py --port COM3
```

Replace `COM3` with the port assigned to your Arduino.

---

## 5. Open the Web Dashboard

Once the Flask server starts, open the local address displayed in the terminal.

Typically:

```text
http://127.0.0.1:5000
```

The dashboard will begin updating when valid sensor readings are received from the Arduino.

---

# Data Flow

A single sensor measurement travels through the system as follows:

```text
1. Ambient light changes
            │
            ▼
2. Photodiode output changes
            │
            ▼
3. Arduino reads analogue input A1
            │
            ▼
4. Arduino evaluates lighting thresholds
            │
       ┌────┴────┐
       │         │
       ▼         ▼
5a. LEDs      5b. Sensor value
    update         sent over Serial
                       │
                       ▼
                6. Python receives data
                       │
                       ▼
                7. Data is processed
                       │
                       ▼
                8. Flask-SocketIO
                   pushes update
                       │
                       ▼
                9. Browser dashboard
                   updates in real time
```

---

# Testing and Calibration

Testing was carried out under several different lighting conditions.

These included:

- Direct bright light
- Normal room lighting
- Partially covering the photodiode
- Low-light conditions
- Fully covering the sensor

The tests were used to establish suitable threshold values and confirm that each part of the system responded correctly.

---

## Testing Process

The system was tested as a complete hardware/software chain.

### Sensor

The photodiode was exposed to different lighting conditions to verify that the analogue reading changed consistently.

### Arduino

Serial Monitor readings were checked to confirm that the Arduino was correctly sampling the sensor.

### LED Indicator

Each lighting threshold was tested to ensure the correct number of LEDs activated.

### Street-Light LED

The main LED was verified to switch on when the sensor entered the configured low-light range.

### Serial Communication

Arduino readings were compared against the values received by Python.

### Dashboard

The dashboard was monitored while lighting conditions changed to verify that graphs, statistics, alerts and status indicators updated correctly.

---

# Engineering Design Decisions

## Why use threshold-based lighting control?

Threshold control provides predictable and deterministic behaviour.

For a prototype system, this makes the lighting response:

- easy to calibrate;
- easy to test;
- easy to demonstrate; and
- easy to validate against sensor readings.

---

## Why use serial communication?

USB serial provides a reliable connection between the Arduino and computer without requiring additional networking hardware.

It allowed the project to focus on:

- sensor acquisition;
- embedded control;
- communication;
- software processing; and
- real-time visualisation.

---

## Why separate Arduino and Python processing?

The system separates responsibilities between the embedded device and computer.

### Arduino

Responsible for:

```text
Sensor acquisition
       +
Threshold processing
       +
Physical LED control
```

### Python

Responsible for:

```text
Serial reception
       +
Data processing
       +
Statistics
       +
Real-time dashboard
```

This architecture simplifies debugging and makes individual sections of the system easier to modify or extend.

---

## Why use Flask-SocketIO?

Traditional web pages would require repeated refreshing or polling to retrieve updated readings.

Flask-SocketIO allows new sensor data to be pushed to the browser as it becomes available.

This creates a smoother real-time monitoring experience.

---

# Project Limitations

Although the prototype successfully demonstrates the full sensor-to-dashboard workflow, several limitations remain.

### Fixed Thresholds

The current sensor thresholds were manually calibrated for the prototype environment.

Different sensor placements or lighting environments may require recalibration.

### Wired Communication

The Arduino currently communicates with the computer through USB.

This is reliable for the prototype but would not be practical for large-scale street-light deployment.

### Main LED Control

The main street-light LED is connected to **digital pin D7**.

D7 is not a PWM-capable pin on the Arduino Nano, meaning the current design uses:

```text
ON / OFF
```

control rather than continuously adjustable brightness.

### Temporary Dashboard Data

The dashboard focuses on real-time monitoring.

Long-term readings are not currently stored in a persistent database.

### Prototype Hardware

The breadboard-based circuit demonstrates the engineering concept but is not designed for outdoor deployment.

---

# Future Improvements

The project could be developed further by introducing:

### PWM Street-Light Control

Move the main LED to a PWM-capable pin.

This would allow:

```text
Very Bright → 0% lighting
Moderate    → Low brightness
Dark        → Medium brightness
Very Dark   → 100% brightness
```

instead of simple ON/OFF control.

### Wireless Communication

Replace USB serial with a network-enabled microcontroller such as an ESP32.

Communication could then use protocols such as:

```text
Wi-Fi
MQTT
HTTP
```

### Multiple Street Lights

Several sensor nodes could communicate with a central monitoring system.

```text
Street Light 1 ─┐
Street Light 2 ─┤
Street Light 3 ─┼──► Network ──► Central Dashboard
Street Light 4 ─┤
Street Light 5 ─┘
```

### Persistent Data Storage

Sensor readings could be stored in a database for:

- historical analysis;
- identifying lighting patterns;
- energy analysis;
- fault detection; and
- long-term monitoring.

### Motion or Traffic Detection

A PIR, ultrasonic or other suitable sensor could be added so lighting reacts to both:

```text
Ambient light
      +
Road / pedestrian activity
```

This could further reduce unnecessary energy usage.

### Energy Monitoring

Adding power measurement would allow the system to measure and compare energy consumption under different control strategies.

---

# My Contribution

**Tomás Loureiro Santos**

This project was developed as part of a two-person engineering team.

My primary responsibilities included:

- Setting up and calibrating the photodiode sensor
- Building and testing the Arduino-side hardware
- Programming Arduino sensor acquisition
- Developing the threshold-based LED control logic
- Implementing the six-LED light-level indicator
- Configuring the main street-light behaviour
- Testing sensor readings under different lighting conditions
- Verifying serial data produced by the Arduino
- Troubleshooting hardware and software integration
- Collaborating on the integration of the Arduino system with the real-time dashboard

Through the project, I gained practical experience working across both hardware and software rather than treating them as separate systems.

---

# Skills Demonstrated

This project demonstrates practical experience in:

### Embedded Systems

- Arduino programming
- Analogue sensor interfacing
- Digital I/O
- ADC readings
- Threshold control
- Hardware debugging

### Communication

- Serial communication
- UART fundamentals
- Hardware/software data transfer
- Real-time data streaming

### Python Development

- PySerial
- Data processing
- Flask
- Flask-SocketIO
- Application debugging

### Web Development

- HTML
- CSS
- JavaScript
- Chart.js
- Real-time dashboard interfaces

### Engineering

- Sensor calibration
- Prototype development
- System integration
- Hardware/software troubleshooting
- Testing
- Iterative development
- Engineering evaluation

---

# Project Outcome

The completed prototype successfully demonstrated an end-to-end smart lighting system:

```text
Physical Environment
        │
        ▼
     Sensor
        │
        ▼
     Arduino
        │
        ▼
Embedded Decision
        │
        ├──────────► Physical Lighting Control
        │
        ▼
Serial Communication
        │
        ▼
      Python
        │
        ▼
Real-Time Dashboard
```

The project demonstrates how **embedded hardware, communication systems and software applications can work together as a complete computer engineering system**.

---

# Result

### 72% — First Class

University of Greenwich  
**Sensors & Networks — ELEE1148**  
2026

---

# Author

**Tomás Loureiro Santos**
**Amr Assaf**

Computer Engineering  
University of Greenwich

GitHub: [Tomas-l-santos](https://github.com/Tomas-l-santos)
GitHub: [A9rlt](https://github.com/A9rlt)