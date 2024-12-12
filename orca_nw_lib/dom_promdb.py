
from prometheus_client import CollectorRegistry, Gauge, Info

from orca_nw_lib.promdb_utils import write_to_prometheus
from .gnmi_pb2 import SubscribeResponse
from .gnmi_util import get_logging

_logger = get_logging().getLogger(__name__)

dom_registry = CollectorRegistry()
dom_tranceiver_info = Info('dom_tranceiver_info', 'DOM tranceiver info from subscription', labelnames=["device_ip", "interface"], registry=dom_registry)
dom_threshold_info = Info('dom_threshold_info', 'DOM threshold info from subscription', labelnames=["device_ip", "interface"], registry=dom_registry)

dom_time_registry = CollectorRegistry()
input_power_info = Gauge('dom_input_power', 'DOM Input power', labelnames=["device_ip", "interface"], registry=dom_time_registry)
output_power_info = Gauge('dom_output_power', 'DOM output power', labelnames=["device_ip", "interface"], registry=dom_time_registry)
laser_bias_current_info = Gauge('dom_laser_bias_current', 'DOM bias amp', labelnames=["device_ip", "interface"], registry=dom_time_registry)
temperature_info = Gauge('dom_temperature', 'DOM temperature', labelnames=["device_ip", "interface"], registry=dom_time_registry)
supply_voltage_info = Gauge('dom_supply_voltage', 'DOM suppy volts', labelnames=["device_ip", "interface"], registry=dom_time_registry)

