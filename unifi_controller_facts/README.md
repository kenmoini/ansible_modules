# unifi_controller_facts - UniFi Controller Facts Ansible Module

This project is to extend the UniFi Controller API and consume it via a native Ansible module.
There are a few difficulties with this sort of thing, first being the lack of UniFi Controller API documentation.  It's pretty much non-existant.  This project is largely based on this project: [https://github.com/Art-of-WiFi/UniFi-API-client/], this is basically a Python port of that client, you may notice many similarities.

## What does this do?
This module provides a simple, yet needed extension of the UniFi Controller API.  With this module, you can query your UniFi Controller and gather facts and information.  This module doesn't have many actions (read: none), the primary purpose is to gather information from the UniFi Controller.  In order to manipulate your UniFi Controller, you'll need my unifi_controller Ansible module (coming soon).

## Instructions
1) Download, fork, obtain this source code somehow
2) Load it onto a machine that has Ansible installed
3) Note the test.yml file for examples on how to use the module

## Example
    - name: Get User List
      unifi_controller_facts:
        controller_baseURL: "https://127.0.0.1:8443"
        controller_username: "admin"
        controller_password: "changeme"
        controller_site: "default"
        query: list_users
      register: returnedData

## Available queries
**Clients**
--list_online_clients
--list_clients
--list_guests
--list_users
--list_user_groups
--stat_all_users
--stat_authorizations
--stat_sessions
**Devices**
--list_devices
--list_wlan_goups
--list_rouge_access_points
--list_known_rogue_access_points
--list_tags
**Stats**
--five_minute_site_stats
--hourly_site_stats
--daily_site_stats
--all_site_stats
--five_minute_access_point_stats
--hourly_access_point_stats
--daily_access_point_stats
--five_minute_site_dashboard_metrics
--hourly_site_dashboard_metrics
--site_health_metrics
--port_forwarding_stats
--dpi_stats
**Hotspot**
--stat_vouchers
--stat_payments
--list_hotspot_operators
**Configuration**
--list_sites
--sysinfo
--list_site_settings
--list_admins_for_current_site
--list_wlan_configuration
--list_current_channels
--list_voip_extensions
--list_network_configuration
--list_port_configuration
--list_port_forwarding_rules
--list_firewall_groups
--dynamic_dns_configuration
--list_country_codes
--list_auto_backups
--list_radius_profiles
--list_radius_accounts
**Messages**
--list_alarms
--list_events


## Known Issues
* Documentation in embedded in the module script.  It should be copied and compiled externally probably a bit better...
* There are a few untested functions that I don't have the current capacity to fully develop/test, being that I lack a USG, and only have 2 UAPs.  If anyone would like to contribute code to support the UniFi switches, and cameras, etc, or maybe donate a device, that'd be much appreciated.
* There are also a few functions that seem to have been broken/made unavailable in the version of the UniFi Controller I operate (my setup isn't that old, I've only tested the 5.8.x line)

## License
GNU GPLv3

## Credits
* Based off of this project, so many thanks to the {wo}men who provided the groundwork https://github.com/Art-of-WiFi/UniFi-API-client/
* Ansible module was based off this starting point: https://blog.toast38coza.me/custom-ansible-module-hello-world/
