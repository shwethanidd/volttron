.. _SEP-2:

SEP 2.0 DER Support
===================

Version 1.0

Smart Energy Profile 2.0 (SEP2, IEEE 2030.5) specifies a REST architecture built
around the core HTTP verbs: GET, HEAD, PUT, POST and DELETE.
A specification for the SEP2 protocol can be found
`here <http://www.csee.org.cn/Portal/zh-cn/Publications/atm/docs-13-0200-00-sep2-smart-energy-profile-2.pdf.pdf>`_.

SEP2 EndDevices (clients) POST XML resources representing their state,
and GET XML resources containing command and control information from the server.
The server never reaches out to the client unless a "subscription" is
registered and supported for a particular resource type. This implementation
does not use SEP2 registered subscriptions.

The SEP2 specification requires HTTP headers, and it explicitly requires RESTful
response codes, for example:

    -   201 - "Created"
    -   204 - "No Content"
    -   301 - "Moved Permanently"
    -   etc.

SEP2 message encoding may be either XML or EXI.
Only XML is supported in this implementation.

SEP2 requires HTTPS/TLS version 1.2 along with support for the
cipher suite TLS_ECDHE_ECDSA_WITH_AES_128_CCM_8.
Production installation requires a certificate issued by a SEP2 CA.
The encryption requirement can be met by using a web server such as
Apache to proxy the HTTPs traffic.

SEP2 discovery, if supported, must be implemented by an xmDNS server.
Avahi can be modified to perform this function.

Function Sets
-------------

SEP2 groups XML resources into "Function Sets."  Some of these function sets
provide a core set of functionality used across higher-level function sets.
This implementation implements resources from the following function sets:

    -   Time
    -   Device Information
    -   Device Capabilities
    -   End Device
    -   Function Set Assignments
    -   Power Status
    -   Distributed Energy Resources

Distributed Energy Resources
----------------------------

Distributed energy resources (DERs) are devices that generate energy, e.g., solar inverters,
or store energy, e.g., battery storage systems, electric vehicle supply equipment (EVSEs).
These devices are managed by a SEP2 DER server using DERPrograms which are described by
the SEP2 specification as follows:

    Servers host one or more DERPrograms, which in turn expose DERControl events to DER clients.
    DERControl instances contain attributes that allow DER clients to respond to events
    that are targeted to their device type. A DERControl instance also includes scheduling
    attributes that allow DER clients to store and process future events. These attributes
    include start time and duration, as well an indication of the need for randomization of
    the start and / or duration of the event. The SEP2 DER client model is based on the
    SunSpec Alliance Inverter Control Model [SunSpec] which is derived from
    IEC 61850-90-7 [61850] and [EPRI].

EndDevices post multiple SEP2 resources describing their status.  The following is an
example of a Power Status resource that might be posted by an EVSE (vehicle charging
station):

.. code-block:: xml

    <PowerStatus xmlns="http://zigbee.org/sep" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" href="/sep2/edev/96/ps">
        <batteryStatus>4</batteryStatus>
        <changedTime>1487812095</changedTime>
        <currentPowerSource>1</currentPowerSource>
        <estimatedChargeRemaining>9300</estimatedChargeRemaining>
        <PEVInfo>
            <chargingPowerNow>
                <multiplier>3</multiplier>
                <value>-5</value>
            </chargingPowerNow>
            <energyRequestNow>
                <multiplier>3</multiplier>
                <value>22</value>
            </energyRequestNow>
            <maxForwardPower>
                <multiplier>3</multiplier>
                <value>7</value>
            </maxForwardPower>
            <minimumChargingDuration>11280</minimumChargingDuration>
            <targetStateOfCharge>10000</targetStateOfCharge>
            <timeChargeIsNeeded>9223372036854775807</timeChargeIsNeeded>
            <timeChargingStatusPEV>1487812095</timeChargingStatusPEV>
        </PEVInfo>
    </PowerStatus>

Design Details
--------------

.. image:: files/volttron_sep2.jpg

VOLTTRON's SEP2 implementation includes a SEP2Agent and a SEP2 device driver,
as described below.

VOLTTRON SEP2Agent
~~~~~~~~~~~~~~~~~~

SEP2Agent implements a SEP2 server that receives HTTP POST/PUT
requests from SEP2 devices. The requests are routed to SEP2Agent over the VOLTTRON
message bus by VOLTTRON's MasterWebService. SEP2Agent returns an appropriate HTTP
response. In some cases (e.g., DERControl requests), this response includes a data
payload.

SEP2Agent maps SEP2 resource data to a VOLTTRON SEP2 data model based on SunSpec,
using block numbers and point names as defined in the SunSpec Information Model,
which in turn is harmonized with 61850. The data model is given in detail below.

Each device's data is stored by SEP2Agent in an EndDevice memory structure. This
structure is not persisted to a database. Each EndDevice retains only the most
recently received value for each field.

SEP2Agent exposes RPC calls for getting and setting EndDevice data.

VOLTTRON SEP2 Device Driver
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The SEP2 device driver is a new addition to VOLTTRON MasterDriverAgent's family of
standard device drivers. It exposes get_point/set_point calls for SEP2 EndDevice fields.

