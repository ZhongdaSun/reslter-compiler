""" THIS IS AN AUTOMATICALLY GENERATED FILE!"""
from __future__ import print_function
import json
from rest.restler.engine import primitives
from rest.restler.engine.core import requests
from rest.restler.engine.errors import ResponseParsingException
from rest.restler.engine import dependencies

req_collection = requests.RequestCollection([])
# Endpoint: /Microsoft.Network/applicationGatewayAvailableSslOptions/default, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("Microsoft.Network"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("applicationGatewayAvailableSslOptions"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("default"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/Microsoft.Network/applicationGatewayAvailableSslOptions/default"
)
req_collection.add_request(request)

# Endpoint: /Microsoft.Network/applicationGatewayAvailableSslOptions/default/predefinedPolicies, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("Microsoft.Network"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("applicationGatewayAvailableSslOptions"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("default"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("predefinedPolicies"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/Microsoft.Network/applicationGatewayAvailableSslOptions/default/predefinedPolicies"
)
req_collection.add_request(request)

# Endpoint: /Microsoft.Network/applicationGatewayAvailableSslOptions/default/predefinedPolicies/{predefinedPolicyName}, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("Microsoft.Network"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("applicationGatewayAvailableSslOptions"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("default"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("predefinedPolicies"),
    primitives.restler_static_string("/"),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/Microsoft.Network/applicationGatewayAvailableSslOptions/default/predefinedPolicies/{predefinedPolicyName}"
)
req_collection.add_request(request)
