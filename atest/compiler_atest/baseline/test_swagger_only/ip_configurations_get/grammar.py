""" THIS IS AN AUTOMATICALLY GENERATED FILE!"""
from __future__ import print_function
import json
from restler.engine import primitives
from restler.engine.core import requests
from restler.engine.errors import ResponseParsingException
from restler.engine import dependencies

_networkInterfaces__networkInterfaceName__put_name = dependencies.DynamicVariable("_networkInterfaces__networkInterfaceName__put_name")

_networkInterfaces__networkInterfaceName__put_properties_ipConfigurations_0_name = dependencies.DynamicVariable("_networkInterfaces__networkInterfaceName__put_properties_ipConfigurations_0_name")

_subnets__subnetName__put_id = dependencies.DynamicVariable("_subnets__subnetName__put_id")

_subnets__subnetName__put_name = dependencies.DynamicVariable("_subnets__subnetName__put_name")

def parse_networkInterfacesnetworkInterfaceNameput(data, **kwargs):
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
            temp_7262 = str(data["name"])
            
        except Exception as error:
            # This is not an error, since some properties are not always returned
            pass


        try:
            temp_8173 = str(data["properties"]["ipConfigurations"][0]["name"])
            
        except Exception as error:
            # This is not an error, since some properties are not always returned
            pass



    # If no dynamic objects were extracted, throw.
    if not (temp_7262 or temp_8173):
        raise ResponseParsingException("Error: all of the expected dynamic objects were not present in the response.")

    # Set dynamic variables
    if temp_7262:
        dependencies.set_variable("_networkInterfaces__networkInterfaceName__put_name", temp_7262)
    if temp_8173:
        dependencies.set_variable("_networkInterfaces__networkInterfaceName__put_properties_ipConfigurations_0_name", temp_8173)


def parse_subnetssubnetNameput(data, **kwargs):
    """ Automatically generated response parser """
    # Declare response variables
    temp_7680 = None
    temp_5581 = None

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


        try:
            temp_5581 = str(data["name"])
            
        except Exception as error:
            # This is not an error, since some properties are not always returned
            pass



    # If no dynamic objects were extracted, throw.
    if not (temp_7680 or temp_5581):
        raise ResponseParsingException("Error: all of the expected dynamic objects were not present in the response.")

    # Set dynamic variables
    if temp_7680:
        dependencies.set_variable("_subnets__subnetName__put_id", temp_7680)
    if temp_5581:
        dependencies.set_variable("_subnets__subnetName__put_name", temp_5581)

req_collection = requests.RequestCollection([])
# Endpoint: /networkInterfaces/{networkInterfaceName}, method: Put
request = requests.Request([
    primitives.restler_static_string("PUT "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("networkInterfaces"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload_uuid4_suffix("networkInterfaceName", quoted=False),
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
            "virtualMachine":
                {
                    "id":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string("""
                }
            ,
            "ipConfigurations":
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
                            "privateIPAddressVersion":"""),
    primitives.restler_fuzzable_group("privateIPAddressVersion", ['IPv4','IPv6']  ,quoted=True),
    primitives.restler_static_string(""",
                            "subnet":
                                {
                                    "properties":
                                        {
                                            "addressPrefix":"""),
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
                            ,
                            "primary":"""),
    primitives.restler_fuzzable_bool("true"),
    primitives.restler_static_string(""",
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
                    "id":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string("""
                }
            ],
            "macAddress":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
            "primary":"""),
    primitives.restler_fuzzable_bool("true"),
    primitives.restler_static_string(""",
            "enableAcceleratedNetworking":"""),
    primitives.restler_fuzzable_bool("true"),
    primitives.restler_static_string(""",
            "enableIPForwarding":"""),
    primitives.restler_fuzzable_bool("true"),
    primitives.restler_static_string(""",
            "resourceGuid":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
            "provisioningState":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string("""
        }
    ,
    "etag":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
    "id":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
    "location":"""),
    primitives.restler_fuzzable_string("fuzzstring", quoted=True),
    primitives.restler_static_string(""",
    "tags":"""),
    primitives.restler_fuzzable_object("{ \"fuzz\": false }"),
    primitives.restler_static_string("}"),
    primitives.restler_static_string("\r\n"),
    
    {

        'post_send':
        {
            'parser': parse_networkInterfacesnetworkInterfaceNameput,
            'dependencies':
            [
                _networkInterfaces__networkInterfaceName__put_name.writer(),
                _networkInterfaces__networkInterfaceName__put_properties_ipConfigurations_0_name.writer()
            ]
        }

    },

],
requestId="/networkInterfaces/{networkInterfaceName}"
)
req_collection.add_request(request)

# Endpoint: /networkInterfaces/{networkInterfaceName}/ipConfigurations/{ipConfigurationName}, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("networkInterfaces"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string(_networkInterfaces__networkInterfaceName__put_name.reader(), quoted=False),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("ipConfigurations"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string(_networkInterfaces__networkInterfaceName__put_properties_ipConfigurations_0_name.reader(), quoted=False),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/networkInterfaces/{networkInterfaceName}/ipConfigurations/{ipConfigurationName}"
)
req_collection.add_request(request)

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
