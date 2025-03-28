""" THIS IS AN AUTOMATICALLY GENERATED FILE!"""
from __future__ import print_function
import json
from restler.engine import primitives
from restler.engine.core import requests
from restler.engine.errors import ResponseParsingException
from restler.engine import dependencies

_stores__storeId__order_post_id = dependencies.DynamicVariable("_stores__storeId__order_post_id")

_stores__storeId__order_post_order_items = dependencies.DynamicVariable("_stores__storeId__order_post_order_items")

_stores__storeId__order_post_order_items_0 = dependencies.DynamicVariable("_stores__storeId__order_post_order_items_0")

def parse_storesstoreIdorderpost(data, **kwargs):
    """ Automatically generated response parser """
    # Declare response variables
    temp_7262 = None
    temp_8173 = None
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
            temp_7262 = str(data["id"])
            
        except Exception as error:
            # This is not an error, since some properties are not always returned
            pass


        try:
            temp_8173 = str(data["order_items"])
            
        except Exception as error:
            # This is not an error, since some properties are not always returned
            pass


        try:
            temp_7680 = str(data["order_items"][0])
            
        except Exception as error:
            # This is not an error, since some properties are not always returned
            pass



    # If no dynamic objects were extracted, throw.
    if not (temp_7262 or temp_8173 or temp_7680):
        raise ResponseParsingException("Error: all of the expected dynamic objects were not present in the response.")

    # Set dynamic variables
    if temp_7262:
        dependencies.set_variable("_stores__storeId__order_post_id", temp_7262)
    if temp_8173:
        dependencies.set_variable("_stores__storeId__order_post_order_items", temp_8173)
    if temp_7680:
        dependencies.set_variable("_stores__storeId__order_post_order_items_0", temp_7680)

req_collection = requests.RequestCollection([])
# Endpoint: /stores, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("stores"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/stores"
)
req_collection.add_request(request)

# Endpoint: /stores/{storeId}/order, method: Post
request = requests.Request([
    primitives.restler_static_string("POST "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("stores"),
    primitives.restler_static_string("/"),
    primitives.restler_fuzzable_int("1"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("order"),
    primitives.restler_static_string("?"),
    primitives.restler_static_string("apiVersion="),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False, examples=["2020-02-02"]),
    primitives.restler_static_string("&"),
    primitives.restler_static_string("expiration="),
    primitives.restler_fuzzable_int("1", examples=["10"]),
    primitives.restler_static_string("&"),
    primitives.restler_static_string("arrayQueryParameter="),
    primitives.restler_static_string("&"),
    primitives.restler_static_string("arrayQueryParameter2="),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False, examples=["a"]),
    primitives.restler_static_string("&"),
    primitives.restler_static_string("arrayQueryParameter2="),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False, examples=["b"]),
    primitives.restler_static_string("&"),
    primitives.restler_static_string("arrayQueryParameter2="),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False, examples=["c"]),
    primitives.restler_static_string("&"),
    primitives.restler_static_string("arrayQueryParameter3="),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False, examples=["ddd"]),
    primitives.restler_static_string(","),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False, examples=["eee"]),
    primitives.restler_static_string(","),
    primitives.restler_fuzzable_string("fuzzstring", quoted=False, examples=["fff"]),
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
    "storeId":"""),
    primitives.restler_fuzzable_int("1", examples=["23456"]),
    primitives.restler_static_string(""",
    "rush":"""),
    primitives.restler_fuzzable_bool("true", examples=["true"]),
    primitives.restler_static_string(""",
    "bagType":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True, examples=["paperfestive"]),
    primitives.restler_static_string(""",
    "item_descriptions":
    [
    ],
    "item_feedback":
    [
        """),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True, examples=["great"]),
    primitives.restler_static_string(""",
        """),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True, examples=["awesome"]),
    primitives.restler_static_string("""
    ]}"""),
    primitives.restler_static_string("\r\n"),
    
    {

        'post_send':
        {
            'parser': parse_storesstoreIdorderpost,
            'dependencies':
            [
                _stores__storeId__order_post_id.writer(),
                _stores__storeId__order_post_order_items.writer(),
                _stores__storeId__order_post_order_items_0.writer()
            ]
        }

    },

],
requestId="/stores/{storeId}/order"
)
req_collection.add_request(request)

# Endpoint: /stores/{storeId}/order/{orderId}, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("stores"),
    primitives.restler_static_string("/"),
    primitives.restler_fuzzable_int("1"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("order"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string(_stores__storeId__order_post_id.reader(), quoted=False),
    primitives.restler_static_string("?"),
    primitives.restler_static_string("arrayQueryParameter99="),
    primitives.restler_static_string(_stores__storeId__order_post_order_items.reader(), quoted=False),
    primitives.restler_static_string("&"),
    primitives.restler_static_string("stringQueryParameter77="),
    primitives.restler_static_string(_stores__storeId__order_post_order_items_0.reader(), quoted=False),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/stores/{storeId}/order/{orderId}"
)
req_collection.add_request(request)
