import unittest
from urllib.parse import quote_plus

from orca_nw_lib.gnmi_pb2 import PathElem, Path
from orca_nw_lib.gnmi_util import get_gnmi_path_decoded


class TestGetGnmiPathDecoded(unittest.TestCase):
    def test_get_gnmi_path_decoded(self):
        ip = '237.84.2.178/24'
        input_path = f'openconfig-interfaces:interfaces/interface[name=Vlan1]/openconfig-if-ethernet:ethernet/ipv4/ipv4-address[address={quote_plus(ip)}]'
        expected_output = Path(target='openconfig')
        expected_output.elem.append(PathElem(name='openconfig-interfaces:interfaces'))
        expected_output.elem.append(PathElem(name='interface', key={'name': 'Vlan1'}))
        expected_output.elem.append(PathElem(name='openconfig-if-ethernet:ethernet'))
        expected_output.elem.append(PathElem(name='ipv4'))
        expected_output.elem.append(PathElem(name='ipv4-address', key={'address': ip}))

        result = get_gnmi_path_decoded(input_path)
        self.assertEqual(result, expected_output)
