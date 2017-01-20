from volttrontesting.utils.platformwrapper import PlatformWrapper, \
    start_wrapper_platform
import gevent
from apiutils import *

def vc_vcp_platforms(use_http=True):
    vc = PlatformWrapper()
    vcp = PlatformWrapper()

    # VC is setup to allow all connections
    vc.allow_all_connections()
    start_wrapper_platform(vc, with_http=True)

    if use_http == True:
        start_wrapper_platform(vcp,
                               volttron_central_address=vc.bind_web_address)
    else:
        start_wrapper_platform(vcp, volttron_central_address=vc.vip_address,
                               volttron_central_serverkey=vc.serverkey)
    return vc, vcp

def test_autoregister_external():
    #gevent.sleep(15)
    vc, vcp = vc_vcp_platforms()

    api = APITester(vc.jsonrpc_endpoint)

    platforms = api.get_result(api.list_platforms)
    assert len(platforms) == 1
    p = platforms[0]
    assert p['uuid']
    assert p['name'] == vcp.vip_address
    assert vcp.vip_address != vc.vip_address
    assert isinstance(p['health'], dict)
    vc.shutdown_platform()
    vcp.shutdown_platform()


if __name__ == '__main__':
    try:
        test_autoregister_external()
    except KeyboardInterrupt:
        pass