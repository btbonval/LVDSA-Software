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

# Set this to True to print to STDOUT for dev purposes rather than submit to Slack Webhooks
LOCAL_DEBUG=False

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
        r'data center',
        r'artificial intelligence',
        r'AI',
        r'flock',
        r'surveillance',
        r'automated',
        r'security',
        r'camera',
        r'axon',
    ],
    # TODO will this search the same PDF for the same keywords twice if they're also above?
    # if yes, keep this dict readable but run it through a function that flips the dict to be
    # `keyword: ['no_more_data_centers', 'abolish_ice']` if both apply, etc
    "abolish_ice": [
        r'surveillance',
        r'security',
    ],
}

PATTERNS = {
    # for each keyword, build a list of [keyword, regex pattern] where
    # the first part is the human readable keyword/keyphrase and
    # the second part is a compiled regular expression to find the keyword.
    # apply '\b' to the front and back of every pattern for word boundaries.
    # replace any space with `\s+` for one or more whitespaces including line breaks.
    name: [[p, re.compile(r'\b' + p.replace(' ',r'\s+') + r'\b', re.I)] for p in pats]
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
                        # break out the readable first item from the regex pattern second item.
                        readable, pattern = pat
                        if pattern.search(page) is not None:
                            keywords.setdefault(name, set()).add(readable)

        # track whether a document was posted only once,
        # even if it was posted as a comment to multiple webhooks.
        posted = False

        # TODO refactor copy/paste between the two if-blocks into a function
        if keywords.get("no_more_data_centers"):
            message = f"""Found keyword(s) in a City of Las Vegas agenda.
Found words: {", ".join(sorted(keywords["no_more_data_centers"]))}
Document title: {str(title)}
Document URL: {str(doc_url)}
"""

            if LOCAL_DEBUG:
                print("NMDC ", message)
            else:
                r = requests.post(SECRETS["NMDC_WEBHOOK"], data=json.dumps({"text": message}))
                if r.status_code != 200:
                    print("Error posting to slack:")
                    print(r.content)
                    sys.exit(1)
            stats["comments posted"] += 1
            posted = True

        if keywords.get("abolish_ice"):
            message = f"""Found keyword(s) in a City of Las Vegas agenda.
Found words: {", ".join(sorted(keywords["abolish_ice"]))}
Document title: {str(title)}
Document URL: {str(doc_url)}
"""
            if LOCAL_DEBUG:
                print("Abolish ", message)
            else:
                r = requests.post(SECRETS["ABOLISH_WEBHOOK"], data=json.dumps({"text": message}))
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
