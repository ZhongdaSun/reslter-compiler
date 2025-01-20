# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import os
from compiler.utilities import JsonSerialization
from compiler.grammar import (
    get_operation_method_from_string,
    ProducerConsumerAnnotation,
    RequestId,
    AnnotationResourceReference)
from compiler.access_paths import (
    try_get_access_path_from_string,
    EmptyAccessPath)
from compiler.xms_paths import get_x_ms_path
from compiler.config import ConfigSetting
from restler.utils import restler_logger as logger


GlobalAnnotationKey = "x-restler-global-annotations"


# omitted ProducerConsumerUserAnnotation because it is only used to
# figure out the annotation refer to grammar.ProducerConsumerAnnotation
def get_except_property(o, except_consumer):
    """
    从注解的 except 子句中获取消费者的 endpoint 和 method 属性

    @param o: 包含 except 子句的字典
    @param except_consumer: 当前的 except 子句

    @return: consumer_endpoint 和 consumer_method
    @rtype: tuple
    """
    keys = o.keys()
    if "consumer_endpoint" in keys:
        consumer_endpoint = o.get("consumer_endpoint")
    else:
        raise ValueError(f"注解中的 except 子句无效: {except_consumer}")

    if "consumer_method" in keys:
        consumer_method = o.get("consumer_method")
    else:
        raise ValueError(f"注解中的 except 子句无效: {except_consumer}")

    return consumer_endpoint, consumer_method


"""
"x-restler-annotations": [
          {
            "producer_endpoint": "/stores",
            "producer_method": "POST",
            "producer_resource_name": "metadata",
            "consumer_param": "/storeProperties/tags"
          },
          {
            "producer_endpoint": "/stores",
            "producer_method": "POST",
            "producer_resource_name": "/delivery/metadata/",
            "consumer_param": "/items/[0]/deliveryTags",
          }
        ]
"""


# parseAnnotation
def parse_annotation(annotation: dict):
    """
    解析单个注解字典，创建 ProducerConsumerAnnotation 对象

    @param annotation: 包含注解的字典
    @type  annotation： dict

    @return: 解析后的 ProducerConsumerAnnotation 对象
    @rtype: ProducerConsumerAnnotation
    """
    keys = annotation.keys()
    consumer_request_id = None

    # 处理生产者相关属性
    if "producer_endpoint" in keys:
        producer_endpoint = annotation.get("producer_endpoint")
        xms_path = get_x_ms_path(producer_endpoint)
        if xms_path is not None:
            producer_endpoint = xms_path.get_normalized_endpoint()

        if "producer_method" in keys:
            method = get_operation_method_from_string(annotation.get("producer_method"))
            producer_request_id = RequestId(endpoint=producer_endpoint,
                                            method=method,
                                            xms_path=None,
                                            has_example=False)
        else:
            raise ValueError("无效注解: 如果指定了 producer_endpoint，必须指定 producer_method")

    else:
        raise ValueError("无效注解: 必须指定 producer_endpoint")

    consumer_endpoint = None

    if "consumer_endpoint" in keys:
        consumer_endpoint = annotation.get("consumer_endpoint")
        xms_path = get_x_ms_path(consumer_endpoint)
        if xms_path is not None:
            consumer_endpoint = xms_path.get_normalized_endpoint()

    if "consumer_method" in keys:
        if "consumer_endpoint" in keys:
            method = get_operation_method_from_string(annotation.get("consumer_method"))
            consumer_request_id = RequestId(endpoint=consumer_endpoint,
                                            method=method,
                                            xms_path=None,
                                            has_example=False)
        else:
            raise ValueError("无效注解: 如果指定了 consumer_endpoint，必须指定 consumer_method")

    consumer_parameter = None
    if "consumer_param" in keys:
        str_consumer_param = annotation.get("consumer_param")
        access_path = try_get_access_path_from_string(str_consumer_param)
        if access_path is not None:
            consumer_parameter = AnnotationResourceReference(resource_name="", resource_path=access_path)
        else:
            consumer_parameter = AnnotationResourceReference(resource_name=str_consumer_param,
                                                             resource_path=EmptyAccessPath)

    producer_parameter = None
    if "producer_resource_name" in keys:
        str_producer_parameter = annotation.get("producer_resource_name")
        access_path = try_get_access_path_from_string(str_producer_parameter)
        if access_path is not None:
            producer_parameter = AnnotationResourceReference(resource_name=None,
                                                             resource_path=access_path)
        else:
            producer_parameter = AnnotationResourceReference(resource_name=str_producer_parameter,
                                                             resource_path=EmptyAccessPath)

    except_consumer_id = None
    if "except" in keys:
        list_except = annotation.get("except")
        except_consumer = []
        for ec in list_except:
            if isinstance(ec, list):
                for x in ec:
                    o = x["value"]
                    except_consumer.append(get_except_property(o, ec))
            elif isinstance(ec, dict):
                except_consumer.append(get_except_property(ec, ec))
            else:
                raise ValueError(f"无效的 except 子句: {ec}")

        except_consumer_id = []
        for except_endpoint, except_method in except_consumer:
            x_ms_path = get_x_ms_path(except_endpoint)
            endpoint = except_endpoint
            if x_ms_path is not None:
                endpoint = x_ms_path.get_normalized_endpoint()
            except_consumer_id.append(RequestId(endpoint=endpoint,
                                                method=get_operation_method_from_string(except_method),
                                                xms_path=x_ms_path, has_example=False))

    return ProducerConsumerAnnotation(producer_id=producer_request_id,
                                      consumer_id=consumer_request_id,
                                      producer_parameter=producer_parameter,
                                      consumer_parameter=consumer_parameter,
                                      except_consumer_id=except_consumer_id)


