""" THIS IS AN AUTOMATICALLY GENERATED FILE!"""
from __future__ import print_function
import json
from restler.engine import primitives
from restler.engine.core import requests
from restler.engine.errors import ResponseParsingException
from restler.engine import dependencies

req_collection = requests.RequestCollection([])
# Endpoint: /products, method: Post
request = requests.Request([
    primitives.restler_static_string("POST "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("products"),
    primitives.restler_static_string("?"),
    primitives.restler_static_string("required-param="),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False, examples=["a"]),
    primitives.restler_static_string("&"),
    primitives.restler_static_string("optional-param="),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False, examples=["b"]),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/products"
)
req_collection.add_request(request)
