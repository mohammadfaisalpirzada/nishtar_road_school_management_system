web: gunicorn web_app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 60
worker: python worker.py  # Optional background sync process - enable by setting ENABLE_BACKGROUND_SYNC=true
