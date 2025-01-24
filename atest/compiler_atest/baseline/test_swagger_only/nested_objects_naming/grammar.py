""" THIS IS AN AUTOMATICALLY GENERATED FILE!"""
from __future__ import print_function
import json
from rest.restler.engine import primitives
from rest.restler.engine.core import requests
from rest.restler.engine.errors import ResponseParsingException
from rest.restler.engine import dependencies

_virtualNetworkTaps__tapName__put_id = dependencies.DynamicVariable("_virtualNetworkTaps__tapName__put_id")

_publicIPAddresses__publicIpAddressName__put_id = dependencies.DynamicVariable("_publicIPAddresses__publicIpAddressName__put_id")

def parse_virtualNetworkTapstapNameput(data, **kwargs):
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
        dependencies.set_variable("_virtualNetworkTaps__tapName__put_id", temp_7262)


def parse_publicIPAddressespublicIpAddressNameput(data, **kwargs):
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
        dependencies.set_variable("_publicIPAddresses__publicIpAddressName__put_id", temp_8173)

req_collection = requests.RequestCollection([])
# Endpoint: /virtualNetworkTaps/{tapName}, method: Put
request = requests.Request([
    primitives.restler_static_string("PUT "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("virtualNetworkTaps"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload_uuid4_suffix("tapName", quoted=False),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),
    
    {

        'post_send':
        {
            'parser': parse_virtualNetworkTapstapNameput,
            'dependencies':
            [
                _virtualNetworkTaps__tapName__put_id.writer()
            ]
        }

    },

],
requestId="/virtualNetworkTaps/{tapName}"
)
req_collection.add_request(request)

# Endpoint: /publicIPAddresses/{publicIpAddressName}, method: Put
request = requests.Request([
    primitives.restler_static_string("PUT "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("publicIPAddresses"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload_uuid4_suffix("publicIpAddressName", quoted=False),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),
    
    {

        'post_send':
        {
            'parser': parse_publicIPAddressespublicIpAddressNameput,
            'dependencies':
            [
                _publicIPAddresses__publicIpAddressName__put_id.writer()
            ]
        }

    },

],
requestId="/publicIPAddresses/{publicIpAddressName}"
)
req_collection.add_request(request)

# Endpoint: /vtap/{tapConfigurationName}, method: Put
request = requests.Request([
    primitives.restler_static_string("PUT "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("vtap"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload_uuid4_suffix("tapConfigurationName", quoted=False),
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
            "virtualNetworkTap":
                {
                    "id":"""),
    primitives.restler_static_string(_virtualNetworkTaps__tapName__put_id.reader(), quoted=True),
    primitives.restler_static_string("""
                }
        }
    }"""),
    primitives.restler_static_string("\r\n"),

],
requestId="/vtap/{tapConfigurationName}"
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
            "frontendIPConfigurations":
            [
                {
                    "properties":
                        {
                            "privateIPAddress":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
                            "privateIPAllocationMethod":"""),
    primitives.restler_fuzzable_group("privateIPAllocationMethod", ['Static','Dynamic']  ,quoted=True),
    primitives.restler_static_string(""",
                            "subnet":
                                {
                                    "id":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string("""
                                }
                            ,
                            "publicIPAddress":
                                {
                                    "id":"""),
    primitives.restler_static_string(_publicIPAddresses__publicIpAddressName__put_id.reader(), quoted=True),
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
