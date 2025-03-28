""" THIS IS AN AUTOMATICALLY GENERATED FILE!"""
from __future__ import print_function
import json
from restler.engine import primitives
from restler.engine.core import requests
from restler.engine.errors import ResponseParsingException
from restler.engine import dependencies

_system_environments_post_id = dependencies.DynamicVariable("_system_environments_post_id")

_system_environments_post_name = dependencies.DynamicVariable("_system_environments_post_name")

_system_environments_post_url = dependencies.DynamicVariable("_system_environments_post_url")

def parse_systemenvironmentspost(data, **kwargs):
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
            temp_8173 = str(data["name"])
            
        except Exception as error:
            # This is not an error, since some properties are not always returned
            pass


        try:
            temp_7680 = str(data["url"])
            
        except Exception as error:
            # This is not an error, since some properties are not always returned
            pass



    # If no dynamic objects were extracted, throw.
    if not (temp_7262 or temp_8173 or temp_7680):
        raise ResponseParsingException("Error: all of the expected dynamic objects were not present in the response.")

    # Set dynamic variables
    if temp_7262:
        dependencies.set_variable("_system_environments_post_id", temp_7262)
    if temp_8173:
        dependencies.set_variable("_system_environments_post_name", temp_8173)
    if temp_7680:
        dependencies.set_variable("_system_environments_post_url", temp_7680)

req_collection = requests.RequestCollection([])
# Endpoint: /system-environments, method: Post
request = requests.Request([
    primitives.restler_static_string("POST "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("system-environments"),
    primitives.restler_static_string(" HTTP/1.1\r\n"),
    primitives.restler_static_string("Accept: application/json\r\n"),
    primitives.restler_static_string("Host: localhost:8888\r\n"),
    primitives.restler_refreshable_authentication_token("authentication_token_tag"),
    primitives.restler_static_string("\r\n"),
    
    {

        'post_send':
        {
            'parser': parse_systemenvironmentspost,
            'dependencies':
            [
                _system_environments_post_id.writer(),
                _system_environments_post_name.writer(),
                _system_environments_post_url.writer()
            ]
        }

    },

],
requestId="/system-environments"
)
req_collection.add_request(request)

# Endpoint: /system-environments/{system-environment-id}, method: Patch
request = requests.Request([
    primitives.restler_static_string("PATCH "),
    primitives.restler_basepath("/api"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string("system-environments"),
    primitives.restler_static_string("/"),
    primitives.restler_static_string(_system_environments_post_id.reader(), quoted=False),
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
    primitives.restler_static_string(_system_environments_post_name.reader(), quoted=True),
    primitives.restler_static_string(""",
    "image_url":"""),
    primitives.restler_static_string(_system_environments_post_url.reader(), quoted=True),
    primitives.restler_static_string("}"),
    primitives.restler_static_string("\r\n"),

],
requestId="/system-environments/{system-environment-id}"
)
req_collection.add_request(request)
