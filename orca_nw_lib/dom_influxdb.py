import datetime
from orca_nw_lib.influxdb_utils import create_point, write_to_influx
from .gnmi_pb2 import SubscribeResponse
from .gnmi_util import get_logging


_logger = get_logging().getLogger(__name__)


def handle_dom_influxdb(device_ip: str, resp: SubscribeResponse):
    """
    Sends the subscription system metrics received from a device to the InfluxDB.
    
    Args:
        device_ip (str): The IP address of the device
        resp (SubscribeResponse): The subscription response containing metrics

    Returns: 
        None
    """

    intfc = ""
    threshold = ""
    point = create_point("dom_info")
    device_pnt = point.tag("device_ip", device_ip)
    for ele in resp.update.prefix.elem:
        if ele.name == "component":
            if ele.key.get('name').startswith('Ethernet'):
                intfc = ele.key.get('name')
                intfc_pnt = device_pnt.tag("interface", intfc)
                break

    if not intfc:
        _logger.debug("DOM Info not found in gNMI subscription response from %s",device_ip,)
        return
    
    if intfc:
        for u in resp.update.update:
            for ele in u.path.elem:
                if ele.name == "cable-length":
                    intfc_pnt.field("cable_length", float(u.val.float_val))
                elif ele.name == "connector-type":
                    intfc_pnt.field("connector_type", u.val.string_val)
                elif ele.name == "date-code":
                    intfc_pnt.field("date_code", u.val.string_val)
                elif ele.name == "display-name":
                    intfc_pnt.field("display_name", u.val.string_val)
                elif ele.name == "form-factor":
                    intfc_pnt.field("form_factor", u.val.string_val)
                elif ele.name == "input-power": # and ele.name == "instant":
                    intfc_pnt.field("input_power", float(u.val.float_val))
                elif ele.name == "is-high-power-media":
                    intfc_pnt.field("is_high_power_media", str(u.val.bool_val))
                elif ele.name == "laser-bias-current": # and ele.name == "instant":
                    intfc_pnt.field("laser_bias_current", float(u.val.float_val))
                elif ele.name == "laser-capabilities": # and ele.name == "transmitter-is-tunable":
                    intfc_pnt.field("laser_capabilities", str(u.val.bool_val))
                elif ele.name == "max-module-power":
                    intfc_pnt.field("max_module_power", float(u.val.float_val))
                elif ele.name == "max-port-power":
                    intfc_pnt.field("max_port_power", float(u.val.float_val))
                elif ele.name == "media-lane-count":
                    intfc_pnt.field("media_lane_count", float(u.val.float_val))
                elif ele.name == "media-lockdown-state":
                    intfc_pnt.field("media_lockdown_state", str(u.val.bool_val))
                elif ele.name == "output-power": # and ele.name == "instant":
                    intfc_pnt.field("output_power", float(u.val.float_val))
                elif ele.name == "present":
                    intfc_pnt.field("present", u.val.string_val)
                elif ele.name == "qualified":
                    intfc_pnt.field("qualified", str(u.val.bool_val))
                elif ele.name == "serial-no":
                    intfc_pnt.field("serial_no", u.val.string_val)
                elif ele.name == "supply-voltage": # and ele.name == "instant":
                    intfc_pnt.field("supply_voltage", float(u.val.float_val))
                elif ele.name == "vendor":
                    intfc_pnt.field("vendor", u.val.string_val)
                elif ele.name == "vendor-oui":
                    intfc_pnt.field("vendor_oui", u.val.string_val)
                elif ele.name == "vendor-part":
                    intfc_pnt.field("vendor_part", u.val.string_val)
                elif ele.name == "vendor-rev":
                    intfc_pnt.field("vendor_rev", u.val.string_val)
                # Temperature
                elif ele.name == "temperature": # and ele.name == "instant":
                    intfc_pnt.field("temperature", float(u.val.float_val))


                # Thereshold
                if (ele.name == "threshold"):
                    if ele.key.get('severity') == "CRITICAL":
                        threshold = "CRITICAL"
                    elif ele.key.get('severity') == "WARNING":
                        threshold = "WARNING"

                if threshold == "CRITICAL":
                    if ele.name == "input-power-lower":
                        intfc_pnt.field("threshold_critical_input_power_lower", float(u.val.float_val))
                    elif ele.name == "input-power-upper":
                        intfc_pnt.field("threshold_critical_input_power_upper", float(u.val.float_val))
                    elif ele.name == "laser-bias-current-lower":
                        intfc_pnt.field("threshold_critical_laser_bias_current_lower", float(u.val.float_val))
                    elif ele.name == "laser-bias-current-upper":
                        intfc_pnt.field("threshold_critical_laser_bias_current_upper", float(u.val.float_val))
                    elif ele.name == "module-temperature-lower":
                        intfc_pnt.field("threshold_critical_module_temperature_lower", float(u.val.float_val))
                    elif ele.name == "module-temperature-upper":
                        intfc_pnt.field("threshold_critical_module_temperature_upper", float(u.val.float_val))
                    elif ele.name == "output-power-lower":
                        intfc_pnt.field("threshold_critical_output_power_lower", float(u.val.float_val))
                    elif ele.name == "output-power-upper":
                        intfc_pnt.field("threshold_critical_output_power_upper", float(u.val.float_val))
                    elif ele.name == "supply-voltage-lower":
                        intfc_pnt.field("threshold_critical_supply_voltage_lower", float(u.val.float_val))
                    elif ele.name == "supply-voltage-upper":
                        intfc_pnt.field("threshold_critical_supply_voltage_upper", float(u.val.float_val))

                elif threshold == "WARNING":
                    if ele.name == "input-power-lower":
                        intfc_pnt.field("threshold_warning_input_power_lower", float(u.val.float_val))
                    elif ele.name == "input-power-upper":
                        intfc_pnt.field("threshold_warning_input_power_upper", float(u.val.float_val))
                    elif ele.name == "laser-bias-current-lower":
                        intfc_pnt.field("threshold_warning_laser_bias_current_lower", float(u.val.float_val))
                    elif ele.name == "laser-bias-current-upper":
                        intfc_pnt.field("threshold_warning_laser_bias_current_upper", float(u.val.float_val))
                    elif ele.name == "module-temperature-lower":
                        intfc_pnt.field("threshold_warning_module_temperature_lower", float(u.val.float_val))
                    elif ele.name == "module-temperature-upper":
                        intfc_pnt.field("threshold_warning_module_temperature_upper", float(u.val.float_val))
                    elif ele.name == "output-power-lower":
                        intfc_pnt.field("threshold_warning_output_power_lower", float(u.val.float_val))
                    elif ele.name == "output-power-upper":
                        intfc_pnt.field("threshold_warning_output_power_upper", float(u.val.float_val))
                    elif ele.name == "supply-voltage-lower":
                        intfc_pnt.field("threshold_warning_supply_voltage_lower", float(u.val.float_val))
                    elif ele.name == "supply-voltage-upper":
                        intfc_pnt.field("threshold_warning_supply_voltage_upper", float(u.val.float_val))

    point.time(datetime.datetime.now(datetime.timezone.utc))
    write_to_influx(point=point)
    _logger.debug("gNMI subscription dom info to influxdb for %s ",device_ip)