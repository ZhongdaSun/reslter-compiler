""" THIS IS AN AUTOMATICALLY GENERATED FILE!"""
from __future__ import print_function
import json
from engine import primitives
from engine.core import requests
from engine.errors import ResponseParsingException
from engine import dependencies
req_collection = requests.RequestCollection([])
# Endpoint: /v1/application/export, method: Post
request = requests.Request([
    primitives.restler_static_string("POST "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("v1"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("application"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("export"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_static_string("Authorization: "),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("\r\n"),
    primitives.restler_static_string("Content-Type: "),
    primitives.restler_static_string("application/json"),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),
    primitives.restler_static_string("["),
    primitives.restler_static_string("""
    """),
    primitives.restler_fuzzable_object("{ \"fuzz\": false }"),
    primitives.restler_static_string("]"),
    primitives.restler_static_string("\r\n"),

],
requestId="/v1/application/export"
)
req_collection.add_request(request)

# Endpoint: /v1/kubernetes/namespaces/deployments/scale, method: Patch
request = requests.Request([
    primitives.restler_static_string("PATCH "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("v1"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("kubernetes"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("namespaces"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("deployments"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("scale"),
    primitives.restler_static_string("?"),
    primitives.restler_static_string("appName="),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("&"),
    primitives.restler_static_string("nameSpace="),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("&"),
    primitives.restler_static_string("scaleCount="),
    primitives.restler_fuzzable_object("{ \"fuzz\": false }"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_static_string("Authorization: "),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/v1/kubernetes/namespaces/deployments/scale"
)
req_collection.add_request(request)
