# 🧠 PulseCare AI Agent  
### AI-Native Health Anomaly Detection & Natural Language Query Engine on AlloyDB

---

## 🚀 Overview

PulseCare AI is an AI-native health intelligence system built on **AlloyDB for PostgreSQL** that enables clinicians to query patient anomalies using natural language.

It transforms raw healthcare telemetry into meaningful insights using:

- Natural Language → SQL conversion  
- Semantic search using vector embeddings  
- In-database AI reasoning using AlloyDB (`embedding()` + `ai.if()`)

---

## 🎯 Problem Statement

Modern healthcare IoT systems generate massive volumes of telemetry data, where critical anomalies are often buried within noise.

Traditional databases:
- Cannot understand natural language  
- Require complex SQL queries  
- Lack semantic and contextual reasoning  

👉 Result: Delayed insights and slower clinical decisions  

---

## 💡 Solution

PulseCare AI introduces:

> 💥 **"Intelligence at the Data Layer"**

- Query health data using plain English  
- Detect anomalies using semantic similarity  
- Perform AI reasoning directly inside AlloyDB  

---

## 🏗️ Architecture

### 🔹 Data Pipeline
