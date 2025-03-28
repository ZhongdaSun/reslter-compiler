""" THIS IS AN AUTOMATICALLY GENERATED FILE!"""
from __future__ import print_function
import json
from rest.restler.engine import primitives
from rest.restler.engine.core import requests
from rest.restler.engine.errors import ResponseParsingException
from rest.restler.engine import dependencies
req_collection = requests.RequestCollection([])
# Endpoint: /Ping, method: Post
request = requests.Request([
    primitives.restler_static_string("POST "),
    primitives.restler_basepath(""),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("Ping"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: {{fums-reporting}}\r\n"),
    primitives.restler_static_string("Content-Type: "),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False, examples=["application/json"]),
    primitives.restler_static_string("\r\n"),
    primitives.restler_static_string("Content-Type: "),
    primitives.restler_static_string("application/json"),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True, examples=["BBBBCCCCC"]),
    primitives.restler_static_string("\r\n"),

],
requestId="/Ping"
)
req_collection.add_request(request)

# Endpoint: /Ping, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath(""),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("Ping"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: {{fums-reporting}}\r\n"),
    primitives.restler_static_string("Content-Type: "),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False, examples=["application/json"]),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/Ping"
)
#req_collection.add_request(request)
