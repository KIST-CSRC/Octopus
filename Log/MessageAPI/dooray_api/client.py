"""Dooray API Client Library"""
import requests
import logging
import json
from .exceptions import err_dict, HTTPError

_logger = logging.getLogger(__name__)


class Response(object):
    """API 호출 후 응답을 처리한다."""

    def __init__(self,
                 response):
        """
        :param response: API 요청의 반환 값
        :type response:  requests.Response
        """
        self._status_code = response.status_code
        self._body = response.content
        self._headers = response.headers
        self._url = response.url

    @property
    def status_code(self):
        """
        :return: integer, API 호출의 상태 코드를 반환한다.
        """
        return self._status_code

    @property
    def url(self):
        """
        :return: string, 요청한 API 의 URL 을 반환한다.
        """
        return self._url

    @property
    def body(self):
        """
        :return: binary, API 의 응답 body 를 반환한다.
        """
        return self._body

    @property
    def headers(self):
        """
        :return: dictionary, 응답 헤더를 반환한다.
        """
        return self._headers

    @property
    def to_dict(self):
        """
        :return: dictionary, API 응답 body 를 Dictionary 로 반환한다
        """
        if self.body:
            return json.loads(self.body.decode('utf-8'))
        else:
            return None


class ServiceClient(object):
    """Quickly and easily access any REST or REST-like Dooray API."""

    # Supported HTTP verbs
    methods = {'get', 'post', 'put'}

    def __init__(self,
                 host: str,
                 request_headers: dict,
                 url_path=None,
                 timeout=None):
        self.host = host
        self.request_headers = request_headers or {}
        self._url_path = url_path or []
        self.timeout = timeout

    def _build_url(self,
                   query_params=None):
        """요청에 전달할 최종 URL 를 생성한다.
        :param query_params: 모든 쿼리 스트링을 모아둔 Dictionary
        :type query_params: dictionary
        :return: string
        """
        url = ''
        cnt = 0
        while cnt < len(self._url_path):
            url += f'/{self._url_path[cnt]}'
            cnt += 1

        if query_params:
            url_values = _dict_to_query_string(query_params)
            url = f'{url}?{url_values}'

        url = f'{self.host}{url}'
        _logger.info(f'url={url}')
        return url

    def _update_headers(self,
                        request_headers):
        """request 헤더를 업데이트 한다.
        :param request_headers: API 호출에 대해 설정할 헤더
        :type request_headers: dictionary
        :return: dictionary
        """
        return self.request_headers.update(request_headers)

    def _build_client(self, name=None):
        """새로운 클라이언트 객체를 생성한다.
        :param name: Name of the url segment URL 세그먼트의 네임
                     (e.g. https://wwww.naver.com/1/2/3 인 경우 세그먼트는 1,2,3 으로 구성
        :type name: string
        :return: A ServiceClient object
        """
        url_path = self._url_path + [name] if name else self._url_path
        return ServiceClient(host=self.host,
                             request_headers=self.request_headers,
                             url_path=url_path)

    def _make_request(self, session, request, timeout=None):
        """API 를 호출하고 응답을 반환한다.
        :param session: 요청을 위한 세션
        :type session: requests.Session
        :param request: 실제 요청을 수행할 요청 object
        :type request: requests.PreparedRequest
        :param timeout: timeout 설정
        :type timeout: float
        :return: requests.Response
        """
        timeout = timeout or self.timeout
        return session.send(request, timeout=timeout)

    def _(self, name):
        """URL 세그먼트에 값을 직접 추가하거나 하이픈이 포함된 세그먼트일 경우 사용한다.
           (e.g. /your/url/path/key/_(value) -> /your/url/path/key/value)
           값을 URL 에 추가하고자 할 때 _(추가하고자 하는 값) 을 사용하여 URL 을 생성할 수 있다.
        :param name: URL 세그먼트 명
        :type name: string
        :return: Client object
        """
        return self._build_client(name)

    def __getattr__(self, name):
        """URL 에 메서드 호출을 동적으로 추가하여 HTTP 메서드를 호출한다.
           (e.g. client.name.name.method())
           .v{number}을 사용하여 버전 번호를 추가할 수 있다.
        :param name: URL 세그먼트 또는 메서드 명
        :type name: string
        :return: mixed
        """
        if name in self.methods:
            method = name.upper()

            def http_request(
                    request_body=None,
                    query_params=None,
                    request_headers=None,
                    timeout=None,
                    **_):
                """API 를 호출한다.
                :param timeout: HTTP 요청 시간, requests Client 로 전파
                :param request_headers: HTTP 헤더
                :param query_params: HTTP 쿼리 파라미터
                :param request_body: HTTP 요청 Body
                :return: requests.Response
                """
                
                if request_headers:
                    self._update_headers(request_headers)

                if request_body is None:
                    data = None
                else:
                    if 'Content-Type' in self.request_headers and \
                            self.request_headers['Content-Type'] != \
                            'application/json':
                        data = request_body.encode('utf-8')
                    else:
                        self.request_headers.setdefault(
                            'Content-Type', 'application/json')
                        data = json.dumps(request_body).encode('utf-8')

                session = requests.Session()
                request = requests.Request(
                    method=method,
                    url=self._build_url(query_params),
                    headers=self.request_headers,
                    data=data
                )
                # print(self.request_headers)
                # print(self._build_url(query_params))
                # print(data)

                _logger.debug('{method} Request: {url}'.format(
                    method=method,
                    url=request.url))
                if request.data:
                    _logger.debug('PAYLOAD: {data}'.format(
                        data=data))
                _logger.debug('HEADERS: {headers}'.format(
                    headers=request.headers))

                prepared_request = request.prepare()
                response = Response(
                    self._make_request(session, prepared_request, timeout)
                )

                if response.status_code in err_dict.keys():
                    raise HTTPError(err_dict[response.status_code], response.status_code)

                _logger.debug('{method} Response: {status} {body}'.format(
                    method=prepared_request.method,
                    status=response.status_code,
                    body=response.body))

                return response

            return http_request
        else:
            # Add a segment to the URL
            if '_' in name:
                name = name.replace('_', '-')
            return self._(name)


def _dict_to_query_string(d):
    query = ''
    for key in d.keys():
        query += str(key) + '=' + str(d[key]) + "&"
    return query[:-1]