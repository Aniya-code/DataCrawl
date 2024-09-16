from mitmproxy import http
from mitmproxy.tools.main import mitmdump
import sys


def response(flow: http.HTTPFlow) -> None:
    # if 'videoplayback' in flow.request.pretty_url:
    response_body_size = len(flow.response.content)
    with open('log.csv', 'a') as f:
        f.write(str(response_body_size) + '\n')
    print(f"#################### Response body size: {response_body_size} bytes ####################")


if __name__ == '__main__':
    sys.argv = [
        __file__,  # 必须包含
        "-s", __file__,  # 加载脚本文件
        "--mode", "upstream:http://127.0.0.1:7890",
       ]

    mitmdump()