# Gets annotation data from Json
# This applies if the user specifies a separate file with annotations only
# Gets the RESTler dependency annotation from the extension data
# The 'except' clause indicates that all consumer IDs with resource name 'workflowName'
# should be resolved to this producer, except for the indicated consumer endpoint (which
# should use the dependency in order of resolution, e.g. custom dictionary entry.)
# {
#        "producer_resource_name": "name",
#        "producer_method": "PUT",
#        "consumer_param": "workflowName",
#        "producer_endpoint": "/subscriptions/{subscriptionId}/providers/Microsoft.Logic/workflows/{workflowName}",
#        "except": {
#            "consumer_endpoint": "/subscriptions/{subscriptionId}/providers/Microsoft.Logic/workflows/{workflowName}",
#            "consumer_method": "PUT"
#        }
#    },
def get_annotations_from_json(annotation_json: list[dict]) -> list[ProducerConsumerAnnotation]:
    """
    从 JSON 数据中解析注解列表

    @param annotation_json: JSON 形式的注解数据
    @type  annotation_json： list[dict]

    @return: 解析后的注解列表
    @rtype: list[ProducerConsumerAnnotation]
    """
    if annotation_json is None or len(annotation_json) == 0:
        return []
    try:
        annotations = []
        for ann in annotation_json:
            logger.write_to_main(f"ann={ann}", ConfigSetting().LogConfig.annotations)
            parsed_ann = parse_annotation(ann)
            if parsed_ann:
                annotations.append(parsed_ann)
        return annotations
    except Exception as e:
        print(f"Error: Annotation format is incorrect {str(e)}")
        raise e


# Gets the RESTler dependency annotation from OpenAPI v3 links
#    "links": {
#      "linkName":{
#        "description": "description",
#        "operationId": "target operation",
#        "parameters": {
#          "configStoreName": "JSON path to value"
#        }
#      }
#      }
# getAnnotationsFromOpenapiLinks
def get_global_annotations_from_file(file_path):
    """
    Load global annotations from a specified file

    @param file_path: file path
    @type  file_path： str

    @return: Parsed Global Annotation List
    @rtype: list[ProducerConsumerAnnotation]
    """
    if os.path.exists(file_path):
        global_annotations_json = JsonSerialization.try_deeserialize_from_file(file_path)
        logger.write_to_main(f"global_annotations_json={global_annotations_json}",
                             ConfigSetting().LogConfig.annotations)
        global_ann = global_annotations_json.get(GlobalAnnotationKey)
        logger.write_to_main(f"global_ann={global_ann}", ConfigSetting().LogConfig.annotations)
        if global_ann:
            return global_ann
        else:
            print("Error: Invalid annotation file: It must include the key 'x-compiler-global-annotations'")
            raise ValueError("Invalid annotation file")
    else:
        return []


def parse_producer_parameter(param_value):
    """
    从 JSON 参数值中解析生产者参数

    @param param_value: 参数值字符串
    @type  param_value： str

    @return: AnnotationResourceReference对象或 None
    @rtype: AnnotationResourceReference
    """
    if isinstance(param_value, str):
        if param_value.startswith("$request.") or param_value.startswith("$response.") or param_value.startswith(
                "body#"):

            parts = param_value.split(".")
            if len(parts) == 3:
                p = try_get_access_path_from_string(parts[2])
                return AnnotationResourceReference(resource_name="", resource_path=p) if p else (
                    AnnotationResourceReference(resource_name=parts[2], resource_path=EmptyAccessPath))
    return None


# todo Remove this source code because these functionalities are only supported in openapi3

"""
# parseLink
def parse_link(link, oas_doc, producer_request_id):
    # Parse the link and create ProducerConsumerAnnotation
    consumer_operation = next((op for op in oas_doc.Operations if op.Operation.OperationId == link.OperationId), None)
    if consumer_operation:
        consumer_endpoint = consumer_operation.Path
        consumer_method = get_operation_method_from_string(consumer_operation.Method)
        consumer_request_id = RequestId(endpoint=consumer_endpoint,
                                        method=get_operation_method_from_string(consumer_method),
                                        xms_path=None)

        kv = next(iter(link.Parameters.items()), None)
        if kv:
            # todo
            consumer_parameter = re.sub("^(path|query|header|cookie)", "", kv[0])
            p = try_get_access_path_from_string(consumer_parameter)
            consumer_parameter = AnnotationResourceReference(resource_name="", resource_path=p) if p else (
                AnnotationResourceReference(resource_name=consumer_parameter, resource_path=EmptyAccessPath))

            producer_parameter = parse_producer_parameter(kv[1])
            if producer_parameter:
                return ProducerConsumerAnnotation(producer_id=producer_request_id,
                                                  consumer_id=consumer_request_id,
                                                  producer_parameter=consumer_parameter,
                                                  consumer_parameter=producer_parameter,
                                                  except_consumer_id=None)

    return None


# Gets the RESTler dependency annotation from OpenAPI v3 links
#    "links": {
#      "linkName":{
#        "description": "description",
#        "operationId": "target operation",
#        "parameters": {
#          "configStoreName": "JSON path to value"
#        }
#      }
#    }
#
def get_annotations_from_openapi_links(producer_request_id, links, oas_doc):
    if not links:
        return []
               
    annotations = []
    for k, v in links.items():
        result = parse_link(v.ActualLink, oas_doc, producer_request_id)
        if result:
            annotations.append(result)
    return annotations
"""
