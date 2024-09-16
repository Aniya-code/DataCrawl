from mitmproxy import http
from mitmproxy.tools.main import mitmdump
from os import path


class MITM_HTTP:
    def __init__(self):
        self.is_first = True
        protocal = "tls"
        # protocal = "quic"
        body_log_fullname = f"data/{protocal}_body_log.csv"
        self.f = open(body_log_fullname, 'a', encoding="utf8")

    def response(self, flow: http.HTTPFlow) -> None:
        if 'videoplayback' in flow.request.pretty_url:
            response_body_size = len(flow.response.content)
            if response_body_size > 0:
                if self.is_first:
                    self.f.write(str(response_body_size))
                    self.is_first = False
                else:
                    self.f.write(f'/{response_body_size}')
                self.f.flush()
            print(f"~~~~~~~~[MITM]videoplayback size: {response_body_size}~~~~~~~~")

body_plugin = MITM_HTTP()
addons = [body_plugin]

if __name__ == '__main__':
    try:
        mitmdump([
            "-s", __file__, 
            # "--mode", "upstream:http://127.0.0.1:7890", # 直连时注释掉改行
            # "--mode", "upstream:http://10.26.22.212:7890",
            
        ])
    finally:
        body_plugin.f.close()