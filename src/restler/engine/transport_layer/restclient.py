import json

import requests
import json as complexjson
from restler.utils import restler_logger as logger

IS_CLOSED_LOG = False
class RestClient:

    def __init__(self, api_root_url):
        self.api_root_url = api_root_url
        self.session = requests.session()

    def get(self, url, **kwargs):
        return self.request(url, "GET", **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return self.request(url, "POST", data, json, **kwargs)

    def put(self, url, data=None, **kwargs):
        return self.request(url, "PUT", data, **kwargs)

    def delete(self, url, **kwargs):
        return self.request(url, "DELETE", **kwargs)

    def patch(self, url, data=None, **kwargs):
        return self.request(url, "PATCH", data, **kwargs)

    def rest_client_method(self, render_data):
        from restler.engine.transport_layer.response import HttpResponse
        DELIM = "\r\n\r\n"

        def _get_end_of_header(message):
            return message.index(DELIM)

        def _get_url_path(message):
            start_url_index = message.find(" ")
            header = message.find(" HTTP/1.1\r\n")
            return message[start_url_index + 2:header]

        def _get_method_from_message(message):
            end_of_method_idx = message.find(" ")
            method_name = message[0:end_of_method_idx]
            return method_name

        def _get_start_of_body(message):
            return _get_end_of_header(message) + len(DELIM)

        def _get_body_message(message):
            start = _get_start_of_body(message)
            return message[start: len(message)]

        def _get_header(message):
            header = message.find(" HTTP/1.1\r\n")
            return message[header + len(" HTTP/1.1\r\n"):_get_end_of_header(message)]

        method = _get_method_from_message(message=render_data)
        body = _get_body_message(message=render_data)
        url = _get_url_path(message=render_data)
        header = {"Host": "http://192.168.1.21:17103/",
                  "Content-Type": "application/json"}
        self.api_root_url = "http://192.168.1.21:17103/"
        # header_dict = json.loads(header)
        logger.write_to_main(f"render_data={render_data}", False)
        logger.write_to_main(f"method ={method} body={body} url={url}, header={header}", False)
        response = self.request(url=url, method=method)
        status_code = response.status_code
        try:
            response_body = response.ok
            response_body = response.text
        except ValueError:
            response_body = response.text
        response = HttpResponse(str(status_code) + "$" + response_body)

        return True, response

    def request(self, url, method, data=None, json=None, **kwargs):
        url = self.api_root_url + url
        headers = dict(**kwargs).get("headers")
        params = dict(**kwargs).get("params")
        files = dict(**kwargs).get("files")
        cookies = dict(**kwargs).get("cookies")
        self.request_log(url, method, data, json, params, headers, files, cookies)
        if method == "GET":
            return self.session.get(url, **kwargs)
        if method == "POST":
            return requests.post(url, data, json, **kwargs)
        if method == "PUT":
            if json:
                # PUT 和 PATCH 中没有提供直接使用json参数的方法，因此需要用data来传入
                data = complexjson.dumps(json)
            return self.session.put(url, data, **kwargs)
        if method == "DELETE":
            return self.session.delete(url, **kwargs)
        if method == "PATCH":
            if json:
                data = complexjson.dumps(json)
            return self.session.patch(url, data, **kwargs)

    def request_log(self, url, method, data=None, json=None, params=None, headers=None, files=None, cookies=None,
                    **kwargs):
        logger.write_to_main("接口请求地址 ==>> {}".format(url), False)
        logger.write_to_main("接口请求方式 ==>> {}".format(method), IS_CLOSED_LOG)
        # Python3中，json在做dumps操作时，会将中文转换成unicode编码，因此设置 ensure_ascii=False
        logger.write_to_main("接口请求头 ==>> {}".format(complexjson.dumps(headers, indent=4, ensure_ascii=False)),
                             IS_CLOSED_LOG)
        logger.write_to_main("接口请求 params 参数 ==>> {}".format(complexjson.dumps(params, indent=4, ensure_ascii=False)),
                             IS_CLOSED_LOG)
        logger.write_to_main("接口请求体 data 参数 ==>> {}".format(complexjson.dumps(data, indent=4, ensure_ascii=False)),
                             IS_CLOSED_LOG)
        logger.write_to_main("接口请求体 json 参数 ==>> {}".format(complexjson.dumps(json, indent=4, ensure_ascii=False)),
                             IS_CLOSED_LOG)
        logger.write_to_main("接口上传附件 files 参数 ==>> {}".format(files), IS_CLOSED_LOG)
        logger.write_to_main("接口 cookies 参数 ==>> {}".format(complexjson.dumps(cookies, indent=4, ensure_ascii=False)
                                                                ), IS_CLOSED_LOG)
