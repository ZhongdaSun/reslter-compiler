""" THIS IS AN AUTOMATICALLY GENERATED FILE!"""
from __future__ import print_function
import json
from restler.engine import primitives
from restler.engine.core import requests
from restler.engine.errors import ResponseParsingException
from restler.engine import dependencies
req_collection = requests.RequestCollection([])
# Endpoint: /resource, method: Post
request = requests.Request([
    primitives.restler_static_string("POST "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("resource"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/resource"
)
req_collection.add_request(request)

# Endpoint: /resource/{resourceId}, method: Put
request = requests.Request([
    primitives.restler_static_string("PUT "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("resource"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload_uuid4_suffix("resourceId", quoted=False),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_static_string("Content-Type: "),
    primitives.restler_static_string("application/json"),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),
    primitives.restler_static_string("{"),
    primitives.restler_static_string("""
    "resource":
        {
            "id":"""),
    primitives.restler_custom_payload_uuid4_suffix("/resource/id", quoted=False),
    primitives.restler_static_string(""",
            "name":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string("""
        }
    }"""),
    primitives.restler_static_string("\r\n"),

],
requestId="/resource/{resourceId}"
)
req_collection.add_request(request)
