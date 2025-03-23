""" THIS IS AN AUTOMATICALLY GENERATED FILE!"""
from __future__ import print_function
import json
from restler.engine import primitives
from restler.engine.core import requests
from restler.engine.errors import ResponseParsingException
from restler.engine import dependencies

_subnets__subnetName__put_id = dependencies.DynamicVariable("_subnets__subnetName__put_id")

_subnets__subnetName__put_name = dependencies.DynamicVariable("_subnets__subnetName__put_name")

def parse_subnetssubnetNameput(data, **kwargs):
    """ Automatically generated response parser """
    # Declare response variables
    temp_7262 = None
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
            temp_7262 = str(data["id"])
            
        except Exception as error:
            # This is not an error, since some properties are not always returned
            pass


        try:
            temp_8173 = str(data["name"])
            
        except Exception as error:
            # This is not an error, since some properties are not always returned
            pass



    # If no dynamic objects were extracted, throw.
    if not (temp_7262 or temp_8173):
        raise ResponseParsingException("Error: all of the expected dynamic objects were not present in the response.")

    # Set dynamic variables
    if temp_7262:
        dependencies.set_variable("_subnets__subnetName__put_id", temp_7262)
    if temp_8173:
        dependencies.set_variable("_subnets__subnetName__put_name", temp_8173)

req_collection = requests.RequestCollection([])
# Endpoint: /subnets/{subnetName}, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("subnets"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string(_subnets__subnetName__put_name.reader(), quoted=False),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/subnets/{subnetName}"
)
req_collection.add_request(request)

# Endpoint: /subnets/{subnetName}, method: Put
request = requests.Request([
    primitives.restler_static_string("PUT "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("subnets"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload_uuid4_suffix("subnetName", quoted=False),
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
    "properties":
        {
            "addressPrefix":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
            "nullProperty":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
            "intProperty":"""),
    primitives.restler_fuzzable_int("1"),
    primitives.restler_static_string(""",
            "emptyProperty":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string("""
        }
    ,
    "name":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
    "id":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string("}"),
    primitives.restler_static_string("\r\n"),
    
    {

        'post_send':
        {
            'parser': parse_subnetssubnetNameput,
            'dependencies':
            [
                _subnets__subnetName__put_id.writer(),
                _subnets__subnetName__put_name.writer()
            ]
        }

    },

],
requestId="/subnets/{subnetName}"
)
req_collection.add_request(request)

# Endpoint: /applicationGateways/{applicationGatewayName}, method: Put
request = requests.Request([
    primitives.restler_static_string("PUT "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("applicationGateways"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload_uuid4_suffix("applicationGatewayName", quoted=False),
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
    "properties":
        {
            "gatewayIPConfigurations":
            [
                {
                    "properties":
                        {
                            "subnet":
                                {
                                    "id":"""),
    primitives.restler_static_string(_subnets__subnetName__put_id.reader(), quoted=True),
    primitives.restler_static_string("""
                                }
                            ,
                            "provisioningState":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string("""
                        }
                    ,
                    "name":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
                    "etag":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
                    "type":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string("""
                }
            ]
        }
    }"""),
    primitives.restler_static_string("\r\n"),

],
requestId="/applicationGateways/{applicationGatewayName}"
)
req_collection.add_request(request)

# Endpoint: /virtualNetworks/{virtualNetworkName}, method: Put
request = requests.Request([
    primitives.restler_static_string("PUT "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("virtualNetworks"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload_uuid4_suffix("virtualNetworkName", quoted=False),
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
    "subnets":
    [
        {
            "properties":
                {
                    "addressPrefix":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
                    "nullProperty":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
                    "intProperty":"""),
    primitives.restler_fuzzable_int("1"),
    primitives.restler_static_string(""",
                    "emptyProperty":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string("""
                }
            ,
            "name":"""),
    primitives.restler_static_string(_subnets__subnetName__put_name.reader(), quoted=True),
    primitives.restler_static_string(""",
            "id":"""),
    primitives.restler_static_string(_subnets__subnetName__put_id.reader(), quoted=True),
    primitives.restler_static_string("""
        }
    ]}"""),
    primitives.restler_static_string("\r\n"),

],
requestId="/virtualNetworks/{virtualNetworkName}"
)
req_collection.add_request(request)
