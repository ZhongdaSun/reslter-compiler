""" THIS IS AN AUTOMATICALLY GENERATED FILE!"""
from __future__ import print_function
import json
import json
from restler.engine import primitives
from restler.engine.core import requests
from restler.engine.errors import ResponseParsingException
from restler.engine import dependencies

_api_dataItem__dataIteMName__dataPoints__dataPointName__metadata_post_id = dependencies.DynamicVariable("_api_dataItem__dataIteMName__dataPoints__dataPointName__metadata_post_id")

_api_dataItem__dataITeMName__dataPoints__dataPOInTName__put_name = dependencies.DynamicVariable("_api_dataItem__dataITeMName__dataPoints__dataPOInTName__put_name")

_api_dataItem__dataItemName__put_name = dependencies.DynamicVariable("_api_dataItem__dataItemName__put_name")

def parse_apidataItemdataIteMNamedataPointsdataPointNamemetadatapost(data, **kwargs):
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
        dependencies.set_variable("_api_dataItem__dataIteMName__dataPoints__dataPointName__metadata_post_id", temp_7262)


def parse_apidataItemdataITeMNamedataPointsdataPOInTNameput(data, **kwargs):
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
            temp_8173 = str(data["name"])
            
        except Exception as error:
            # This is not an error, since some properties are not always returned
            pass



    # If no dynamic objects were extracted, throw.
    if not (temp_8173):
        raise ResponseParsingException("Error: all of the expected dynamic objects were not present in the response.")

    # Set dynamic variables
    if temp_8173:
        dependencies.set_variable("_api_dataItem__dataITeMName__dataPoints__dataPOInTName__put_name", temp_8173)


def parse_apidataItemdataItemNameput(data, **kwargs):
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
            temp_7680 = str(data["name"])
            
        except Exception as error:
            # This is not an error, since some properties are not always returned
            pass



    # If no dynamic objects were extracted, throw.
    if not (temp_7680):
        raise ResponseParsingException("Error: all of the expected dynamic objects were not present in the response.")

    # Set dynamic variables
    if temp_7680:
        dependencies.set_variable("_api_dataItem__dataItemName__put_name", temp_7680)

req_collection = requests.RequestCollection([])
# Endpoint: /api/dataItem/{dataITEMName}/dataPoints/{dataPOIntName}/metadata/{id}, method: Get
request = requests.Request([
    primitives.restler_static_string("GET "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("dataItem"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string(_api_dataItem__dataItemName__put_name.reader(), quoted=False),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("dataPoints"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string(_api_dataItem__dataITeMName__dataPoints__dataPOInTName__put_name.reader(), quoted=False),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("metadata"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string(_api_dataItem__dataIteMName__dataPoints__dataPointName__metadata_post_id.reader(), quoted=False),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),

],
requestId="/api/dataItem/{dataITEMName}/dataPoints/{dataPOIntName}/metadata/{id}"
)
req_collection.add_request(request)

# Endpoint: /api/dataItem/{dataIteMName}/dataPoints/{dataPointName}/metadata, method: Post
request = requests.Request([
    primitives.restler_static_string("POST "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("dataItem"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string(_api_dataItem__dataItemName__put_name.reader(), quoted=False),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("dataPoints"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string(_api_dataItem__dataITeMName__dataPoints__dataPOInTName__put_name.reader(), quoted=False),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("metadata"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),
    
    {

        'post_send':
        {
            'parser': parse_apidataItemdataIteMNamedataPointsdataPointNamemetadatapost,
            'dependencies':
            [
                _api_dataItem__dataIteMName__dataPoints__dataPointName__metadata_post_id.writer()
            ]
        }

    },

],
requestId="/api/dataItem/{dataIteMName}/dataPoints/{dataPointName}/metadata"
)
req_collection.add_request(request)

# Endpoint: /api/dataItem/{dataITeMName}/dataPoints/{dataPOInTName}, method: Put
request = requests.Request([
    primitives.restler_static_string("PUT "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("dataItem"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string(_api_dataItem__dataItemName__put_name.reader(), quoted=False),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("dataPoints"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload_uuid4_suffix("dataPOInTName", quoted=False),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),
    
    {

        'post_send':
        {
            'parser': parse_apidataItemdataITeMNamedataPointsdataPOInTNameput,
            'dependencies':
            [
                _api_dataItem__dataITeMName__dataPoints__dataPOInTName__put_name.writer()
            ]
        }

    },

],
requestId="/api/dataItem/{dataITeMName}/dataPoints/{dataPOInTName}"
)
req_collection.add_request(request)

# Endpoint: /api/dataItem/{dataItemName}, method: Put
request = requests.Request([
    primitives.restler_static_string("PUT "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("dataItem"),
    primitives.restler_static_string("/"),
    primitives.restler_custom_payload_uuid4_suffix("dataItemName", quoted=False),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),
    
    {

        'post_send':
        {
            'parser': parse_apidataItemdataItemNameput,
            'dependencies':
            [
                _api_dataItem__dataItemName__put_name.writer()
            ]
        }

    },

],
requestId="/api/dataItem/{dataItemName}"
)
req_collection.add_request(request)
