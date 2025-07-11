#!/usr/bin/env python3
# clipboard_server.py

from flask import Flask, request
import subprocess

app = Flask(__name__)
windows_clip = ""

@app.route('/win', methods=['GET', 'POST'])
def win_clipboard():
    """
    POST: Receive Windows clipboard text in the request body and store it.
    GET:  Return the last stored Windows clipboard text.
    """
    global windows_clip
    if request.method == 'POST':
        windows_clip = request.get_data(as_text=True)
        return 'OK', 200
    else:
        return windows_clip, 200

@app.route('/mac', methods=['GET', 'POST'])
def mac_clipboard():
    """
    POST: Receive text in the request body and set it into the Mac clipboard.
    GET:  Read and return the current Mac clipboard contents.
    """
    if request.method == 'POST':
        data = request.get_data()
        p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        p.communicate(data)
        return 'OK', 200
    else:
        p = subprocess.Popen(['pbpaste'], stdout=subprocess.PIPE)
        data, _ = p.communicate()
        return data, 200

if __name__ == '__main__':
    # Listen on all interfaces, port 8000
    app.run(host='0.0.0.0', port=8000, debug=True)
