""" THIS IS AN AUTOMATICALLY GENERATED FILE!"""
from __future__ import print_function
import json
from restler.engine import primitives
from restler.engine.core import requests
from restler.engine.errors import ResponseParsingException
from restler.engine import dependencies

_archive_post_hash_query = dependencies.DynamicVariable("_archive_post_hash_query")

_archive_post_name = dependencies.DynamicVariable("_archive_post_name")

_archive_post_tag = dependencies.DynamicVariable("_archive_post_tag")

_file__fileId__post_fileId_path = dependencies.DynamicVariable("_file__fileId__post_fileId_path")

req_collection = requests.RequestCollection([])
# Endpoint: /archive/{archiveId}/{label}, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("archive"),
    primitives.restler_static_string("/"),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False),
    primitives.restler_static_string("/"),
    primitives.restler_static_string(_archive_post_tag.reader(), quoted=False),
    primitives.restler_static_string("?"),
    primitives.restler_static_string("hash="),
    primitives.restler_custom_payload_query("hash"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/archive/{archiveId}/{label}"
)
req_collection.add_request(request)

# Endpoint: /archive, method: Post
request = requests.Request([
    primitives.restler_static_string("POST "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("archive"),
    primitives.restler_static_string("?"),
    primitives.restler_static_string("hash="),
    primitives.restler_custom_payload_query("hash", writer=_archive_post_hash_query.writer()),
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
    "name":"""),
    primitives.restler_fuzzable_object("{ \"fuzz\": false }", writer=_archive_post_name.writer()),
    primitives.restler_static_string(""",
    "tag":"""),
    primitives.restler_custom_payload("tag", quoted=True, writer=_archive_post_tag.writer()),
    primitives.restler_static_string("}"),
    primitives.restler_static_string("\r\n"),
    
    {

        'post_send':
        {
            
            'dependencies':
            [
                _archive_post_hash_query.writer(),
                _archive_post_name.writer(),
                _archive_post_tag.writer()
            ]
        }

    },

],
requestId="/archive"
)
req_collection.add_request(request)

# Endpoint: /archive/{archiveId}, method: Put
request = requests.Request([
    primitives.restler_static_string("PUT "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("archive"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload_uuid4_suffix("archiveId", quoted=False),
    primitives.restler_static_string("?"),
    primitives.restler_static_string("sig="),
    primitives.restler_static_string(_archive_post_hash_query.reader(), quoted=False),
    primitives.restler_static_string("&"),
    primitives.restler_static_string("hash="),
    primitives.restler_custom_payload_query("hash"),
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
    "name":"""),
    primitives.restler_static_string(_archive_post_name.reader(), quoted=False),
    primitives.restler_static_string(""",
    "tag":"""),
    primitives.restler_static_string(_archive_post_tag.reader(), quoted=True),
    primitives.restler_static_string("}"),
    primitives.restler_static_string("\r\n"),

],
requestId="/archive/{archiveId}"
)
req_collection.add_request(request)

# Endpoint: /file/{fileId}, method: Post
request = requests.Request([
    primitives.restler_static_string("POST "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("file"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload_uuid4_suffix("fileId", writer=_file__fileId__post_fileId_path.writer(), quoted=False),
    primitives.restler_static_string("?"),
    primitives.restler_static_string("hash="),
    primitives.restler_custom_payload_query("hash"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),
    
    {

        'post_send':
        {
            
            'dependencies':
            [
                _file__fileId__post_fileId_path.writer()
            ]
        }

    },

],
requestId="/file/{fileId}"
)
req_collection.add_request(request)

# Endpoint: /file/{fileId}, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("file"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string(_file__fileId__post_fileId_path.reader(), quoted=False),
    primitives.restler_static_string("?"),
    primitives.restler_static_string("hash="),
    primitives.restler_custom_payload_query("hash"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/file/{fileId}"
)
req_collection.add_request(request)

# Endpoint: /file/{fileId}, method: Delete
request = requests.Request([
    primitives.restler_static_string("DELETE "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("file"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string(_file__fileId__post_fileId_path.reader(), quoted=False),
    primitives.restler_static_string("?"),
    primitives.restler_static_string("hash="),
    primitives.restler_custom_payload_query("hash"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/file/{fileId}"
)
req_collection.add_request(request)
