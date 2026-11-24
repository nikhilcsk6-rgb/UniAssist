from app import create_app

app = create_app()

if __name__ == "__main__":
    # use_reloader=False: the auto-reloader restarts the server mid-request (and can fight with the
    # Chroma/SQLite files on Windows/OneDrive). Restart manually after code changes.
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False, threaded=True)
