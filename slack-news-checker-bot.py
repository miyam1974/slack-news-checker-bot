#!/usr/bin/env python3
# ------------------------------------------------------------------------------
# SCRIPT (No changes required)
# ------------------------------------------------------------------------------
url_post = "https://slack.com/api/chat.postMessage"
url_base = "https://news.google.com/rss/search"

k_hl    = "hl"
v_hl    = "ja"
k_gl    = "gl"
v_gl    = "JP"
k_ceid  = "ceid"
v_ceid  = v_hl + ":" + v_gl

normal  = "normal"
dry_run = "dry-run"

import requests
import socket
import os
import sys
import importlib
from datetime import datetime,timedelta,timezone
import feedparser
import urllib.parse

def get_day_of_week_jp(dt):
    w_list = ['月', '火', '水', '木', '金', '土', '日']
    return(w_list[dt.weekday()])

def main():
    # ------------------
    # 0.1: config check
    # ------------------
    host = socket.gethostname()
    ip   = socket.gethostbyname(host)
    file = os.path.basename(__file__)

    try:
        conf   = os.path.splitext(os.path.basename(file))[0] + "-config"
        config = importlib.import_module(conf)
    except ModuleNotFoundError as e:
        print("Error: config file import failed. File: %s Desc: %s\n" % (conf, e.args), file=sys.stderr)
        sys.exit(1)

    try:
        config.token
        config.post_channel_id
        config.q_word
        config.q_days

    except AttributeError as e:
        print("Error: required config not exists. Desc: %s\n" % (e.args), file=sys.stderr)
        sys.exit(1)

    if config.q_days == 0:
        config.q_days = 1

    # ------------------
    # 0.2: mode check (normal / dry_run)
    # ------------------
    mode = normal
    if len(sys.argv) >= 2: # 1: No Arguments
        if [a for a in sys.argv if a.lower() == dry_run]:
            mode = dry_run
    # ------------------
    # 1: url
    # ------------------
    #q={param} when:{days}d&hl=ja&gl=JP&ceid=JP:ja
    q = {
        "q"    : config.q_word + " when:" + str(config.q_days) + "d",
        k_hl   : v_hl,
        k_gl   : v_gl,
        k_ceid : v_ceid
    }
    param = urllib.parse.urlencode(q, safe='/:', quote_via=urllib.parse.quote)
    url   = url_base + "?" + param

    # ------------------
    # 2: rss
    # ------------------
    tz   = timezone(timedelta(hours=config.tz_hours))
    rss  = feedparser.parse(url)
    
    feed_dt_jst = datetime(*rss.feed.updated_parsed[:6], tzinfo=timezone.utc).astimezone(tz)
    feed_date   = "%s(%s)" % (feed_dt_jst.strftime("%Y/%-m/%-d %-H:%M"), get_day_of_week_jp(feed_dt_jst))
    
    text = ""
    for entry in rss.entries:
        entry_dt_jst = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).astimezone(tz)
        text += "%s(%s)" % (entry_dt_jst.strftime("%Y/%-m/%-d"), get_day_of_week_jp(entry_dt_jst)) + "\n"
        text += entry.title + "\n"
        text += entry.link  + "\n"
        text += "\n"

    # ------------------
    # 3: slack post
    # ------------------
    if mode == normal or mode == dry_run:
        if text != "":
            text  = "Google News [q=%s] at %s\n----------\n" % (q["q"], feed_date) + text
            text += "Posted from: %s (%s):%s" % (host, ip, file)+ "\n"
            payload1 = {
                "token"     : config.token,
                "channel"   : config.post_channel_id,
                "link_names": "true",
                "text"      : text
            }
            if mode == normal:
                response1  = requests.get(url_post, params=payload1)
                json_data1 = response1.json()
                if json_data1["ok"] == False:
                    print("Error: api/chat.postMessage failed. Desc: %s\n" % (json_data1["error"]), file=sys.stderr)
                    sys.exit(1)

    arguments = []
    if len(sys.argv) >= 2:
        arguments = sys.argv[1:len(sys.argv)]

    print("Args: %s" % (arguments))
    print("Mode: %s" % (mode))
    print("\n" + text)

if __name__ == '__main__':
    main()
# ------------------------------------------------------------------------------
