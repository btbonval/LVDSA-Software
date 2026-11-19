# Run:
# python scrape.py

# Where to find Slack App to configure it for other channels, etc: https://api.slack.com/apps

# https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/

import re
import sys
import json
import time
import pypdf
import requests
import tempfile

SOURCES = [
    {"name": "City of Las Vegas",
     "url": "https://lasvegas.primegov.com/api/v2/PublicPortal/ListUpcomingMeetings",
     "pdf": "https://lasvegas.primegov.com/Public/CompiledDocument?meetingTemplateId={templateId}&compileOutputType=1"},
    {"name": "City of North Las Vegas",
     "url": "https://cityofnorthlasvegas.primegov.com/api/v2/PublicPortal/ListUpcomingMeetings",
     "pdf": "https://cityofnorthlasvegas.primegov.com/Public/CompiledDocument?meetingTemplateId={templateId}&compileOutputType=1"},
]

with open('secrets.json', 'r') as jsonfile:
    SECRETS = json.load(jsonfile)

with open('cache.json', 'r') as jsonfile:
    cache = json.load(jsonfile)

CATEGORIES = {
    "no_more_data_centers": [
        r'data\s+center',
        r'artificial\s+intelligence',
        r'\bAI\b',
        r'\bflock\b',
        r'surveillance',
        r'automated',
        r'security',
        r'camera',
        r'axon',
    ],
    "abolish_ice": [
        r'surveillance',
        r'security',
    ],
}

PATTERNS = {
    name: [re.compile(p, re.I) for p in pats]
    for name, pats in CATEGORIES.items()
}

def error_handler(text):
    print(text)
    sys.exit(1)

def fetch(url, stream=False):
    r = requests.get(url, stream=stream)
    if r.status_code != 200:
        error_handler(f"Unable to retrieve data from {url}")
    return r

stats = {
    "documents listed": 0,
    "documents previously seen": 0,
    "documents parsed": 0,
    "documents posted": 0,
    "comments posted": 0,
}
documents = {}

for i in SOURCES:
    r = fetch(i["url"])

    try:
        results = json.loads(r.text)
    except Exception as e:
        error_handler(f"Unable to parse JSON from {i['url']}: {str(e)}")
    del r

    for entry in results:
        for document in entry['documentList']:
            if document['templateName'] == 'Packet':
                documents[entry['title']] = i["pdf"].format(**document)
                stats["documents listed"] += 1
    del results

    for title in documents:
        time.sleep(60)

        doc_url = documents[title]
        if doc_url in cache:
            stats["documents previously seen"] += 1
            continue
        r = fetch(doc_url, stream=True)

        with tempfile.TemporaryFile(mode='w+b') as pdf:
            for chunk in r.iter_content(10485760):
                pdf.write(chunk)

            pdf.seek(0)

            keywords = {}

            reader = pypdf.PdfReader(pdf)

            for p in reader.pages:
                page = p.extract_text() or ""
                for name, pats in PATTERNS.items():
                    for pat in pats:
                        if pat.search(page) is not None:
                            keywords.setdefault(name, set()).add(pat.pattern)

        # track whether a document was posted only once,
        # even if it was posted as a comment to multiple webhooks.
        posted = False

        if keywords.get("no_more_data_centers"):
            message = f"""Found keyword(s) in a City of Las Vegas agenda.
Found words: {sorted(keywords["no_more_data_centers"])}
Document title: {str(title)}
Document URL: {str(doc_url)}
"""
            r = requests.post(SECRETS["NMDC_WEBHOOK"], data=json.dumps({"text": message}))
            r = requests.post(SECRETS["ADMIN_WEBHOOK"], data=json.dumps({"text": message}))
            if r.status_code != 200:
                print("Error posting to slack:")
                print(r.content)
                sys.exit(1)
            stats["comments posted"] += 1
            posted = True

        if keywords.get("abolish_ice"):
            message = f"""Found keyword(s) in a City of Las Vegas agenda.
Found words: {sorted(keywords["abolish_ice"])}
Document title: {str(title)}
Document URL: {str(doc_url)}
"""
            r = requests.post(SECRETS["ABOLISH_WEBHOOK"], data=json.dumps({"text": message}))
            r = requests.post(SECRETS["ADMIN_WEBHOOK"], data=json.dumps({"text": message}))
            if r.status_code != 200:
                print("Error posting to slack:")
                print(r.content)
            sys.exit(1)
            stats["comments posted"] += 1
            posted = True

        if posted:
            stats["documents posted"] += 1

        cache[doc_url] = True
        stats["documents parsed"] += 1

# save out the cache
with open('cache.json','w') as jsonfile:
    json.dump(cache, jsonfile)

print("Completed successfully. Stats:\n", stats)
