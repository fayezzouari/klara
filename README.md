---
title: AI Copilot for Renewable Energy Data Rooms
emoji: ⚡
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: "4.16.0"
app_file: app.py
pinned: false
---

# ⚡ AI Copilot for Renewable Energy Data Rooms

This project is a smart assistant designed to automate document analysis in renewable energy data rooms. Developers often face a flood of critical documents — leases, permits, interconnection agreements — stored in PDFs or spreadsheets. Manually parsing and transferring relevant data into checklists or reports is slow, error-prone, and costly.

This AI Copilot streamlines that process by enabling:
- 📄 **Bulk PDF uploads**  
- 🔍 **Natural language queries on document content**  
- 🧾 **Reference-backed answers with page numbers and source quotes**  
- ✅ **Checklist auto-population with traceable sources**

---

## 🚀 Key Benefits

- **Saves time** by automating tedious document parsing  
- **Reduces errors** in due diligence workflows  
- **Boosts trust** with answers linked to exact document locations  
- **Fits custom workflows** by supportina# ⚡ AI Copilot for Renewable Energy Data Rooms

> A smart Gradio-powered assistant for analyzing critical documents like leases, permits, and interconnection agreements in renewable energy projects.

![Hugging Face Space](https://img.shields.io/badge/🤖%20AI%20Copilot-Gradio%20App-blue?logo=gradio)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

---

## 🔎 Overview

This AI Copilot is designed to help developers and analysts working in renewable energy data rooms quickly extract key information from large volumes of PDF and spreadsheet files. It streamlines due diligence by automating:

- 📄 **Bulk PDF upload and parsing**  
- 💬 **Natural language question answering on document content**  
- 📌 **Answers with references, page numbers, and source quotes**  
- ✅ **Auto-filling due diligence checklists (WIP)**

---

## 🚀 Demo

Try it out directly in the [Hugging Face Space](https://huggingface.co/spaces/fayezzouari/klara).

---
title: AI Copilot for Renewable Energy Data Rooms
emoji: ⚡
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: "4.16.0"
app_file: app.py
pinned: false
url: https://huggingface.co/spaces/fayezzouari/klara
---
---

## 🌟 Features

- ⏱ **Time-saving** document analysis  
- 🛡️ **Traceable** answers with inline source citations  
- 🧠 **LLM-powered** query understanding via LangChain and Groq  
- 🧩 **Plug-and-play** with your own checklists and workflows  

---

## 🧠 How It Works

1. **PDF Parsing** – Text and metadata extraction  
2. **Semantic Chunking** – Smart segmentation with `chonkie`  
3. **Vector Embedding** – Semantic storage via ChromaDB  
4. **LLM QA** – Natural language answers from Groq's LLMs via LangChain  
5. **Checklist Automation (WIP)** – Extract and match info to project-specific checklists  

---

## 🛠️ Tech Stack

| Component              | Role                                 |
|------------------------|--------------------------------------|
| 🖼️ Gradio              | Web UI for interaction               |
| 🧱 ChromaDB             | Vector store for fast semantic search |
| 🧠 LangChain + Groq API | LLM query engine                    |
| 📄 PyPDF               | PDF extraction                       |
| 🔍 Sentence Transformers | Embedding generation               |
| 🧩 Chonkie             | Custom chunking utility              |

---

## ⚙️ Setup & Usage

### 🔧 Installation

```bash
git clone https://github.com/fayezzouari/klara.git
cd klara
pip install -r requirements.txt
g organization-specific checklists

---

## 🧠 How It Works

1. **PDF Parsing**: Extracts raw text and metadata  
2. **Semantic Chunking**: Breaks text into meaningful, queryable segments  
3. **Vector Embedding & Search**: Stores segments in ChromaDB for fast retrieval  
4. **Question Answering**: Uses an LLM (via LangChain) to provide accurate, sourced answers  
5. **Checklist Filling (WIP)**: Matches document content to your custom due diligence checklists  

---

## 💻 Tech Stack

- **Gradio** – Simple web UI for uploading and querying  
- **LangChain + GROQ API** – Language model orchestration  
- **ChromaDB** – Vector storage for semantic search  
- **Chonkie** – Smart chunking of documents  
- **Sentence Transformers** – Embedding generation  
- **PyPDF** – PDF parsing

---

## 🚀 Getting Started

### 1. Clone & Install
```bash
git clone https://github.com/fayezzouari/klara.git
cd KLARA
pip install -r requirements.txt
```

### 2. Configure
Add your API key in a `.env` file:
```env
GROQ_API_KEY=your_api_key_here
```

### 3. Run the App
```bash
python app.py
```
Access the web interface at `http://127.0.0.1:7860`

---

## 📂 How to Use

### Upload & Process Documents
1. Upload a PDF  
2. Click **"Process PDF"** – the system prepares it for querying  

### Ask Questions
1. Switch to the **Query** tab  
2. Ask a question in plain English  
3. Get an answer with cited sources  

---

## 🛠 Configuration Highlights

Change behavior via `config.py`:

| Setting | Description |
|--------|-------------|
| `DEFAULT_LLM_MODEL` | Model used for answering queries |
| `DEFAULT_CHUNK_SIZE` | Max size per semantic segment |
| `DEFAULT_RESULTS_COUNT` | Number of segments retrieved per query |

---

## 🧪 Development & Debugging

- Key modules: `DocumentProcessor`, `DocumentSplitter`  
- Debug logs shown in terminal  
- Make sure `.env` contains a valid `GROQ_API_KEY`

---

## 📄 License

MIT License – feel free to use and adapt.

---

## ✉️ Contact

For support or collaboration:  
📧 `iyed.mdimegh@insat.ucar.tn`
📧 `fayez.zouari@insat.ucar.tn`

---

Would you like a **custom badge** or visual to add to the README for presentation or GitHub?