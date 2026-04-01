# Starter Here

## 1) Install (beta)

```bash
pipx install "git+https://github.com/Alberto-Manzoni/PyTestFlow.git@v0.2.0-beta.1"
```

Source repositories:
- Engine: https://github.com/Alberto-Manzoni/PyTestFlow
- Frontend: https://github.com/Alberto-Manzoni/PyTestFlow-FrontEnd

## 2) Start backend + GUI host

```bash
pytestflow-am start
```

Optional (open browser automatically):

```bash
pytestflow-am start --open
```

## 3) Open GUI

Go to `http://127.0.0.1:8000/`.

## 4) Run the motherboard sequence

In the GUI:
1. Select the motherboard test sequence.
2. Launch the run.

## Notes

- The backend exposes WebSocket on `ws://127.0.0.1:8765`.
- If frontend assets are in a local folder, set `PYTESTFLOW_FRONTEND_DIR` to that folder (must contain `index.html`).
- If you need this guide in your current folder, run:

```bash
pytestflow-am quickstart
```
