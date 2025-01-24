""" THIS IS AN AUTOMATICALLY GENERATED FILE!"""
from __future__ import print_function
import json
from rest.restler.engine import primitives
from rest.restler.engine.core import requests
from rest.restler.engine.errors import ResponseParsingException
from rest.restler.engine import dependencies

_first_post_id = dependencies.DynamicVariable("_first_post_id")

_second_post_id = dependencies.DynamicVariable("_second_post_id")

_third_post_id = dependencies.DynamicVariable("_third_post_id")

def parse_firstpost(data, **kwargs):
    """ Automatically generated response parser """
    # Declare response variables
    temp_7262 = None

    if 'headers' in kwargs:
        headers = kwargs['headers']


    # Parse body if needed
    if data:

        try:
            data = json.loads(data)
        except Exception as error:
            raise ResponseParsingException("Exception parsing response, data was not valid json: {}".format(error))
        pass

    # Try to extract each dynamic object

        try:
            temp_7262 = str(data["id"])
            
        except Exception as error:
            # This is not an error, since some properties are not always returned
            pass



    # If no dynamic objects were extracted, throw.
    if not (temp_7262):
        raise ResponseParsingException("Error: all of the expected dynamic objects were not present in the response.")

    # Set dynamic variables
    if temp_7262:
        dependencies.set_variable("_first_post_id", temp_7262)


def parse_secondpost(data, **kwargs):
    """ Automatically generated response parser """
    # Declare response variables
    temp_8173 = None

    if 'headers' in kwargs:
        headers = kwargs['headers']


    # Parse body if needed
    if data:

        try:
            data = json.loads(data)
        except Exception as error:
            raise ResponseParsingException("Exception parsing response, data was not valid json: {}".format(error))
        pass

    # Try to extract each dynamic object

        try:
            temp_8173 = str(data["id"])
            
        except Exception as error:
            # This is not an error, since some properties are not always returned
            pass



    # If no dynamic objects were extracted, throw.
    if not (temp_8173):
        raise ResponseParsingException("Error: all of the expected dynamic objects were not present in the response.")

    # Set dynamic variables
    if temp_8173:
        dependencies.set_variable("_second_post_id", temp_8173)


def parse_thirdpost(data, **kwargs):
    """ Automatically generated response parser """
    # Declare response variables
    temp_7680 = None

    if 'headers' in kwargs:
        headers = kwargs['headers']


    # Parse body if needed
    if data:

        try:
            data = json.loads(data)
        except Exception as error:
            raise ResponseParsingException("Exception parsing response, data was not valid json: {}".format(error))
        pass

    # Try to extract each dynamic object

        try:
            temp_7680 = str(data["id"])
            
        except Exception as error:
            # This is not an error, since some properties are not always returned
            pass



    # If no dynamic objects were extracted, throw.
    if not (temp_7680):
        raise ResponseParsingException("Error: all of the expected dynamic objects were not present in the response.")

    # Set dynamic variables
    if temp_7680:
        dependencies.set_variable("_third_post_id", temp_7680)

