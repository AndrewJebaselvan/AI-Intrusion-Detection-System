# 🚨 AI-Based Intrusion Detection System with RAG

An intelligent, real-time intrusion detection system that combines **Computer Vision**, **Edge AI**, and **Retrieval-Augmented Generation (RAG)** to detect, analyze, and explain security threats from video streams.

---

## 🔥 Overview

This project detects unauthorized intrusions in restricted zones using deep learning and provides **AI-driven explanations** of events.

It supports:
- 🎥 Live camera feed
- 📁 Recorded video upload
- ⚠️ Real-time threat scoring
- 🤖 Natural language querying of events

---

## 🧠 Architecture


Video Input → YOLOv8 Detection → Threat Logic → Event Logs → LlamaIndex → AI Response


---

## ⚙️ Features

- ✅ Real-time human detection using YOLOv8  
- ✅ Restricted zone monitoring  
- ✅ Persistence-based intrusion confirmation  
- ✅ Dynamic threat scoring (LOW / MEDIUM / HIGH)  
- ✅ Event logging system  
- ✅ Upload and analyze recorded videos  
- ✅ AI query system (ask questions about events)  
- ✅ Fully offline (no external APIs required)  

---

## 🧠 Core Algorithm: Context-Aware Threat Scoring

Unlike basic detection systems, this project implements a custom **context-aware intrusion detection algorithm** that combines detection confidence, temporal persistence, and spatial awareness.

---

### 🔹 Step 1: Object Detection

- YOLOv8 detects persons in each frame  
- Bounding boxes are extracted  

---

### 🔹 Step 2: Zone Intersection Logic

Each detected person is checked against a predefined **restricted zone**:


if bounding_box overlaps restricted_zone → potential intrusion


---

### 🔹 Step 3: Temporal Persistence

To avoid false positives, intrusion is confirmed only if a person remains inside the zone for a minimum number of frames:


if inside_frames >= threshold → intrusion_confirmed


---

### 🔹 Step 4: Threat Score Calculation

A custom scoring function evaluates severity:


Threat Score = (Confidence × 40) + (Persistence Ratio × 40) + (Zone Criticality × 20)


Where:
- Confidence → YOLO detection confidence  
- Persistence Ratio → time spent inside zone  
- Zone Criticality → importance of region  

---

### 🔹 Step 5: Threat Classification


Score ≥ 75 → HIGH
Score ≥ 40 → MEDIUM
Else → LOW


---

### 🔹 Step 6: IoT Trigger Logic

High-risk events trigger alerts:


if score ≥ threshold → trigger alert system


---

### 🔹 Step 7: Logging & AI Analysis

- Events are stored in logs  
- Retrieved using LlamaIndex  
- Processed using hybrid AI (rule-based + transformer model)  

---

## ⚡ Key Innovation

- Combines **spatial + temporal intelligence**  
- Reduces false positives using persistence logic  
- Provides **explainable threat scoring**  
- Enables **AI-driven querying of events**  

---

## 🧰 Tech Stack

- Python  
- Flask (Backend API)  
- OpenCV (Video Processing)  
- YOLOv8 (Object Detection)  
- LlamaIndex (Retrieval System)  
- Hugging Face Transformers (Local AI Model)  

---

## 📸 Screenshots

> *(Add screenshots here for better impact)*  
- Dashboard  
- Detection output  
- AI query results  

---

## 🚀 Getting Started

### 1️⃣ Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/AI-Intrusion-Detection-System.git
cd AI-Intrusion-Detection-System
2️⃣ Create virtual environment
python -m venv virt310
.\virt310\Scripts\activate
3️⃣ Install dependencies
pip install flask opencv-python ultralytics numpy==1.26.4 llama-index transformers torch sentence-transformers faiss-cpu llama-index-embeddings-huggingface
4️⃣ Run the application
python app.py
🧪 Usage
🎥 Live Detection
Connect camera stream
System detects intrusion in real-time
📁 Upload Video
Upload recorded video
System processes it like live feed
🤖 AI Query

Ask questions like:

“What intrusion happened?”
“Summarize events”
“Was it high threat?”
🧠 AI Layer (RAG)
Logs are indexed using LlamaIndex
Relevant context is retrieved
Hybrid approach:
Rule-based reasoning (for accuracy)
Transformer model (for flexibility)
🎯 Key Highlights
⚡ Real-time inference pipeline
🧠 Hybrid AI (rule-based + LLM)
🔒 Fully offline system (no API dependency)
🧩 Modular architecture
🚧 Future Improvements
Multi-object tracking
Face recognition
IoT alert integration
Cloud deployment
👨‍💻 Author

P. Jeba Selvan Andrew
AI & Data Science Engineer