from __future__ import absolute_import
from rest.swagger.base import BaseObj, FieldMeta
from rest.restler.utils import restler_logger as logger
import six


# *******change logger*******
# add "type" in response
# add "example" in BaseSchema.
class BaseObj_v2_0(BaseObj):
    __swagger_version__ = '2.0'


class XMLObject(six.with_metaclass(FieldMeta, BaseObj_v2_0)):
    """ XML Object
    """
    __swagger_fields__ = {
        'name': None,
        'namespace': None,
        'prefix': None,
        'attribute': None,
        'wrapped': None,
    }


class BaseSchema(BaseObj_v2_0):
    """ Base type for Items, Schema, Parameter, Header
    """

    __swagger_fields__ = {
        'type': None,
        'format': None,
        'items': None,
        'default': None,
        'maximum': None,
        'exclusiveMaximum': None,
        'minimum': None,
        'exclusiveMinimum': None,
        'maxLength': None,
        'minLength': None,
        'maxItems': None,
        'minItems': None,
        'multipleOf': None,
        'enum': None,
        'pattern': None,
        'uniqueItems': None,
        'example': None,  # swagger has inline example in parameters.
        'examples': None,
    }


class Items(six.with_metaclass(FieldMeta, BaseSchema)):
    """ Items Object
    """

    __swagger_fields__ = {
        'collectionFormat': 'csv',
    }

    def _prim_(self, v, prim_factory, ctx=None):
        return prim_factory.produce(self, v, ctx)


class Schema(six.with_metaclass(FieldMeta, BaseSchema)):
    """ Schema Object
    """

    __swagger_fields__ = {
        '$ref': None,
        'maxProperties': None,
        'minProperties': None,
        'required': [],
        'allOf': [],
        'properties': {},
        'additionalProperties': None,
        'title': None,
        'description': None,
        'discriminator': None,
        'readOnly': None,
        'readonly': None,
        'xml': None,
        'externalDocs': None,
    }

    __internal_fields__ = {
        # pyswagger only
        'ref_obj': None,
        'final': None,
        'name': None,
    }

    def _prim_(self, v, prim_factory, ctx=None):
        return prim_factory.produce(self, v, ctx)


class Swagger(six.with_metaclass(FieldMeta, BaseObj_v2_0)):
    """ Swagger Object
    """

    __swagger_fields__ = {
        'swagger': None,
        'info': None,
        'host': None,
        'basePath': None,
        'schemes': [],
        'consumes': [],
        'produces': [],
        'paths': None,
        'x-ms-paths': None,
        'definitions': None,
        'parameters': None,
        'responses': None,
        'securityDefinitions': None,
        'security': None,
        'tags': None,
        'externalDocs': None,
        'x-restler-global-annotations': []
    }


class Contact(six.with_metaclass(FieldMeta, BaseObj_v2_0)):
    """ Contact Object
    """

    __swagger_fields__ = {
        'name': None,
        'url': None,
        'email': None,
    }


class License(six.with_metaclass(FieldMeta, BaseObj_v2_0)):
    """ License Object
    """

    __swagger_fields__ = {
        'name': None,
        'url': None,
    }


class Info(six.with_metaclass(FieldMeta, BaseObj_v2_0)):
    """ Info Object
    """

    __swagger_fields__ = {
        'version': None,
        'title': None,
        'description': None,
        'termsOfService': None,
        'contact': None,
        'license': None,
    }


class Parameter(six.with_metaclass(FieldMeta, BaseSchema)):
    """ Parameter Object
    """

    __swagger_fields__ = {
        # Reference Object
        '$ref': None,

        'name': None,
        'in': None,
        'required': None,

        # body parameter
        'schema': None,

        # other parameter
        'collectionFormat': 'csv',

        # for converter only
        'description': None,

        # TODO: not supported yet
        'allowEmptyValue': False,
        'explode': None,
        'style': None,
    }

    __internal_fields__ = {
        'final': None,
    }

    def _prim_(self, v, prim_factory, ctx=None):
        logger.write_to_main("enter parameter __prim__")
        i = getattr(self, 'in')
        schema = getattr(self, 'schema')
        return prim_factory.produce(schema, v, ctx) if i == 'body' else prim_factory.produce(self, v, ctx)


class Header(six.with_metaclass(FieldMeta, BaseSchema)):
    """ Header Object
    """

    __swagger_fields__ = {
        'collectionFormat': 'csv',
        'description': None,
        'schema': None,
    }

    def _prim_(self, v, prim_factory, ctx=None):
        return prim_factory.produce(self, v, ctx)


class Response(six.with_metaclass(FieldMeta, BaseObj_v2_0)):
    """ Response Object
    """

    __swagger_fields__ = {
        # Reference Object
        '$ref': None,

        'schema': None,
        'headers': {},
        'type': None,
        'description': None,
        'examples': None,
    }

    __internal_fields__ = {
        'final': None,
    }


class Operation(six.with_metaclass(FieldMeta, BaseObj_v2_0)):
    """ Operation Object
    """

    __swagger_fields__ = {
        'tags': None,
        'operationId': None,
        'consumes': [],
        'produces': [],
        'schemes': [],
        'parameters': None,
        'responses': None,
        'deprecated': False,
        'security': None,
        'description': None,
        'summary': None,
        'externalDocs': None,
        'examples': None,  # spec examples
        'x-ms-examples': None,
        'x-restler-annotations': None,
        'x-ms-long-running-operation': None
    }

    __internal_fields__ = {
        'method': None,
        'url': None,
        'path': None,
        'base_path': None,
        'cached_schemes': [],
    }


class PathItem(six.with_metaclass(FieldMeta, BaseObj_v2_0)):
    """ Path Item Object
    """

    __swagger_fields__ = {
        # Reference Object
        '$ref': None,

        'get': None,
        'put': None,
        'post': None,
        'delete': None,
        'options': None,
        'head': None,
        'patch': None,
        'parameters': [],
    }


class SecurityScheme(six.with_metaclass(FieldMeta, BaseObj_v2_0)):
    """ Security Scheme Object
    """

    __swagger_fields__ = {
        'type': None,
        'name': None,
        'in': None,
        'flow': None,
        'authorizationUrl': None,
        'tokenUrl': None,
        'scopes': None,
        'description': None,
    }


class Tag(six.with_metaclass(FieldMeta, BaseObj_v2_0)):
    """ Tag Object
    """

    __swagger_fields__ = {
        'name': None,
        'description': None,
        'externalDocs': None,
    }


class ExternalDocumentation(six.with_metaclass(FieldMeta, BaseObj_v2_0)):
    """ External Documentation Object
    """

    __swagger_fields__ = {
        'description': None,
        'url': None,
    }
