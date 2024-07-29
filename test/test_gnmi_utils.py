import unittest
from urllib.parse import quote_plus

from orca_nw_lib.gnmi_pb2 import PathElem, Path
from orca_nw_lib.gnmi_util import get_gnmi_path


class TestGetGnmiPathDecoded(unittest.TestCase):
    def test_get_gnmi_path_decoded(self):
        ip = "237.84.2.178/24"
        input_path = f"openconfig-interfaces:interfaces/interface[name=Vlan1]/openconfig-if-ethernet:ethernet/ipv4/ipv4-address[address={quote_plus(ip)}]"
        expected_output = Path(target="openconfig")
        expected_output.elem.append(PathElem(name="openconfig-interfaces:interfaces"))
        expected_output.elem.append(PathElem(name="interface", key={"name": "Vlan1"}))
        expected_output.elem.append(PathElem(name="openconfig-if-ethernet:ethernet"))
        expected_output.elem.append(PathElem(name="ipv4"))
        expected_output.elem.append(PathElem(name="ipv4-address", key={"address": ip}))

        result = get_gnmi_path(input_path)
        self.assertEqual(result, expected_output)

    def test_get_gnmi_path_simple(self):
        path = "openconfig-interfaces:interfaces/interface[name=Vlan1]/openconfig-if-ethernet:ethernet"
        expected_path = Path(
            target="openconfig",
            elem=[
                PathElem(name="openconfig-interfaces:interfaces"),
                PathElem(name="interface", key={"name": "Vlan1"}),
                PathElem(name="openconfig-if-ethernet:ethernet"),
            ],
        )
        self.assertEqual(get_gnmi_path(path), expected_path)

    def test_get_gnmi_path_with_encoded_value(self):
        path = "openconfig-interfaces:interfaces/interface[name=Vlan1]/openconfig-if-ethernet:ethernet/ipv4/ipv4-address[address=237.84.2.178%2f24]"
        expected_path = Path(
            target="openconfig",
            elem=[
                PathElem(name="openconfig-interfaces:interfaces"),
                PathElem(name="interface", key={"name": "Vlan1"}),
                PathElem(name="openconfig-if-ethernet:ethernet"),
                PathElem(name="ipv4"),
                PathElem(name="ipv4-address", key={"address": "237.84.2.178/24"}),
            ],
        )
        self.assertEqual(get_gnmi_path(path), expected_path)

    def test_get_gnmi_path_with_multiple_keys(self):
        path = "openconfig-interfaces:interfaces/interface[name=Vlan1]/openconfig-if-ethernet:ethernet/ipv4/ipv4-address[address=237.84.2.178%2f24,prefix-length=24]"
        expected_path = Path(
            target="openconfig",
            elem=[
                PathElem(name="openconfig-interfaces:interfaces"),
                PathElem(name="interface", key={"name": "Vlan1"}),
                PathElem(name="openconfig-if-ethernet:ethernet"),
                PathElem(name="ipv4"),
                PathElem(
                    name="ipv4-address",
                    key={"address": "237.84.2.178/24", "prefix-length": "24"},
                ),
            ],
        )
        self.assertEqual(get_gnmi_path(path), expected_path)

    def test_get_gnmi_path_with_empty_path(self):
        path = ""
        expected_path = Path(target="openconfig", elem=[])
        self.assertEqual(get_gnmi_path(path), expected_path)

    def test_get_gnmi_path_with_invalid_path(self):
        path = "openconfig-interfaces:interfaces/interface[name=Vlan1]/openconfig-if-ethernet:ethernet/ipv4/ipv4-address[address=237.84.2.178%2f24,prefix-length=24"
        with self.assertRaises(ValueError):
            get_gnmi_path(path)
