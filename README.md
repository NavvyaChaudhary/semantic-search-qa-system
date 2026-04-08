# Semantic Document Search & QA System

**Made by:** Navvya Chaudhary
**Program:** BTech CSE (Data Science & AI)
**Type:** Live Project

---

## What This Project Does

This is a document search system that actually understands what you're asking, not just what words you typed.

You upload a PDF, TXT, or Word file. You type a question. The system reads through your document and returns the most relevant sections — ranked by how closely they match the meaning of your question, not just whether they share the same keywords.

For example, if your document talks about "neural networks learning from labelled data" and you search for "how does supervised learning work", it will still find the right section. That's the difference between keyword search and semantic search.

---

## Tech Stack

| Layer | What I Used | Why |
|---|---|---|
| Frontend | Streamlit | Fast to build, runs in browser, pure Python |
| Backend API | Java (Spring Boot) | Acts as the REST middleware layer |
| NLP Engine | Python | All the actual AI work happens here |
| Embedding Model | all-mpnet-base-v2 | Strong sentence-level semantic understanding |
| Math | NumPy | Cosine similarity calculations |
| PDF Reading | PyMuPDF | Reliable text extraction from PDFs |
| DOCX Reading | python-docx | Reading Word documents |

---

## Project Structure

```
semsearch/
│
├── streamlit_app.py          # The entire frontend — UI, file upload, results display
│
├── python_engine/
│   └── search_engine.py      # Core NLP logic — chunking, embeddings, MMR search
│
├── java_backend/
│   ├── pom.xml
│   └── src/main/java/com/search/
│       ├── App.java           # Spring Boot entry point
│       └── SearchController.java   # REST endpoint, calls Python via ProcessBuilder
│
├── requirements.txt
└── .streamlit/
    └── config.toml            # Dark theme settings
```

---

## How It Works (The Actual Pipeline)

**Step 1 — Upload & Extract**
You upload a file through the sidebar. The system reads its contents depending on the file type — plain read for TXT, PyMuPDF for PDFs, python-docx for Word files.

**Step 2 — Chunking**
The text gets split into small overlapping chunks. I'm not splitting by word count blindly — the code first breaks the text into complete sentences and then groups them together until a word limit is hit. This matters because if you cut a sentence in half, the embedding for that chunk becomes less accurate.

**Step 3 — Embedding**
Every chunk gets passed to the `all-mpnet-base-v2` Sentence Transformer model, which converts it into a 768-dimensional vector. These vectors encode meaning — sentences that mean similar things end up close together in vector space, even if the words are different.

**Step 4 — Query Comes In**
When you type a question, that question gets embedded into the same 768-dimensional space using the same model.

**Step 5 — Cosine Similarity**
The system compares your query vector against every chunk vector using cosine similarity. This measures the angle between two vectors — the closer the angle, the more similar the meaning. It pulls the top 20 candidates.

**Step 6 — MMR Re-ranking**
Instead of just returning the top 5 by score (which often gives you 5 near-identical chunks), the system runs MMR (Maximal Marginal Relevance). MMR picks results that are both relevant to your query AND different from each other. The result is 5 answers that each add something new.

**Step 7 — Display**
Results come back to Streamlit as ranked cards, each showing the source file, similarity percentage, and the actual text chunk.

---

## The Java Layer

Java acts as a REST API between the frontend and Python. When Streamlit sends a POST request to `localhost:8080/api/search` with the query and file paths, the `SearchController` uses `ProcessBuilder` to run Python as a subprocess, reads the JSON output from stdout, and returns it.

In a real production deployment this layer would also handle things like authentication, rate limiting, logging, and managing multiple users. For this project it demonstrates a proper three-tier architecture which is the standard for enterprise applications.

---

## Why Semantic Search and Not Just Ctrl+F

Regular keyword search only finds exact word matches. If the document uses different terminology than your query, it fails completely. Semantic search converts both the document and the query into vectors that represent meaning, so synonyms, paraphrasing, and related concepts are all handled naturally. This is the same underlying idea behind how Google Search, Notion AI, and most modern document tools work.

---

## Running It Locally (MacBook)

**Requirements:** Python 3.10+, Java 17+, Maven

```bash
# 1. Clone or download the project
cd semsearch

# 2. Create a virtual environment (keeps packages isolated)
python3 -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt
# Note: the model downloads (~420MB) on first run, this is normal

# 4. Run the Streamlit app
streamlit run streamlit_app.py
```

Open `http://localhost:8501` in your browser. Upload a file, click Index, ask a question.

**To also run the Java backend:**
```bash
# Update the PYTHON_SCRIPT path in SearchController.java first, then:
cd java_backend
mvn spring-boot:run
# Runs at http://localhost:8080
```

---

## Deploying to Streamlit Cloud

1. Push the project to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New App**, select your repo, set the main file to `streamlit_app.py`
4. Hit Deploy — Streamlit installs everything from `requirements.txt` automatically

The app gets a public URL. Java doesn't run on Streamlit Cloud, but the app works fine without it since Streamlit imports Python directly.

---

## Known Limitations

- The model runs on CPU, so indexing a large document (50+ pages) takes a few seconds
- The system retrieves relevant chunks but does not generate a direct sentence answer — it shows you the passage so you can read it in context
- Currently supports English documents only
- No persistent storage — the index resets if you refresh the page

---

## Possible Improvements (Future Work)

- Add FAISS vector database for faster search on large document collections
- Use a generative model on top to produce a direct summarised answer from the retrieved chunks (full RAG pipeline)
- Support for multi-language documents
- Save the index to disk so it persists between sessions
- Add highlighting to show which exact sentence within a chunk matched the query

---

*BTech CSE (DSAI) Live Project — Navvya Chaudhary*
