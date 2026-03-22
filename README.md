# Zomato-AI-Restaurant-Recommendation-System

AI-powered restaurant recommendation system that uses user inputs (city, budget, preferences) to generate personalized dining suggestions using real Zomato data and LLM-based reasoning.

**Scope:** The bundled dataset maps “city” to Zomato **localities within Bangalore** (e.g. Banashankari, Bellandur)—not other metros—so searches should use those area names.

## Web UI

1. **Change directory to the repository root** (the folder that contains `phase_6_web/` and `data/`). If you run from another folder, Python may report `No module named 'phase_6_web'` or the app will not find the Parquet file.

2. Install dependencies (`pip install -r requirements.txt`), then start the server:

   `python3 -m phase_6_web`

   The terminal prints the exact URL (default **http://127.0.0.1:8000/**). You can also use:

   `python3 -m uvicorn phase_6_web.api:app --host 127.0.0.1 --port 8000`

3. Open that URL in a normal browser tab (Chrome, Safari, Firefox—not “Open with Live Server” on the HTML file alone). Do not use `file:///…/index.html`.

**If the page still does not load:** read the terminal output. `Address already in use` means another app is on port 8000—use `PORT=8001 python3 -m phase_6_web` and open `http://127.0.0.1:8001/`. `ModuleNotFoundError: phase_6_web` means you are not in the repo root on `PYTHONPATH` (use `cd` to the project root first).

## 📐 Architecture

See detailed system design here: [ARCHITECTURE.md](./ARCHITECTURE.md)