The SEP2 device driver periodically issues SEP2Agent RPC calls to refresh its cached
representation of EndDevice data. It issues RPC calls to SEP2Agent as needed when
responding to get_point, set_point and scrape_all calls.

Field Definitions
~~~~~~~~~~~~~~~~~

These field IDs correspond to the ones in the SEP2 device driver's configuration file, sep2.csv.
They have been used in that file's "Volttron Point Name" column and also in its "Point Name" column.

================= ======================== ==================================================== ======= ======
Field ID          SEP2 Resource/Property   Description                                          Units   Type
================= ======================== ==================================================== ======= ======
b1_Md             device_information       Model (32 char lim).                                         string
                    mfModel
b1_Opt            device_information       Long-form device identifier (32 char lim).                   string
                    lfdi
b1_SN             abstract_device          Short-form device identifier (32 char lim).                  string
                    sfdi
b1_Vr             device_information       Version (16 char lim).                                       string
                    mfHwVer
b113_A            mirror_meter_reading     AC current.                                          A       float
                    PhaseCurrentAvg
b113_DCA          mirror_meter_reading     DC current.                                          A       float
                    InstantPackCurrent
b113_DCV          mirror_meter_reading     DC voltage.                                          V       float
                    LineVoltageAvg
b113_DCW          mirror_meter_reading     DC power.                                            W       float
                    PhasePowerAvg
b113_PF           mirror_meter_reading     AC power factor.                                     %       float
                    PhasePFA
b113_WH           mirror_meter_reading     AC energy.                                           Wh      float
                    EnergyIMP
b120_AhrRtg       der_capability           Usable capacity of the battery.                      Ah      float
                    rtgAh                  Maximum charge minus minimum charge.
b120_ARtg         der_capability           Maximum RMS AC current level capability of the       A       float
                    rtgA                   inverter.
b120_MaxChaRte    der_capability           Maximum rate of energy transfer into the device.     W       float
                    rtgMaxChargeRate
b120_MaxDisChaRte der_capability           Maximum rate of energy transfer out of the device.   W       float
                    rtgMaxDischargeRate
b120_WHRtg        der_capability           Nominal energy rating of the storage device.         Wh      float
                    rtgWh
b120_WRtg         der_capability           Continuous power output capability of the inverter.  W       float
                    rtgW
b121_WMax         der_settings             Maximum power output. Default to WRtg.               W       float
                    setMaxChargeRate
b122_ActWh        mirror_meter_reading     AC lifetime active (real) energy output.             Wh      float
                    EnergyEXP
b122_StorConn     der_status               CONNECTED=0, AVAILABLE=1, OPERATING=2, TEST=3.               enum
                    storConnectStatus
b124_WChaMax      der_control              Setpoint for maximum charge. This is the only        W       float
                    opModFixedFlow         field that is writable with a set_point call.
b403_Tmp          mirror_meter_reading     Pack temperature.                                    C       float
                    InstantPackTemp
b404_DCW          PEVInfo                  Power flow in or out of the inverter.                W       float
                    chargingPowerNow
b404_DCWh         der_availability         Output energy (absolute SOC).                        Wh      float
                    availabilityDuration   Calculated as (availabilityDuration / 3600) * WMax.
b802_LocRemCtl    der_status               Control Mode: REMOTE=0, LOCAL=1.                             enum
                    localControlModeStatus
b802_SoC          der_status               State of Charge %.                                   % WHRtg float
                    stateOfChargeStatus
b802_State        der_status               DISCONNECTED=1, INITIALIZING=2, CONNECTED=3,                 enum
                    inverterStatus         STANDBY=4, SOC PROTECTION=5, FAULT=99.
================= ======================== ==================================================== ======= ======

Revising and Expanding the Field Definitions
--------------------------------------------

The SEP2-to-SunSpec field mappings in this implementation are a relatively thin subset of all possible
field definitions. Developers are encouraged to expand the definitions.

The procedure for expanding the field mappings requires you to make changes in two places:

1. Update the driver's point definitions in services/core/MasterDriverAgent/master_driver/sep2.csv
2. Update the SEP2-to-SunSpec field mappings in services/core/SEP2Agent/sep2/end_device.py and __init__.py

When updating VOLTTRON's SEP2 data model, please use field IDs that conform to the SunSpec
block-number-and-field-name model outlined in the SunSpec Information Model Reference
(see the link below).

For Further Information
-----------------------

SunSpec References:

    -   Information model specification: http://sunspec.org/wp-content/uploads/2015/06/SunSpec-Information-Models-12041.pdf
    -   Information model reference spreadsheet: http://sunspec.org/wp-content/uploads/2015/06/SunSpec-Information-Model-Reference.xlsx
    -   Inverter models: http://sunspec.org/wp-content/uploads/2015/06/SunSpec-Inverter-Models-12020.pdf
    -   Energy storage models: http://sunspec.org/wp-content/uploads/2015/06/SunSpec-Energy-Storage-Models-12032.pdf

Questions? Please contact:

    -   Rob Calvert (rob@kisensum.com) or James Sheridan (james@kisensum.com)
