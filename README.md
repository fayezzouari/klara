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
- **Fits custom workflows** by supporting organization-specific checklists

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
git clone <repository-url>
cd <repository-folder>
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