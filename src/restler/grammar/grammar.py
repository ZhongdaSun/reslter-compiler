""" THIS IS AN AUTOMATICALLY GENERATED FILE!"""
from __future__ import print_function
import json
from restler.engine import primitives
from restler.engine.core import requests
from restler.engine.errors import ResponseParsingException
from restler.engine import dependencies
req_collection = requests.RequestCollection([])
# Endpoint: /redis/after/deriveRules, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/event-relation-after"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("redis"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("after"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("deriveRules"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: 192.168.1.21:17103\r\n"),
    primitives.restler_static_string("Authorization: "),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/redis/after/deriveRules"
)
req_collection.add_request(request)

# Endpoint: /redis/after/derives/{ruleId}, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/event-relation-after"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("redis"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("after"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("derives"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload("ruleId", quoted=False),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: 192.168.1.21:17103\r\n"),
    primitives.restler_static_string("Authorization: "),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/redis/after/derives/{ruleId}"
)
req_collection.add_request(request)

# Endpoint: /rules/api/v1/relation/after, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/event-relation-after"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("rules"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("v1"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("relation"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("after"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: 192.168.1.21:17103\r\n"),
    primitives.restler_static_string("Authorization: "),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/rules/api/v1/relation/after"
)
req_collection.add_request(request)

# Endpoint: /rules/api/v1/relation/after, method: Post
request = requests.Request([
    primitives.restler_static_string("POST "),
    primitives.restler_basepath("/event-relation-after"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("rules"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("v1"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("relation"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("after"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: 192.168.1.21:17103\r\n"),
    primitives.restler_static_string("Authorization: "),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("\r\n"),
    primitives.restler_static_string("Content-Type: "),
    primitives.restler_static_string("application/json"),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string("\r\n"),

],
requestId="/rules/api/v1/relation/after"
)
req_collection.add_request(request)

# Endpoint: /rules/api/v1/relation/after/context/keys, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/event-relation-after"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("rules"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("v1"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("relation"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("after"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("context"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("keys"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: 192.168.1.21:17103\r\n"),
    primitives.restler_static_string("Authorization: "),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/rules/api/v1/relation/after/context/keys"
)
req_collection.add_request(request)

# Endpoint: /rules/api/v1/relation/after/rt/appversion/his, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/event-relation-after"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("rules"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("v1"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("relation"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("after"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("rt"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("appversion"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("his"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: 192.168.1.21:17103\r\n"),
    primitives.restler_static_string("Authorization: "),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/rules/api/v1/relation/after/rt/appversion/his"
)
req_collection.add_request(request)

# Endpoint: /rules/api/v1/relation/after/{ruleId}, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/event-relation-after"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("rules"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("v1"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("relation"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("after"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload("ruleId", quoted=False),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: 192.168.1.21:17103\r\n"),
    primitives.restler_static_string("Authorization: "),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/rules/api/v1/relation/after/{ruleId}"
)
req_collection.add_request(request)

# Endpoint: /rules/api/v1/relation/after/{ruleId}, method: Put
request = requests.Request([
    primitives.restler_static_string("PUT "),
    primitives.restler_basepath("/event-relation-after"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("rules"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("v1"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("relation"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("after"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: 192.168.1.21:17103\r\n"),
    primitives.restler_static_string("Authorization: "),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("\r\n"),
    primitives.restler_static_string("Content-Type: "),
    primitives.restler_static_string("application/json"),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string("\r\n"),

],
requestId="/rules/api/v1/relation/after/{ruleId}"
)
req_collection.add_request(request)

# Endpoint: /rules/api/v1/relation/after/{ruleId}/detail, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/event-relation-after"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("rules"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("v1"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("relation"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("after"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload("ruleId", quoted=False),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("detail"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: 192.168.1.21:17103\r\n"),
    primitives.restler_static_string("Authorization: "),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/rules/api/v1/relation/after/{ruleId}/detail"
)
req_collection.add_request(request)

# Endpoint: /rules/api/v1/relation/after/{ruleId}/disable, method: Put
request = requests.Request([
    primitives.restler_static_string("PUT "),
    primitives.restler_basepath("/event-relation-after"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("rules"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("v1"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("relation"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("after"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload("ruleId", quoted=False),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("disable"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: 192.168.1.21:17103\r\n"),
    primitives.restler_static_string("Authorization: "),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/rules/api/v1/relation/after/{ruleId}/disable"
)
req_collection.add_request(request)

# Endpoint: /rules/api/v1/relation/after/{ruleId}/enable, method: Put
request = requests.Request([
    primitives.restler_static_string("PUT "),
    primitives.restler_basepath("/event-relation-after"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("rules"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("v1"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("relation"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("after"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload("ruleId", quoted=False),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("enable"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: 192.168.1.21:17103\r\n"),
    primitives.restler_static_string("Authorization: "),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/rules/api/v1/relation/after/{ruleId}/enable"
)
req_collection.add_request(request)

# Endpoint: /rules/api/v1/relation/after/{ruleId}/his, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/event-relation-after"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("rules"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("v1"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("relation"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("after"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload("ruleId", quoted=False),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("his"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: 192.168.1.21:17103\r\n"),
    primitives.restler_static_string("Authorization: "),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/rules/api/v1/relation/after/{ruleId}/his"
)
req_collection.add_request(request)

# Endpoint: /rules/api/v1/relation/after/{ruleId}/his/{version}, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/event-relation-after"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("rules"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("v1"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("relation"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("after"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload("ruleId", quoted=False),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("his"),
    primitives.restler_static_string("/"),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: 192.168.1.21:17103\r\n"),
    primitives.restler_static_string("Authorization: "),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/rules/api/v1/relation/after/{ruleId}/his/{version}"
)
req_collection.add_request(request)

# Endpoint: /rules/api/v1/relation/after/{ruleId}/manyhis, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/event-relation-after"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("rules"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("v1"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("relation"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("after"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload("ruleId", quoted=False),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("manyhis"),
    primitives.restler_static_string("?"),
    primitives.restler_static_string("versions="),
    primitives.restler_custom_payload("versions", quoted=False),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: 192.168.1.21:17103\r\n"),
    primitives.restler_static_string("Authorization: "),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/rules/api/v1/relation/after/{ruleId}/manyhis"
)
req_collection.add_request(request)
