# 💎 Black Box Gem
## Local Intelligence. Global Resilience.

> **"When they can't call, we have already answered."**

Black Box Gem is an edge-native accident triage and response system designed to bridges the gap between critical vehicle collisions and emergency medical services (EMS). Operating entirely locally at the network edge, the system ingests live vehicle telemetry, applies privacy-preserving computer vision to anonymize sensitive data, and leverages local LLM reasoning to generate actionable, instant crash severity triage reports—even when cloud connectivity is completely severed.

---

## 📺 Project Overview

In a severe vehicle collision, every second counts. Traditional emergency response relies on cellular networks, manual voice calls, or cloud-dependent crash detection systems. If the vehicle spins out into a dead zone or a network tower fails, communication drops completely.

**Black Box Gem solves this by moving intelligence to the vehicle edge:**
1. **Telemetry Ingestion:** Continuously monitors vehicle health, airbag deployment, and collision forces over the vehicle's internal CAN bus.
2. **Privacy-First Processing:** Dynamically blurs personally identifiable information (PII) such as license plates from the dashcam feed at the physical hardware layer.
3. **Local AI Reasoning:** Processes the multi-modal crash footprint locally using a lightweight, optimized LLM engine to deduce injury risk indicators.
4. **Resilient Broadcast:** Prepares compressed, hyper-dense triage payloads optimized for low-bandwidth mesh networks, satellite relays, or standard cellular channels once active.

---

## 🛠️ Tech Stack & Open Source Attributions

Black Box Gem stands on the shoulders of cutting-edge open-source projects and models:

* **Core AI Reasoning Engine:** Google Gemma (Running locally via the optimized `gemma:4b` profile)
* **Local Inference Framework:** [Ollama](https://ollama.com/) 
* **Operator Interface:** Streamlit Dashboard
* **Telemetry Simulation Sockets:** Linux SocketCAN Architecture (`vcan` kernel module)
* **Privacy & Anonymization Pipeline:** [License Plate Recognizer by MKgoud](https://huggingface.co/MKgoud/License-Plate-Recognizer/tree/main) (Used to isolate and mask vehicle identifiers at the ingestion point)

## 🏗️ System Architecture

```text
[Vehicle Sensors] ──(CAN Bus Data)──> [SocketCAN: vcan0] ──┐
                                                           ├─> [Streamlit Engine] ─> [Gemma 3 Triage Prompt] ─> [EMS Operator UI]
[Dashcam Feed]    ──(Raw Video)─────> [MKgoud PII Blur] ───┘
```

---

## 🚀 Quick Start & Local Deployment

Follow these steps to initialize the virtual hardware infrastructure and spin up the local AI triage engine before launching your dashboard.

### 1. Prerequisites

This system utilizes Linux-native kernel modules (`vcan`) to simulate vehicle network routing. Ensure you are running a Linux environment (or an architecture capable of utilizing socket-level network bridges).

### 2. Automated Environment Initialization

We have bundled the hardware network configuration, Ollama backend management, and model orchestration into a unified initialization script.

Make the setup script executable and run it:

```bash
chmod +x setup.sh
./setup.sh

```
---

> ⚙️ **What `setup.sh` handles under the hood:**
> * Authenticates `sudo` rights to load the virtual CAN network modules (`modprobe vcan`).
> * Configures and initializes the local network socket interface (`vcan0`).
> * Confirms or launches the background local `ollama serve` instance daemon.
> * Verifies that the optimized `gemma:4b` model weights are cleanly pulled and cached locally.
> 
> 

### 3. Launching the Command Center

Once the initialization script signals that your network interfaces and models are green, launch the main monitoring control dashboard:

```bash
streamlit run app.py

```

Open the local network portal provided in your terminal (usually `http://localhost:8501`) to interact with the crash simulation control center.

---

## 📄 License

This repository is licensed under the **Apache License 2.0**. See the `LICENSE` file for more details.

*Note: Use of the underlying LLM architecture is independently governed by the Google Gemma Additional Terms of Use.*

