#! /usr/bin/env python
# coding: utf-8

# **********************************************************************
# file: fanyi.py
#
# using youdao python api to translate engligh to chinese or
# chinese to english
#
# API key：1095912987
# keyfrom：hopstar
#
# http://fanyi.youdao.com/openapi.do?keyfrom=hopstar&key=1095912987&type=data&doctype=<doctype>&version=1.1&q=要翻译的文本
# **********************************************************************

import json
import sys

py3 = sys.version_info.major == 3
if py3:
    from urllib.parse import quote
    from urllib.request import urlopen
    raw_input = input
else:
    from urllib import urlopen

API_KEY = "1095912987"
KEYFROM = "hopstar"
DEF_DOCTYPE = "json"
API = "http://fanyi.youdao.com/openapi.do"


def fanyi(query,
          api=API,
          doctype=DEF_DOCTYPE,
          key=API_KEY,
          keyfrom=KEYFROM,
          debug=False):
    """doctype need be: doctype=[json|jsonp|xml|text]"""

    url = "{api}?keyfrom={keyfrom}&key={key}&type=data&doctype={doctype}&version=1.1&q={query}".format(
        api=api,
        key=key,
        keyfrom=keyfrom,
        doctype=doctype,
        query=quote(query) if py3 else query)

    if debug:
        print("query_url:", url)

    res = json.loads(urlopen(url).read().decode("utf-8"))

    if debug:
        print("json:", res)

    error_code = res["errorCode"]

    if error_code == 0:  # normal
        trans = " *|* ".join(res["translation"])
        # print ("{query} ===> {trans}".format(query=query, trans=trans.encode('utf-8')))
        print("{query} ===> {trans}".format(
            query=query, trans=trans if py3 else trans.encode("utf-8")))
        if "basic" in res:
            print("\nBasic info:")
            for key in res["basic"]:
                value = res["basic"][key]
                if isinstance(value, (list, tuple)):
                    value = " #|# ".join(value)
                print("\t{key}: {value}".format(
                    key=key, value=value if py3 else value.encode("utf-8")))

        if "web" in res:
            print("\nWeb info:")
            for item in res["web"]:
                key = item["key"]
                value = " -|- ".join(item["value"])
                print("\t{key}: {value}".format(
                    key=key if py3 else key.encode("utf-8"),
                    value=value if py3 else value.encode("utf-8")))
    elif error_code == 20:  # input query is too long (longer than 200)
        print("**Error**: {query} is too long".format(query=query))
    elif error_code == 30:  # can't translate
        print("**Erorr**: Can't tranlate {query}".format(query=query))
    elif error_code == 40:  # unsupport lang
        print("**Error**: unsupport lang {query}".format(query=query))
    elif error_code == 50:  # unvalid key
        print("**Error**: unvalid key {query}".format(query=query))
    else:  # unknown error code
        print("**Error**: Unknown Error Code get {query}".format(query=query))

    print("")  # print empty line


def main():
    args = sys.argv[1:]
    if not args:
        while True:
            query = raw_input("Query:")
            fanyi(query)

    list(map(fanyi, sys.argv[1:]))


if __name__ == "__main__":
    main()