req_collection = requests.RequestCollection([])
# Endpoint: /first, method: Post
request = requests.Request([
    primitives.restler_static_string("POST "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("first"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),
    
    {

        'post_send':
        {
            'parser': parse_firstpost,
            'dependencies':
            [
                _first_post_id.writer()
            ]
        }

    },

],
requestId="/first"
)
req_collection.add_request(request)

# Endpoint: /first/{storeId}/order/{orderId}, method: Put
request = requests.Request([
    primitives.restler_static_string("PUT "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("first"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string(_first_post_id.reader(), quoted=False),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("order"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload_uuid4_suffix("orderId", quoted=False),
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
    "tags":"""),
    primitives.restler_fuzzable_object("{ \"fuzz\": false }"),
    primitives.restler_static_string(""",
    "storeId":"""),
    primitives.restler_fuzzable_int("1"),
    primitives.restler_static_string(""",
    "storeProperties":
        {
            "tags":"""),
    primitives.restler_custom_payload("/storeProperties/tags", quoted=False),
    primitives.restler_static_string("""
        }
    ,
    "deliveryProperties":
        {
            "tags":"""),
    primitives.restler_fuzzable_object("{ \"fuzz\": false }"),
    primitives.restler_static_string("""
        }
    ,
    "rush":"""),
    primitives.restler_fuzzable_bool("true"),
    primitives.restler_static_string(""",
    "bagType":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
    "items":
    [
        {
            "name":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
            "deliveryTags":"""),
    primitives.restler_custom_payload("/items/[0]/deliveryTags", quoted=False),
    primitives.restler_static_string(""",
            "code":"""),
    primitives.restler_fuzzable_int("1"),
    primitives.restler_static_string(""",
            "storeId":"""),
    primitives.restler_fuzzable_int("1"),
    primitives.restler_static_string(""",
            "expirationMaxDate":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
            "banana":"""),
    primitives.restler_custom_payload("banana", quoted=True),
    primitives.restler_static_string("""
        }
    ],
    "useDoubleBags":"""),
    primitives.restler_fuzzable_bool("true"),
    primitives.restler_static_string(""",
    "bannedBrands":
    [
        """),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string("""
    ]}"""),
    primitives.restler_static_string("\r\n"),

],
requestId="/first/{storeId}/order/{orderId}"
)
req_collection.add_request(request)

# Endpoint: /second, method: Post
request = requests.Request([
    primitives.restler_static_string("POST "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("second"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),
    
    {

        'post_send':
        {
            'parser': parse_secondpost,
            'dependencies':
            [
                _second_post_id.writer()
            ]
        }

    },

],
requestId="/second"
)
req_collection.add_request(request)

# Endpoint: /second/{storeId}/order, method: Post
request = requests.Request([
    primitives.restler_static_string("POST "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("second"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string(_second_post_id.reader(), quoted=False),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("order"),
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
    "tags":"""),
    primitives.restler_fuzzable_object("{ \"fuzz\": false }"),
    primitives.restler_static_string(""",
    "storeId":"""),
    primitives.restler_fuzzable_int("1"),
    primitives.restler_static_string(""",
    "storeProperties":
        {
            "tags":"""),
    primitives.restler_custom_payload("/storeProperties/tags", quoted=False),
    primitives.restler_static_string("""
        }
    ,
    "deliveryProperties":
        {
            "tags":"""),
    primitives.restler_fuzzable_object("{ \"fuzz\": false }"),
    primitives.restler_static_string("""
        }
    ,
    "rush":"""),
    primitives.restler_fuzzable_bool("true"),
    primitives.restler_static_string(""",
    "bagType":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
    "items":
    [
        {
            "name":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
            "deliveryTags":"""),
    primitives.restler_custom_payload("/items/[0]/deliveryTags", quoted=False),
    primitives.restler_static_string(""",
            "code":"""),
    primitives.restler_fuzzable_int("1"),
    primitives.restler_static_string(""",
            "storeId":"""),
    primitives.restler_fuzzable_int("1"),
    primitives.restler_static_string(""",
            "expirationMaxDate":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
            "apple":"""),
    primitives.restler_custom_payload("apple", quoted=True),
    primitives.restler_static_string("""
        }
    ],
    "useDoubleBags":"""),
    primitives.restler_fuzzable_bool("true"),
    primitives.restler_static_string(""",
    "bannedBrands":
    [
        """),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string("""
    ]}"""),
    primitives.restler_static_string("\r\n"),

],
requestId="/second/{storeId}/order"
)
req_collection.add_request(request)

# Endpoint: /third, method: Post
request = requests.Request([
    primitives.restler_static_string("POST "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("third"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),
    
    {

        'post_send':
        {
            'parser': parse_thirdpost,
            'dependencies':
            [
                _third_post_id.writer()
            ]
        }

    },

],
requestId="/third"
)
req_collection.add_request(request)

# Endpoint: /third/{storeId}/order, method: Post
request = requests.Request([
    primitives.restler_static_string("POST "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("third"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string(_third_post_id.reader(), quoted=False),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("order"),
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
    "tags":"""),
    primitives.restler_fuzzable_object("{ \"fuzz\": false }"),
    primitives.restler_static_string(""",
    "storeId":"""),
    primitives.restler_fuzzable_int("1"),
    primitives.restler_static_string(""",
    "storeProperties":
        {
            "tags":"""),
    primitives.restler_custom_payload("/storeProperties/tags", quoted=False),
    primitives.restler_static_string("""
        }
    ,
    "deliveryProperties":
        {
            "tags":"""),
    primitives.restler_fuzzable_object("{ \"fuzz\": false }"),
    primitives.restler_static_string("""
        }
    ,
    "rush":"""),
    primitives.restler_fuzzable_bool("true"),
    primitives.restler_static_string(""",
    "bagType":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
    "items":
    [
        {
            "name":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
            "deliveryTags":"""),
    primitives.restler_custom_payload("/items/[0]/deliveryTags", quoted=False),
    primitives.restler_static_string(""",
            "code":"""),
    primitives.restler_fuzzable_int("1"),
    primitives.restler_static_string(""",
            "storeId":"""),
    primitives.restler_fuzzable_int("1"),
    primitives.restler_static_string(""",
            "expirationMaxDate":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
            "banana":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
            "apple":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string("""
        }
    ],
    "useDoubleBags":"""),
    primitives.restler_fuzzable_bool("true"),
    primitives.restler_static_string(""",
    "bannedBrands":
    [
        """),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string("""
    ]}"""),
    primitives.restler_static_string("\r\n"),

],
requestId="/third/{storeId}/order"
)
req_collection.add_request(request)
