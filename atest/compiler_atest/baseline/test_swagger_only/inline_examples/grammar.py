""" THIS IS AN AUTOMATICALLY GENERATED FILE!"""
from __future__ import print_function
import json
from restler.engine import primitives
from restler.engine.core import requests
from restler.engine.errors import ResponseParsingException
from restler.engine import dependencies

req_collection = requests.RequestCollection([])
# Endpoint: /servers/{serverId}/restart, method: Post
request = requests.Request([
    primitives.restler_static_string("POST "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("servers"),
    primitives.restler_static_string("/"),
    primitives.restler_fuzzable_int("1", examples=["1234567"]),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("restart"),
    primitives.restler_static_string("?"),
    primitives.restler_static_string("computerSize="),
    primitives.restler_fuzzable_number("1.23", examples=["1.67"]),
    primitives.restler_static_string("&"),
    primitives.restler_static_string("computerDimensions="),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False, examples=[None]),
    primitives.restler_static_string(","),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False, examples=["inline_ex_1"]),
    primitives.restler_static_string(","),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False, examples=["inline_ex_2"]),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_static_string("computerName: "),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False, examples=["inline_example_value_laptop1"]),
    primitives.restler_static_string("\r\n"),
    primitives.restler_static_string("Content-Type: "),
    primitives.restler_static_string("application/json"),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),
    primitives.restler_static_string("{"),
    primitives.restler_static_string("""
    "cpu":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True, examples=["i5"]),
    primitives.restler_static_string(""",
    "memory":"""),
    primitives.restler_fuzzable_int("1", examples=["32"]),
    primitives.restler_static_string("}"),
    primitives.restler_static_string("\r\n"),

],
requestId="/servers/{serverId}/restart"
)
req_collection.add_request(request)
