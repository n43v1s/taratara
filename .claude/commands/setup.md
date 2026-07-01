Set up the project virtual environment and install all dependencies.

Steps:
1. Create `.venv` using Python 3.14.
2. Install packages from `requirements.txt`.
3. Vendor HTMX 2.0.10 into `app/static/vendor/htmx.min.js`.

Run each step and confirm it succeeds before moving to the next.

```bash
py -3.14 -m venv .venv
.venv/Scripts/pip install -r requirements.txt
```

For HTMX vendoring, download from:
https://unpkg.com/htmx.org@2.0.10/dist/htmx.min.js
and save to `app/static/vendor/htmx.min.js`.
