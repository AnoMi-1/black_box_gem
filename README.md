## 🚀 Quick Start & Local Deployment

Follow these steps to initialize the virtual hardware interfaces and spin up the local AI triage engine before running the dashboard.

### 1. System Requirements & Hardware Simulation
The Black Box Gem relies on Linux kernel modules to simulate real vehicle telemetry data over a Controller Area Network (CAN bus). 

Make the setup script executable and run it to initialize `vcan0` and boot the local server:
```bash
chmod +x setup_can.sh
./setup_can.sh
