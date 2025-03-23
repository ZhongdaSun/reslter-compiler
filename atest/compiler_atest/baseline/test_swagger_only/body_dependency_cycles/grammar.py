""" THIS IS AN AUTOMATICALLY GENERATED FILE!"""
from __future__ import print_function
import json
from restler.engine import primitives
from restler.engine.core import requests
from restler.engine.errors import ResponseParsingException
from restler.engine import dependencies

req_collection = requests.RequestCollection([])
# Endpoint: /sites/{name}/slots/{slot}/privateAccess/virtualNetworks, method: Put
request = requests.Request([
    primitives.restler_static_string("PUT "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("sites"),
    primitives.restler_static_string("/"),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("slots"),
    primitives.restler_static_string("/"),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("privateAccess"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("virtualNetworks"),
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
    "enabled":"""),
    primitives.restler_fuzzable_bool("true"),
    primitives.restler_static_string(""",
    "virtualNetworks":
    [
        {
            "name":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
            "key":"""),
    primitives.restler_fuzzable_int("1"),
    primitives.restler_static_string(""",
            "resourceId":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
            "subnets":
            [
                {
                    "name":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
                    "key":"""),
    primitives.restler_fuzzable_int("1"),
    primitives.restler_static_string("""
                }
            ]
        }
    ]}"""),
    primitives.restler_static_string("\r\n"),

],
requestId="/sites/{name}/slots/{slot}/privateAccess/virtualNetworks"
)
req_collection.add_request(request)

# Endpoint: /Microsoft.Web/sites/{name}/privateAccess/virtualNetworks, method: Put
request = requests.Request([
    primitives.restler_static_string("PUT "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("Microsoft.Web"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("sites"),
    primitives.restler_static_string("/"),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("privateAccess"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("virtualNetworks"),
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
    "enabled":"""),
    primitives.restler_fuzzable_bool("true"),
    primitives.restler_static_string(""",
    "virtualNetworks":
    [
        {
            "name":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
            "key":"""),
    primitives.restler_fuzzable_int("1"),
    primitives.restler_static_string(""",
            "resourceId":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
            "subnets":
            [
                {
                    "name":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
                    "key":"""),
    primitives.restler_fuzzable_int("1"),
    primitives.restler_static_string("""
                }
            ]
        }
    ]}"""),
    primitives.restler_static_string("\r\n"),

],
requestId="/Microsoft.Web/sites/{name}/privateAccess/virtualNetworks"
)
req_collection.add_request(request)