def handle_dom_promdb(device_ip: str, resp: SubscribeResponse):
    """
    Sends the subscription system metrics received from a device to the Prometheus.
    
    Args:
        device_ip (str): The IP address of the device
        resp (SubscribeResponse): The subscription response containing metrics

    Returns: 
        None
    """
    dom_trans_dict = {}
    dom_thresh_dict = {}
    intfc = ""
    threshold = ""

    for ele in resp.update.prefix.elem:
        if ele.name == "component":
            if ele.key.get('name').startswith('Ethernet'):
                intfc = ele.key.get('name')
                break

    if not intfc:
        _logger.debug("DOM Info not found in gNMI subscription response from %s",device_ip,)
        return

    if intfc:
        for u in resp.update.update:
            for ele in u.path.elem:
                if ele.name == "cable-length":
                    dom_trans_dict["cable_length"] = str(u.val.float_val)
                elif ele.name == "connector-type":
                    dom_trans_dict["connector_type"]= str(u.val.string_val)
                elif ele.name == "date-code":
                    dom_trans_dict["date_code"]= str(u.val.string_val)
                elif ele.name == "display-name":
                    dom_trans_dict["display_name"]= str(u.val.string_val)
                elif ele.name == "form-factor":
                    dom_trans_dict["form_factor"]= str(u.val.string_val)
                elif ele.name == "is-high-power-media":
                    dom_trans_dict["is_high_power_media"]= str(u.val.bool_val)
                elif ele.name == "laser-capabilities":
                    dom_trans_dict["laser_capabilities"]= str(u.val.bool_val)
                elif ele.name == "max-module-power":
                    dom_trans_dict["max_module_power"]= str(u.val.float_val)
                elif ele.name == "max-port-power":
                    dom_trans_dict["max_port_power"]= str(u.val.float_val)
                elif ele.name == "media-lane-count":
                    dom_trans_dict["media_lane_count"]= str(u.val.float_val)
                elif ele.name == "media-lockdown-state":
                    dom_trans_dict["media_lockdown_state"]= str(u.val.bool_val)
                elif ele.name == "present":
                    dom_trans_dict["present"]= u.val.string_val
                elif ele.name == "qualified":
                    dom_trans_dict["qualified"]= str(u.val.bool_val)
                elif ele.name == "serial-no":
                    dom_trans_dict["serial_no"]= u.val.string_val
                elif ele.name == "vendor":
                    dom_trans_dict["vendor"]= u.val.string_val
                elif ele.name == "vendor-oui":
                    dom_trans_dict["vendor_oui"]= u.val.string_val
                elif ele.name == "vendor-part":
                    dom_trans_dict["vendor_part"]= u.val.string_val
                elif ele.name == "vendor-rev":
                    dom_trans_dict["vendor_rev"]= u.val.string_val
                
                # Time Series
                if ele.name == "input-power":
                    input_power_info.labels(device_ip=device_ip, interface=intfc).set(float(u.val.float_val))
                if ele.name == "laser-bias-current":
                    laser_bias_current_info.labels(device_ip=device_ip, interface=intfc).set(float(u.val.float_val))
                if ele.name == "output-power":
                    output_power_info.labels(device_ip=device_ip, interface=intfc).set(float(u.val.float_val))
                if ele.name == "supply-voltage":
                    supply_voltage_info.labels(device_ip=device_ip, interface=intfc).set(float(u.val.float_val))
                if ele.name == "temperature":
                    temperature_info.labels(device_ip=device_ip, interface=intfc).set(float(u.val.float_val))

                
                # Thereshold
                if (ele.name == "threshold"):
                    if ele.key.get('severity') == "CRITICAL":
                        threshold = "CRITICAL"
                    elif ele.key.get('severity') == "WARNING":
                        threshold = "WARNING"

                if threshold == "CRITICAL":
                    if ele.name == "input-power-lower":
                        dom_thresh_dict["threshold_critical_input_power_lower"]= str(u.val.float_val)
                    elif ele.name == "input-power-upper":
                        dom_thresh_dict["threshold_critical_input_power_upper"]= str(u.val.float_val)
                    elif ele.name == "laser-bias-current-lower":
                        dom_thresh_dict["threshold_critical_laser_bias_current_lower"]= str(u.val.float_val)
                    elif ele.name == "laser-bias-current-upper":
                        dom_thresh_dict["threshold_critical_laser_bias_current_upper"]= str(u.val.float_val)
                    elif ele.name == "module-temperature-lower":
                        dom_thresh_dict["threshold_critical_module_temperature_lower"]= str(u.val.float_val)
                    elif ele.name == "module-temperature-upper":
                        dom_thresh_dict["threshold_critical_module_temperature_upper"]= str(u.val.float_val)
                    elif ele.name == "output-power-lower":
                        dom_thresh_dict["threshold_critical_output_power_lower"]= str(u.val.float_val)
                    elif ele.name == "output-power-upper":
                        dom_thresh_dict["threshold_critical_output_power_upper"]= str(u.val.float_val)
                    elif ele.name == "supply-voltage-lower":
                        dom_thresh_dict["threshold_critical_supply_voltage_lower"]= str(u.val.float_val)
                    elif ele.name == "supply-voltage-upper":
                        dom_thresh_dict["threshold_critical_supply_voltage_upper"]= str(u.val.float_val)

                elif threshold == "WARNING":
                    if ele.name == "input-power-lower":
                        dom_thresh_dict["threshold_warning_input_power_lower"]= str(u.val.float_val)
                    elif ele.name == "input-power-upper":
                        dom_thresh_dict["threshold_warning_input_power_upper"]= str(u.val.float_val)
                    elif ele.name == "laser-bias-current-lower":
                        dom_thresh_dict["threshold_warning_laser_bias_current_lower"]= str(u.val.float_val)
                    elif ele.name == "laser-bias-current-upper":
                        dom_thresh_dict["threshold_warning_laser_bias_current_upper"]= str(u.val.float_val)
                    elif ele.name == "module-temperature-lower":
                        dom_thresh_dict["threshold_warning_module_temperature_lower"]= str(u.val.float_val)
                    elif ele.name == "module-temperature-upper":
                        dom_thresh_dict["threshold_warning_module_temperature_upper"]= str(u.val.float_val)
                    elif ele.name == "output-power-lower":
                        dom_thresh_dict["threshold_warning_output_power_lower"]= str(u.val.float_val)
                    elif ele.name == "output-power-upper":
                        dom_thresh_dict["threshold_warning_output_power_upper"]= str(u.val.float_val)
                    elif ele.name == "supply-voltage-lower":
                        dom_thresh_dict["threshold_warning_supply_voltage_lower"]= str(u.val.float_val)
                    elif ele.name == "supply-voltage-upper":
                        dom_thresh_dict["threshold_warning_supply_voltage_upper"]= str(u.val.float_val)
            
    dom_tranceiver_info.labels(device_ip=device_ip, interface=intfc).info(dom_trans_dict)
    dom_threshold_info.labels(device_ip=device_ip, interface=intfc).info(dom_thresh_dict)
    write_to_prometheus(registry=dom_time_registry)
    write_to_prometheus(registry=dom_registry)
    _logger.debug("gNMI subscription dom info to prometheus for %s ",device_ip)