# Run:
# python scraper.py

# Where to find Slack App to configure it for other channels, etc: https://api.slack.com/apps

# https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/

import re
import sys
import json
import time
import pypdf
import requests
import tempfile

SOURCE='https://lasvegas.primegov.com/api/v2/PublicPortal/ListUpcomingMeetings'
PDF='https://lasvegas.primegov.com/Public/CompiledDocument?meetingTemplateId={templateId}&compileOutputType=1'

with open('secrets.json','r') as jsonfile:
    SECRETS = json.load(jsonfile)

with open('cache.json','r') as jsonfile:
    cache = json.load(jsonfile)

# regular expressions to seek in the document
# compile them case-insensitive as part of a list comprehension
expressions = [re.compile(x, re.I) for x in [
    r'data center',
    r'artificial intelligence',
    r' AI ',
    r' flock ',
    r'surveillance',
    r'automated',
    r'security',
    r'camera',
]]

def error_handler(text):
    print(text)
    sys.exit(1)

def fetch(url, stream=False):
    r = requests.get(url, stream=stream)
    if r.status_code != 200:
        error_handler(f"Unable to retrieve data from {url}")
    return r

r = fetch(SOURCE)

try:
    results = json.loads(r.text)
except e:
    error_handler(f"Unable to parse JSON from {SOURCE}: {str(e)}")
# submit for garbage collection, to keep memory low.
del r

# track stats for output
stats = {
    "documents listed": 0,
    "documents previously seen": 0,
    "documents parsed": 0,
    "documents posted": 0,
}

# track document URLs for download later.
documents = {}
for entry in results:
    for document in entry['documentList']:
        if document['templateName'] == 'Packet':
            documents[entry['title']] = PDF.format(**document)
            stats["documents listed"] += 1
# submit for garbage collection, to keep memory low.
del results

# wait a minute for rate limiting
time.sleep(60)

for title in documents:
    doc_url = documents[title]
    if doc_url in cache:
        # don't need to fetch this one again.
        stats["documents previously seen"] += 1
        continue
    r = fetch(doc_url, stream=True)
    # setup a temporary binary file to store the PDF data
    with tempfile.TemporaryFile(mode='w+b') as pdf:
        # download pieces of the file so it doesn't all go into memory
        # read and store 10 KiB at a time, 10*1024*1024 = 10485760
        for chunk in r.iter_content(10485760):
            pdf.write(chunk)
        # the PDF file is complete. Let's run it back to the beginning to be read.
        pdf.seek(0)

        # only the first hit matters
        found_a_hit = False
        reader = pypdf.PdfReader(pdf)
        for p in reader.pages:
            # read a single page at a time to conserve memory
            page = p.extract_text()
            for e in expressions:
                if e.search(page) is not None:
                    # a keyword was found.
                    found_a_hit = True
                    message = f"""Found a keyword in a City of Las Vegas agenda.
Found word: {str(e.pattern)}
Document title: {str(title)}
Document URL: {str(doc_url)}
"""
                    # use json.dumps to escape anything weird in the text message so it won't be interpreted as text
                    r = requests.post(SECRETS["ABOLISH_WEBHOOK"], data=json.dumps({"text": message}))
                    if r.status_code != 200:
                        print("Error posting to slack:")
                        print(r.content)
                        sys.exit(1)
                    #print(f"Found a match. Posted to Slack with status code {r.status_code}")
                    stats["documents posted"] += 1
                    # stop checking expressions
                    break
            if found_a_hit:
                # a hit was found on this page, no need to check more pages.
                break
        # closing the file will delete the file from disk.
        pdf.close()
        # submit for garbage collection, to keep memory low.
        del pdf
        # did enough work to say we processed this one.
        cache[doc_url] = True
        stats["documents parsed"] += 1
        # take a break to avoid rate limits
        time.sleep(60)

# save out the cache
with open('cache.json','w') as jsonfile:
    json.dump(cache, jsonfile)

print("Completed successfully. Stats:\n", stats)
