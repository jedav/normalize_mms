#!/usr/bin/env python

from flask import Flask, make_response, request
import defusedxml.ElementTree as ET
from normalize_addresses import gather_addrs, update_addrs

app = Flask(__name__)

# reference: http://stackoverflow.com/a/27638470/1380639
# our inputs are a bit bigger (tens of MB), but...  doing the stupid thing first

def transform(xml):
  root = ET.fromstring(xml, forbid_dtd=True)
  addrmap = gather_addrs(root)
  update_addrs(root, addrmap)
  return ET.tostring(root)

@app.route('/')
def form():
  return """
    <html>
      <body>
        <h1>Normalize MMS phone numbers</h1>

        <form action="/transform" method="post" enctype="multipart/form-data">
          <input type="file" name="mms_file" />
          <input type="submit" />
        </form>
      </body>
    </html>
  """

@app.route('/transform', methods=["POST"])
def transform_view():
  file = request.files['mms_file']
  if not file:
    return "No file"

  file_contents = file.stream.read()

  result = transform(file_contents)

  response = make_response(result)
  response.headers["Content-Disposition"] = "attachment; filename=normalized.xml"
  return response

if __name__ == "__main__":
  # runs on the inside of a VPN host
  app.run(host="10.8.0.1")
