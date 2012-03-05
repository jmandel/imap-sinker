"""
IMAP Sinker
Josh Mandel 6/2010

Copies unread messages FROM

  * INBOX of one IMAP account(the "source")

    TO

  * INBOX of another IMAP account (the "sink")

Just supply connection details in a separate config file...

Intended to run as a cron job keeping one IMAP account synced to the
new messages in another.  I use this to get e-mail from an Exchange
server (which happens to run IMAP but not POP) into my GMail inbox
(since GMail doesn't currently support auto-fetching over IMAP).

crontab -e:

  */5 * * * * /usr/bin/python /path/to/imap_sinker.py

"""

# Non-configurable code below...
 
import imaplib, time, rfc822, sys
from ConfigParser import ConfigParser

fn = sys.argv[1].strip()
config = ConfigParser({"port" : "993"})
config.read([fn])

def quit(code):
    try: source.close()
    except: pass
    try: sink.close()
    except: pass
    sys.exit(code)

valid = "OK"
def ok(r):
    if (r[0] != valid):
        print "Invalid result.", r
        quit(1)
    return r[1]

source = imaplib.IMAP4_SSL(config.get("source", "server"))
ok(source.login(config.get("source", "user"), config.get("source", "pass")))
ok(source.select("INBOX"))
print source.search(None, "UNSEEN")
messages = ok(source.search(None, "UNSEEN"))[0]
if len(messages) == 0:
    quit(0) # NTD

messages = [int(x) for x in messages.split(" ")]
print messages

sink = imaplib.IMAP4_SSL(config.get("sink", "server"), int(config.get("sink", "port")))
ok(sink.login(config.get("sink", "user"), config.get("sink", "pass")))
ok(sink.select("INBOX"))
for m_number in messages:
    m = ok(source.fetch(m_number, "RFC822"))[0][1]
    header = ok(source.fetch(m_number, "BODY.PEEK[HEADER.FIELDS (Date)]"))
    mdate_raw = header[0][1][6:]
    mdate = time.mktime(rfc822.parsedate(header[0][1][6:]))

    if '#secure' in m:
        m = \
"""From: "Mandel, Joshua" <Joshua.Mandel@childrens.harvard.edu>
To: "Mandel, Joshua" <Joshua.Mandel@childrens.harvard.edu>
Subject: Log in to CHB to receive a #secure# message (nt).
Date: """ + mdate_raw.strip() + """
Accept-Language: en-US
Content-Language: en-US
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

"""
    ok(sink.append("INBOX", "", imaplib.Time2Internaldate(mdate), m))
    ok(source.store(m_number, "+FLAGS", "\\SEEN"))
    print "Sent", m_number
quit(0)
