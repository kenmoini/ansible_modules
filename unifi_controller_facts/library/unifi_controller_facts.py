#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: unifi_controller_facts
short_description: Manage your UniFi Controllers with Ansible
author: "Ken Moini (@kenmoini)"
'''

EXAMPLES = '''
- name: Get User List
  unifi_controller_facts:
    controller_baseURL: "https://127.0.0.1:8443"
    controller_username: "admin"
    controller_password: "changeme"
    controller_site: "default"
    query: list_users
  register: returndData

- name: List online clients
  unifi_controller_facts:
    controller_baseURL: "https://192.168.1.224:8443"
    controller_username: "admin"
    controller_password: "changeme"
    controller_site: "default"
    query: list_online_clients
  register: returndData
'''

from ansible.module_utils.basic import *
import json
import requests
import time

s = requests.session()

# ---------------------------------------------------------------------------------------------------------------------
# Function: unifi_login
# ---------------------------------------------------------------------------------------------------------------------
# Logs in the user, establishes the cookie
# required parameter <controller_baseURL>   = (str) The hostname and port of the target controller
# required parameter <controller_username>  = (str) The username to authenticate as
# required parameter <controller_password>  = (str) The password to authenticate with
#
# Returns
#  dict(
#   "status_code"   => (int) The HTTP Status Code returned,
#   "data"          => (json) Returned JSON from login attempt
#  )
# ---------------------------------------------------------------------------------------------------------------------
def unifi_login(data):
    s.headers.update({'referer': data['controller_baseURL'] + "/login"})
    l = s.post(data['controller_baseURL'] + "/api/login", json.dumps({"username":data["controller_username"], "password":data["controller_password"]}), verify=False)
    return {"status_code": l.status_code, "data": l.json()}
# ---------------------------------------------------------------------------------------------------------------------
# Function: unifi_logout
# ---------------------------------------------------------------------------------------------------------------------
# Logs the user out, destroys the session
# required parameter <controller_baseURL>   = (str) The hostname and port of the target controller
#
# Returns
#  stdObject
# ---------------------------------------------------------------------------------------------------------------------
def unifi_logout(controller_baseURL):
    l = s.get(controller_baseURL + "/logout")
    return l
# ---------------------------------------------------------------------------------------------------------------------
# Function: process_response
# ---------------------------------------------------------------------------------------------------------------------
# Process response returned by API commands
# ---------------------------------------------------------------------------------------------------------------------
def process_response(response_json):
    decoded_response = json.loads(response_json.text)
    if decoded_response['meta']['rc'] == "ok":
        if isinstance(decoded_response['data'], list):
            return False, True, {"status": response_json.status_code, "data": response_json.text}
        else:
            return False, True, {"status": response_json.status_code, "data": "SUCCESS"}
    else:
        return True, False, {"status": response_json.status_code, "data": response_json.text}

# ---------------------------------------------------------------------------------------------------------------------
# Function: process_response_boolean
# ---------------------------------------------------------------------------------------------------------------------
# Process response returned by API commands, returns SUCCESS if the response was just a boolean
# ---------------------------------------------------------------------------------------------------------------------
def process_response_boolean(response_json):
    decoded_response = json.loads(response_json.text)
    if decoded_response['meta']['rc'] == "ok":
        return False, True, {"status": response_json.status_code, "data": "SUCCESS"}
    else:
        return True, False, {"status": response_json.status_code, "data": response_json.text}

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_online_clients - List online client device(s)
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of online client device objects, or in case of a single device request, returns a single client device object
# optional parameter <client_mac> = the MAC address of a single online client device for which the call must be made
# ---------------------------------------------------------------------------------------------------------------------
def list_online_clients(data):
    if data['client_mac'] is not None:
        responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/sta/" + data['client_mac'].strip(), verify=False)
    else:
        responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/sta/", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_guests - List guest devices [UNTESTED]
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of guest device objects with valid access
# optional parameter <since> = time frame in hours to go back to list guests with valid access (default = 24*365 hours)
# ---------------------------------------------------------------------------------------------------------------------
def list_guests(data):
    if data['since'] is not None:
        within = int(data['since'])
    else:
        within = 8760 #In hours, Default: 1yr 24*365
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/guest", params={"within": within}, verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_users - List client devices
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of known client device objects
# ---------------------------------------------------------------------------------------------------------------------
def list_users(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/list/user", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_user_groups - List user groups
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of user group objects
# ---------------------------------------------------------------------------------------------------------------------
def list_user_groups(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/list/usergroup", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: stat_all_users - List all client devices ever connected to the site
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of client device objects
# optional parameter <since> = hours to go back (default is 8760 hours or 1 year)
#
# NOTES:
# - <historyhours> is only used to select clients that were online within that period,
#   the returned stats per client are all-time totals, irrespective of the value of <historyhours>
# ---------------------------------------------------------------------------------------------------------------------
def stat_all_users(data):
    if data['since'] is not None:
        within = int(data['since'])
    else:
        within = 8760 #In hours, Default: 1yr 24*365
    paramsToSend = {"within": within, "type": "all", "conn": "all"} # type: all/user/guest, conn: all/wired/wireless
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/alluser", params=paramsToSend, verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: stat_authorizations - Show all authorizations
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of authorization objects
# optional parameter <start_epoch> = Unix timestamp in seconds
# optional parameter <end_epoch>   = Unix timestamp in seconds
#
# NOTES:
# - defaults to the past 7*24 hours
# ---------------------------------------------------------------------------------------------------------------------
def stat_authorizations(data):
    if data['end_epoch'] is not None:
        end = int(data['end_epoch'])
    else:
        end = int(time.time())
    if data['start_epoch'] is not None:
        start = int(data['start_epoch'])
    else:
        start = int(end - (7*24*3600))
    paramsToSend = {"start": start, "end": end}
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/authorization", params=paramsToSend, verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: stat_sessions - Show all login sessions
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of login session objects for all devices or a single device
# optional parameter <start_epoch> = Unix timestamp in seconds
# optional parameter <end_epoch>   = Unix timestamp in seconds
# optional parameter <client_mac>   = client MAC address to return sessions for (can only be used when start and end are also provided)
# optional parameter <type>  = client type to return sessions for, can be 'all', 'guest' or 'user'; default value is 'all'
#
# NOTES:
# - defaults to the past 7*24 hours
# ---------------------------------------------------------------------------------------------------------------------
def stat_sessions(data):
    if data['end_epoch'] is not None:
        end = int(data['end_epoch'])
    else:
        end = int(time.time())
    if data['start_epoch'] is not None:
        start = int(data['start_epoch'])
    else:
        start = int(end - (7*24*3600))
    if data['client_mac'] is not None:
        paramsToSend = { "start": start, "end": end, "type": "all", "mac": data['client_mac'].strip() }
    else:
        paramsToSend = { "start": start, "end": end, "type": "all" }
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/session", params=paramsToSend, verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_devices - List access points and other devices under management of the controller (USW and/or USG devices)
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of known device objects (or a single device when using the <device_mac> parameter)
# optional parameter <device_mac> = the MAC address of a single device for which the call must be made
# ---------------------------------------------------------------------------------------------------------------------
def list_devices(data):
    if data['device_mac'] is not None:
        responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/device/" + data['client_mac'].strip(), verify=False)
    else:
        responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/device/", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_wlan_groups -List wlan_groups
# ---------------------------------------------------------------------------------------------------------------------
# returns an array containing known wlan_groups
# ---------------------------------------------------------------------------------------------------------------------
def list_wlan_groups(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/list/wlangroup", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_rouge_access_points - List rogue/neighboring access points
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of rogue/neighboring access point objects
# optional parameter <since> = hours to go back to list discovered "rogue" access points (default = 24 hours)
# ---------------------------------------------------------------------------------------------------------------------
def list_rouge_access_points(data):
    if data['since'] is not None:
        within = int(data['since'])
    else:
        within = 24 #In hours, Default: 24
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/rogueap", params={"within": within}, verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_known_rogue_access_points - List known rogue access points
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of known rogue access point objects
# ---------------------------------------------------------------------------------------------------------------------
def list_known_rogue_access_points(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/rest/rogueknown", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_tags - List (device) tags (using REST)
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of known device tag objects
#
# NOTES: this endpoint was introduced with controller versions 5.5.X
# ---------------------------------------------------------------------------------------------------------------------
def list_tags(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/rest/tag", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: five_minute_site_stats - 5 minutes site stats method [UNTESTED]
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of 5-minute stats objects for the current site
# optional parameter <start_epoch> = Unix timestamp in milliseconds
# optional parameter <end_epoch>   = Unix timestamp in milliseconds
#
# NOTES:
# - defaults to the past 12 hours
# - this function/method is only supported on controller versions 5.5.* and later
# - make sure that the retention policy for 5 minutes stats is set to the correct value in
#   the controller settings
# ---------------------------------------------------------------------------------------------------------------------
def five_minute_site_stats(data):
    if data['end_epoch'] is not None:
        end = int(data['end_epoch'])
    else:
        end = int(time.time() * 1000) #Supa future
    if data['start_epoch'] is not None:
        start = int(data['start_epoch'])
    else:
        start = int(end - (12*3600*1000))
    paramsToSend = {"attrs": ['bytes', 'wan-tx_bytes', 'wan-rx_bytes', 'wlan_bytes', 'num_sta', 'lan-num_sta', 'wlan-num_sta', 'time'], "start": start, "end": end}
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/report/5minutes.site", params=paramsToSend, verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: hourly_site_stats - Hourly site stats [UNTESTED]
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of hourly stats objects for the current site
# optional parameter <start_epoch> = Unix timestamp in milliseconds
# optional parameter <end_epoch>   = Unix timestamp in milliseconds
#
# NOTES:
# - defaults to the past 7*24 hours
# - "bytes" are no longer returned with controller version 4.9.1 and later
# ---------------------------------------------------------------------------------------------------------------------
def hourly_site_stats(data):
    if data['end_epoch'] is not None:
        end = int(data['end_epoch'])
    else:
        end = int(time.time() * 1000) #Supa future
    if data['start_epoch'] is not None:
        start = int(data['start_epoch'])
    else:
        start = int(end - (7*24*3600*1000))
    paramsToSend = {"attrs": ['bytes', 'wan-tx_bytes', 'wan-rx_bytes', 'wlan_bytes', 'num_sta', 'lan-num_sta', 'wlan-num_sta', 'time'], "start": start, "end": end}
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/report/hourly.site", params=paramsToSend, verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: daily_site_stats - Daily site stats [UNTESTED]
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of hourly stats objects for the current site
# optional parameter <start_epoch> = Unix timestamp in milliseconds
# optional parameter <end_epoch>   = Unix timestamp in milliseconds
#
# NOTES:
# - defaults to the past 7*24 hours
# - "bytes" are no longer returned with controller version 4.9.1 and later
# ---------------------------------------------------------------------------------------------------------------------
def daily_site_stats(data):
    if data['end_epoch'] is not None:
        end = int(data['end_epoch'])
    else:
        end = int(time.time() * 1000) #Supa future
    if data['start_epoch'] is not None:
        start = int(data['start_epoch'])
    else:
        start = int(end - (52*7*24*3600*1000))
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/report/daily.site", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: all_sites_stats - List sites stats
# ---------------------------------------------------------------------------------------------------------------------
# returns statistics for all sites hosted on this controller
#
# NOTES: this endpoint was introduced with controller version 5.2.9
# ---------------------------------------------------------------------------------------------------------------------
def all_sites_stats(data):
    responseData = s.get(data['controller_baseURL'] + "/api/stat/sites", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: five_minute_access_point_stats - 5 minutes stats method for a single access point or all access points [UNTESTED]
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of 5-minute stats objects
# optional parameter <start_epoch> = Unix timestamp in milliseconds
# optional parameter <end_epoch>   = Unix timestamp in milliseconds
# optional parameter <device_mac>   = AP MAC address to return stats for
#
# NOTES:
# - defaults to the past 12 hours
# - this function/method is only supported on controller versions 5.5.* and later
# - make sure that the retention policy for 5 minutes stats is set to the correct value in
#   the controller settings
# ---------------------------------------------------------------------------------------------------------------------
def five_minute_access_point_stats(data):
    if data['end_epoch'] is not None:
        end = int(data['end_epoch'])
    else:
        end = int(time.time() * 1000) #Supa future
    if data['start_epoch'] is not None:
        start = int(data['start_epoch'])
    else:
        start = int(end - (12*3600*1000))
    if data['device_mac'] is not None:
        paramsToSend = { "start": start, "end": end, "attrs": ['bytes', 'num_sta', 'time'], "mac": data['device_mac'].strip() }
    else:
        paramsToSend = { "start": start, "end": end, "attrs": ['bytes', 'num_sta', 'time'] }
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/report/5minutes.ap", params=paramsToSend, verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: hourly_access_point_stats - Hourly stats method for a single access point or all access points [UNTESTED]
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of hourly stats objects
# optional parameter <start_epoch> = Unix timestamp in milliseconds
# optional parameter <end_epoch>   = Unix timestamp in milliseconds
# optional parameter <device_mac>   = AP MAC address to return stats for
#
# NOTES:
# - defaults to the past 7*24 hours
# - UniFi controller does not keep these stats longer than 5 hours with versions < 4.6.6
# ---------------------------------------------------------------------------------------------------------------------
def hourly_access_point_stats(data):
    if data['end_epoch'] is not None:
        end = int(data['end_epoch'])
    else:
        end = int(time.time() * 1000) #Supa future
    if data['start_epoch'] is not None:
        start = int(data['start_epoch'])
    else:
        start = int(end - (7*24*3600*1000))
    if data['device_mac'] is not None:
        paramsToSend = { "start": start, "end": end, "attrs": ['bytes', 'num_sta', 'time'], "mac": data['device_mac'].strip() }
    else:
        paramsToSend = { "start": start, "end": end, "attrs": ['bytes', 'num_sta', 'time'] }
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/report/hourly.ap", params=paramsToSend, verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: daily_access_point_stats - Daily stats method for a single access point or all access points [UNTESTED]
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of daily stats objects
# optional parameter <start_epoch> = Unix timestamp in milliseconds
# optional parameter <end_epoch>   = Unix timestamp in milliseconds
# optional parameter <device_mac>   = AP MAC address to return stats for
#
# NOTES:
# - defaults to the past 7*24 hours
# - UniFi controller does not keep these stats longer than 5 hours with versions < 4.6.6
# ---------------------------------------------------------------------------------------------------------------------
def daily_access_point_stats(data):
    if data['end_epoch'] is not None:
        end = int(data['end_epoch'])
    else:
        end = int(time.time() * 1000) #Supa future
    if data['start_epoch'] is not None:
        start = int(data['start_epoch'])
    else:
        start = int(end - (7*24*3600*1000))
    if data['device_mac'] is not None:
        paramsToSend = { "start": start, "end": end, "attrs": ['bytes', 'num_sta', 'time'], "mac": data['device_mac'].strip() }
    else:
        paramsToSend = { "start": start, "end": end, "attrs": ['bytes', 'num_sta', 'time'] }
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/report/daily.ap", params=paramsToSend, verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function five_minute_site_dashboard_metrics - List dashboard metrics from the last 5 minutes
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of dashboard metric objects (available since controller version 4.9.1.alpha)
# ---------------------------------------------------------------------------------------------------------------------
def five_minute_site_dashboard_metrics(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/dashboard?scale=5minutes", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function hourly_site_dashboard_metrics - List dashboard metrics from the last hour
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of dashboard metric objects (available since controller version 4.9.1.alpha)
# ---------------------------------------------------------------------------------------------------------------------
def hourly_site_dashboard_metrics(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/dashboard", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: site_health_metrics - List health metrics
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of health metric objects
# ---------------------------------------------------------------------------------------------------------------------
def site_health_metrics(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/health", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: port_forwarding_stats - List port forwarding stats
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of port forwarding stats
# ---------------------------------------------------------------------------------------------------------------------
def port_forwarding_stats(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/portforward", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: dpi_stats - List DPI stats
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of DPI stats
# ---------------------------------------------------------------------------------------------------------------------
def dpi_stats(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/dpi", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: stat_vouchers - List vouchers
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of hotspot voucher objects
# optional parameter <created_time> = Unix timestamp in seconds
# ---------------------------------------------------------------------------------------------------------------------
def stat_vouchers(data):
    if data['created_time'] is not None:
        responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/voucher", params={"created_time": data['created_time']}, verify=False)
    else:
        responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/voucher", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: stat_payments - List payments [UNTESTED]
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of hotspot payments
# optional parameter <since> = number of hours to go back to fetch payments
# ---------------------------------------------------------------------------------------------------------------------
def stat_payments(data):
    if data['since'] is not None:
        responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/payment?within=" + int(data['since']), verify=False)
    else:
        responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/payment", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_hotspot_operators - List hotspot operators (using REST) [UNTESTED]
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of hotspot operators
# ---------------------------------------------------------------------------------------------------------------------
def list_hotspot_operators(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/rest/hotspotop", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_sites - List sites on this controller
# ---------------------------------------------------------------------------------------------------------------------
# returns a list sites hosted on this controller with some details
# ---------------------------------------------------------------------------------------------------------------------
def list_sites(data):
    responseData = s.get(data['controller_baseURL'] + "/api/self/sites", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: sysinfo - Show sysinfo
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of known sysinfo data
# ---------------------------------------------------------------------------------------------------------------------
def sysinfo(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/sysinfo", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_site_settings - List site settings
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of site configuration settings
# ---------------------------------------------------------------------------------------------------------------------
def list_site_settings(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/get/setting", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_admins_for_current_site - List admins for current site [404 ERROR]
# ---------------------------------------------------------------------------------------------------------------------
# returns an array containing administrator objects for selected site
# ---------------------------------------------------------------------------------------------------------------------
def list_admins_for_current_site(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/cmd/sitemgr", params={"cmd": "get-admins"}, verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_admins_for_all_sites - List admins across all sites on this controller
# ---------------------------------------------------------------------------------------------------------------------
# returns an array containing administrator objects for all sites
# ---------------------------------------------------------------------------------------------------------------------
def list_admins_for_all_sites(data):
    responseData = s.get(data['controller_baseURL'] + "/api/stat/admin", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_wlan_configuration - List wlan settings (using REST)
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of wireless networks and their settings, or an array containing a single wireless network when using
# the <wlan_id> parameter
# optional parameter <wlan_id> = 24 char string; _id of the wlan to fetch the settings for
# ---------------------------------------------------------------------------------------------------------------------
def list_wlan_configuration(data):
    if data['wlan_id'] is not None:
        responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/rest/wlanconf/" + str(data['wlan_id'].strip()), verify=False)
    else:
        responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/rest/wlanconf/", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_current_channels - List current channels
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of currently allowed channels
# ---------------------------------------------------------------------------------------------------------------------
def list_current_channels(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/current-channel", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_voip_extensions - List VoIP Extensions [400 ERROR]
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of VoIP extensions
# ---------------------------------------------------------------------------------------------------------------------
def list_voip_extensions(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/list/extension", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_network_configuration - List network settings (using REST)
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of (non-wireless) networks and their settings
# optional parameter <network_id> = string; network id to get specific network data for
# ---------------------------------------------------------------------------------------------------------------------
def list_network_configuration(data):
    if data['network_id'] is not None:
        responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/rest/networkconf/" + str(data['network_id'].strip()), verify=False)
    else:
        responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/rest/networkconf/", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_port_configuration -  List port configurations [UNTESTED
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of port configurations
# ---------------------------------------------------------------------------------------------------------------------
def list_port_configuration(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/list/portconf", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_port_forwarding_rules - List port forwarding settings [UNTESTED]
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of port forwarding settings
# ---------------------------------------------------------------------------------------------------------------------
def list_port_forwarding_rules(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/list/portforward", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_firewall_groups - List firewall groups (using REST) [UNTESTED
# ---------------------------------------------------------------------------------------------------------------------
# returns an array containing the current firewall groups on success
# ---------------------------------------------------------------------------------------------------------------------
def list_firewall_groups(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/rest/firewallgroup", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: dynamic_dns_configuration - List dynamic DNS settings [UNTESTED]
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of dynamic DNS settings
# ---------------------------------------------------------------------------------------------------------------------
def dynamic_dns_configuration(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/list/dynamicdns", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_country_codes - List country codes
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of available country codes
#
# NOTES:
# these codes following the ISO standard:
# https://en.wikipedia.org/wiki/ISO_3166-1_numeric
# ---------------------------------------------------------------------------------------------------------------------
def list_country_codes(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/ccode", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_auto_backups - List auto backups [ERROR 404]
# ---------------------------------------------------------------------------------------------------------------------
# return an array containing objects with backup details on success
# ---------------------------------------------------------------------------------------------------------------------
def list_auto_backups(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/cmd/backup", params={"cmd": "list-backups"}, verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_radius_profiles - List Radius profiles (using REST) [UNTESTED]
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of objects containing all Radius profiles for the current site
#
# NOTES:
# - this function/method is only supported on controller versions 5.5.19 and later
# ---------------------------------------------------------------------------------------------------------------------
def list_radius_profiles(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/rest/radiusprofile", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_radius_accounts - List Radius user accounts (using REST) [UNTESTED]
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of objects containing all Radius accounts for the current site
#
# NOTES:
# - this function/method is only supported on controller versions 5.5.19 and later
# ---------------------------------------------------------------------------------------------------------------------
def list_radius_accounts(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/rest/account", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_alarms - List alarms [UNTESTED]
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of known alarms
# ---------------------------------------------------------------------------------------------------------------------
def list_alarms(data):
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/list/alarm", verify=False)
    return process_response(responseData)

# ---------------------------------------------------------------------------------------------------------------------
# Function: list_events - List events [UNTESTED]
# ---------------------------------------------------------------------------------------------------------------------
# returns an array of known events
# optional parameter <since>            = hours to go back, default value is 720 hours
# optional parameter <start_num>        = which event number to start with (useful for paging of results), default value is 0
# optional parameter <limit_num>        = number of events to return, default value is 3000
# ---------------------------------------------------------------------------------------------------------------------
def list_events(data):
    if data['since'] is not None:
        within = int(data['since'])
    else:
        start = 720 #In hours, Default: 24
    if data['start_num'] is not None:
        start = int(data['start_num'])
    else:
        within = 720 #In hours, Default: 24
    if data['limit_num'] is not None:
        limit = int(data['limit_num'])
    else:
        limit = 720 #In hours, Default: 24
    paramsToSend = {'_sort': "-time", "within": within, 'type': None, '_start': start, '_limit': limit}
    responseData = s.get(data['controller_baseURL'] + "/api/s/" + data['controller_site'] + "/stat/event", params=paramsToSend, verify=False)
    return process_response(responseData)

def main():

    fields = {
        "controller_username": {"required": True, "type": "str"},
        "controller_password": {"required": True, "type": "str", "no_log": True},
        "controller_baseURL": {"required": True, "type": "str"},
        "controller_site": {"required": False, "type": "str", "default": "default"},
        "query": {
            "default": "list_sites",
            "type": 'str',
            "choices": ['list_clients', 'list_online_clients', 'list_guests', 'list_users', 'list_user_groups', 'stat_all_users', 'stat_authorizations', 'stat_sessions', 'list_devices', 'list_wlan_groups', 'list_rouge_access_points', 'list_known_rogue_access_points', 'list_tags', 'five_minute_site_stats', 'hourly_site_stats', 'daily_site_stats', 'all_sites_stats', 'five_minute_access_point_stats', 'hourly_access_point_stats', 'daily_access_point_stats', 'five_minute_site_dashboard_metrics', 'hourly_site_dashboard_metrics', 'site_health_metrics', 'port_forwarding_stats', 'dpi_stats', 'stat_vouchers', 'stat_payments', 'list_hotspot_operators', 'list_sites', 'sysinfo', 'list_site_settings', 'list_admins_for_current_site', 'list_admins_for_all_sites', 'list_wlan_configuration', 'list_current_channels', 'list_voip_extensions', 'list_network_configuration', 'list_port_configuration', 'list_port_forwarding_rules', 'list_firewall_groups', 'dynamic_dns_configuration', 'list_country_codes', 'list_auto_backups', 'list_radius_profiles', 'list_radius_accounts', 'list_alarms', 'list_events']
        },
        "hourly_timeframe": {"required": False, "type": "int", "default": "8760"},
        "since": {"required": False, "type": "int", "default": None},
        "start_num": {"required": False, "type": "int", "default": None},
        "limit_num": {"required": False, "type": "int", "default": None},
        "start_epoch": {"required": False, "type": "int", "default": None},
        "end_epoch": {"required": False, "type": "int", "default": None},
        "created_time": {"required": False, "type": "int", "default": None},
        "device_mac": {"required": False, "type": "str", "default": None},
        "client_mac": {"required": False, "type": "str", "default": None},
        "network_id": {"required": False, "type": "str", "default": None},
        "wlan_id": {"required": False, "type": "str", "default": None},
    }

    choice_map = {
        'list_clients': list_online_clients,
        'list_online_clients': list_online_clients,
        'list_guests': list_guests,
        'list_users': list_users,
        'list_user_groups': list_user_groups,
        'stat_all_users': stat_all_users,
        'stat_authorizations': stat_authorizations,
        'stat_sessions': stat_sessions,
        'list_devices': list_devices,
        'list_wlan_groups': list_wlan_groups,
        'list_rouge_access_points': list_rouge_access_points,
        'list_known_rogue_access_points': list_known_rogue_access_points,
        'list_tags': list_tags,
        'five_minute_site_stats': five_minute_site_stats,
        'hourly_site_stats': hourly_site_stats,
        'daily_site_stats': daily_site_stats,
        'all_sites_stats': all_sites_stats,
        'five_minute_access_point_stats': five_minute_access_point_stats,
        'hourly_access_point_stats': hourly_access_point_stats,
        'daily_access_point_stats': daily_access_point_stats,
        'five_minute_site_dashboard_metrics': five_minute_site_dashboard_metrics,
        'hourly_site_dashboard_metrics': hourly_site_dashboard_metrics,
        'site_health_metrics': site_health_metrics,
        'port_forwarding_stats': port_forwarding_stats,
        'dpi_stats': dpi_stats,
        'stat_vouchers': stat_vouchers,
        'stat_payments': stat_payments,
        'list_hotspot_operators': list_hotspot_operators,
        'list_sites': list_sites,
        'sysinfo': sysinfo,
        'list_site_settings': list_site_settings,
        'list_admins_for_current_site': list_admins_for_current_site,
        'list_admins_for_all_sites': list_admins_for_all_sites,
        'list_wlan_configuration': list_wlan_configuration,
        'list_current_channels': list_current_channels,
        'list_voip_extensions': list_voip_extensions,
        'list_network_configuration': list_network_configuration,
        'list_port_configuration': list_port_configuration,
        'list_port_forwarding_rules': list_port_forwarding_rules,
        'list_firewall_groups': list_firewall_groups,
        'dynamic_dns_configuration': dynamic_dns_configuration,
        'list_country_codes': list_country_codes,
        'list_auto_backups': list_auto_backups,
        'list_radius_profiles': list_radius_profiles,
        'list_radius_accounts': list_radius_accounts,
        'list_alarms': list_alarms,
        'list_events': list_events
    }

    module = AnsibleModule(argument_spec=fields, supports_check_mode=False)

    fireLogin = unifi_login({'controller_baseURL': module.params['controller_baseURL'], "controller_username": module.params['controller_username'], "controller_password": module.params['controller_password']})
    if fireLogin['status_code'] == 200:
        is_error, has_changed, result = choice_map.get(module.params['query'])(module.params)
    else:
        res = {"status": fireLogin['status_code'], "data": fireLogin['data']}
        is_error, has_changed, result = (True, False, res)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error", meta=result)


if __name__ == '__main__':
    main()
