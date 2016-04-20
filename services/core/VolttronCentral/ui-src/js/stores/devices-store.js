'use strict';

var ACTION_TYPES = require('../constants/action-types');
var authorizationStore = require('../stores/authorization-store');
var dispatcher = require('../dispatcher');
var Store = require('../lib/store');

var devicesStore = new Store();

var _action = "get_scan_settings";
var _view = "Detect Devices";
var _device = null;
var _data = null;

var _registryValues = [
    [
        {"key": "Point_Name", "value": "Heartbeat"},
        {"key": "Volttron_Point_Name", "value": "Heartbeat"},
        {"key": "Units", "value": "On/Off"},
        {"key": "Units_Details", "value": "On/Off"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": 0},
        {"key": "Type", "value": "boolean"},
        {"key": "Notes", "value": "Point for heartbeat toggle"}
    ],
    [
        {"key": "Point_Name", "value": "OutsideAirTemperature1"},
        {"key": "Volttron_Point_Name", "value": "OutsideAirTemperature1"},
        {"key": "Units", "value": "F"},
        {"key": "Units_Details", "value": "-100 to 300"},
        {"key": "Writable", "value": false},
        {"key": "Starting_Value", "value": 50},
        {"key": "Type", "value": "float"},
        {"key": "Notes", "value": "CO2 Reading 0.00-2000.0 ppm"}
    ],
    [
        {"key": "Point_Name", "value": "SampleWritableFloat1"},
        {"key": "Volttron_Point_Name", "value": "SampleWritableFloat1"},
        {"key": "Units", "value": "PPM"},
        {"key": "Units_Details", "value": "1000.00 (default)"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": 10},
        {"key": "Type", "value": "float"},
        {"key": "Notes", "value": "Setpoint to enable demand control ventilation"}
    ],
    [
        {"key": "Point_Name", "value": "SampleLong1"},
        {"key": "Volttron_Point_Name", "value": "SampleLong1"},
        {"key": "Units", "value": "Enumeration"},
        {"key": "Units_Details", "value": "1 through 13"},
        {"key": "Writable", "value": false},
        {"key": "Starting_Value", "value": 50},
        {"key": "Type", "value": "int"},
        {"key": "Notes", "value": "Status indicator of service switch"}
    ],
    [
        {"key": "Point_Name", "value": "SampleWritableShort1"},
        {"key": "Volttron_Point_Name", "value": "SampleWritableShort1"},
        {"key": "Units", "value": "%"},
        {"key": "Units_Details", "value": "0.00 to 100.00 (20 default)"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": 20},
        {"key": "Type", "value": "int"},
        {"key": "Notes", "value": "Minimum damper position during the standard mode"}
    ],
    [
        {"key": "Point_Name", "value": "SampleBool1"},
        {"key": "Volttron_Point_Name", "value": "SampleBool1"},
        {"key": "Units", "value": "On / Off"},
        {"key": "Units_Details", "value": "on/off"},
        {"key": "Writable", "value": false},
        {"key": "Starting_Value", "value": true},
        {"key": "Type", "value": "boolean"},
        {"key": "Notes", "value": "Status indidcator of cooling stage 1"}
    ],
    [
        {"key": "Point_Name", "value": "SampleWritableBool1"},
        {"key": "Volttron_Point_Name", "value": "SampleWritableBool1"},
        {"key": "Units", "value": "On / Off"},
        {"key": "Units_Details", "value": "on/off"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": true},
        {"key": "Type", "value": "boolean"},
        {"key": "Notes", "value": "Status indicator"}
    ],
    [
        {"key": "Point_Name", "value": "OutsideAirTemperature2"},
        {"key": "Volttron_Point_Name", "value": "OutsideAirTemperature2"},
        {"key": "Units", "value": "F"},
        {"key": "Units_Details", "value": "-100 to 300"},
        {"key": "Writable", "value": false},
        {"key": "Starting_Value", "value": 50},
        {"key": "Type", "value": "float"},
        {"key": "Notes", "value": "CO2 Reading 0.00-2000.0 ppm"}
    ],
    [
        {"key": "Point_Name", "value": "SampleWritableFloat2"},
        {"key": "Volttron_Point_Name", "value": "SampleWritableFloat2"},
        {"key": "Units", "value": "PPM"},
        {"key": "Units_Details", "value": "1000.00 (default)"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": 10},
        {"key": "Type", "value": "float"},
        {"key": "Notes", "value": "Setpoint to enable demand control ventilation"}
    ],
    [
        {"key": "Point_Name", "value": "SampleLong2"},
        {"key": "Volttron_Point_Name", "value": "SampleLong2"},
        {"key": "Units", "value": "Enumeration"},
        {"key": "Units_Details", "value": "1 through 13"},
        {"key": "Writable", "value": false},
        {"key": "Starting_Value", "value": 50},
        {"key": "Type", "value": "int"},
        {"key": "Notes", "value": "Status indicator of service switch"}
    ],
    [
        {"key": "Point_Name", "value": "SampleWritableShort2"},
        {"key": "Volttron_Point_Name", "value": "SampleWritableShort2"},
        {"key": "Units", "value": "%"},
        {"key": "Units_Details", "value": "0.00 to 100.00 (20 default)"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": 20},
        {"key": "Type", "value": "int"},
        {"key": "Notes", "value": "Minimum damper position during the standard mode"}
    ],
    [
        {"key": "Point_Name", "value": "SampleBool2"},
        {"key": "Volttron_Point_Name", "value": "SampleBool2"},
        {"key": "Units", "value": "On / Off"},
        {"key": "Units_Details", "value": "on/off"},
        {"key": "Writable", "value": false},
        {"key": "Starting_Value", "value": true},
        {"key": "Type", "value": "boolean"},
        {"key": "Notes", "value": "Status indidcator of cooling stage 1"}
    ],
    [
        {"key": "Point_Name", "value": "SampleWritableBool2"},
        {"key": "Volttron_Point_Name", "value": "SampleWritableBool2"},
        {"key": "Units", "value": "On / Off"},
        {"key": "Units_Details", "value": "on/off"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": true},
        {"key": "Type", "value": "boolean"},
        {"key": "Notes", "value": "Status indicator"}
    ],
    [
        {"key": "Point_Name", "value": "OutsideAirTemperature3"},
        {"key": "Volttron_Point_Name", "value": "OutsideAirTemperature3"},
        {"key": "Units", "value": "F"},
        {"key": "Units_Details", "value": "-100 to 300"},
        {"key": "Writable", "value": false},
        {"key": "Starting_Value", "value": 50},
        {"key": "Type", "value": "float"},
        {"key": "Notes", "value": "CO2 Reading 0.00-2000.0 ppm"}
    ],
    [
        {"key": "Point_Name", "value": "SampleWritableFloat3"},
        {"key": "Volttron_Point_Name", "value": "SampleWritableFloat3"},
        {"key": "Units", "value": "PPM"},
        {"key": "Units_Details", "value": "1000.00 (default)"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": 10},
        {"key": "Type", "value": "float"},
        {"key": "Notes", "value": "Setpoint to enable demand control ventilation"}
    ],
    [
        {"key": "Point_Name", "value": "SampleLong3"},
        {"key": "Volttron_Point_Name", "value": "SampleLong3"},
        {"key": "Units", "value": "Enumeration"},
        {"key": "Units_Details", "value": "1 through 13"},
        {"key": "Writable", "value": false},
        {"key": "Starting_Value", "value": 50},
        {"key": "Type", "value": "int"},
        {"key": "Notes", "value": "Status indicator of service switch"}
    ],
    [
        {"key": "Point_Name", "value": "SampleWritableShort3"},
        {"key": "Volttron_Point_Name", "value": "SampleWritableShort3"},
        {"key": "Units", "value": "%"},
        {"key": "Units_Details", "value": "0.00 to 100.00 (20 default)"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": 20},
        {"key": "Type", "value": "int"},
        {"key": "Notes", "value": "Minimum damper position during the standard mode"}
    ],
    [
        {"key": "Point_Name", "value": "SampleBool3"},
        {"key": "Volttron_Point_Name", "value": "SampleBool3"},
        {"key": "Units", "value": "On / Off"},
        {"key": "Units_Details", "value": "on/off"},
        {"key": "Writable", "value": false},
        {"key": "Starting_Value", "value": true},
        {"key": "Type", "value": "boolean"},
        {"key": "Notes", "value": "Status indidcator of cooling stage 1"}
    ],
    [
        {"key": "Point_Name", "value": "SampleWritableBool3"},
        {"key": "Volttron_Point_Name", "value": "SampleWritableBool3"},
        {"key": "Units", "value": "On / Off"},
        {"key": "Units_Details", "value": "on/off"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": true},
        {"key": "Type", "value": "boolean"},
        {"key": "Notes", "value": "Status indicator"}
    ]
];

devicesStore.getState = function () {
    return { action: _action, view: _view, device: _device };
};

devicesStore.getFilteredRegistryValues = function (device, filterStr) {

    return _registryValues.filter(function (item) {
        var pointName = item.find(function (pair) {
            return pair.key === "Point_Name";
        })

        return (pointName ? (pointName.value.trim().toUpperCase().indexOf(filterStr.trim().toUpperCase()) > -1) : false);
    });
}

devicesStore.getRegistryValues = function (device) {
    return _registryValues.slice();
    
};

devicesStore.getDevices = function (platform) {
    return [
            [ 
                { key: "address", label: "Address", value: "Address 192.168.1.42" }, 
                { key: "deviceId", label: "Device ID", value: "548" }, 
                { key: "description", label: "Description", value: "Temperature sensor" }, 
                { key: "vendorId", label: "Vendor ID", value: "18" }, 
                { key: "vendor", label: "Vendor", value: "Siemens" },
                { key: "type", label: "Type", value: "BACnet" }
            ],
            [ 
                { key: "address", label: "Address", value: "RemoteStation 1002:11" }, 
                { key: "deviceId", label: "Device ID", value: "33" }, 
                { key: "description", label: "Description", value: "Actuator 3-pt for zone control" }, 
                { key: "vendorId", label: "Vendor ID", value: "12" }, 
                { key: "vendor", label: "Vendor", value: "Alerton" },
                { key: "type", label: "Type", value: "BACnet" }
            ]
        ];
}

devicesStore.dispatchToken = dispatcher.register(function (action) {
    dispatcher.waitFor([authorizationStore.dispatchToken]);

    switch (action.type) {
        case ACTION_TYPES.SCAN_FOR_DEVICES:
            _action = "start_scan";
            _view = "Detect Devices";
            _device = null;
            devicesStore.emitChange();
            break;
        case ACTION_TYPES.CANCEL_SCANNING:
            _action = "get_scan_settings";
            _view = "Detect Devices";
            _device = null;
            devicesStore.emitChange();
            break;
        case ACTION_TYPES.LIST_DETECTED_DEVICES:
            _action = "show_new_devices";
            _view = "Configure Devices";
            _device = null;
            devicesStore.emitChange();
            break;
        case ACTION_TYPES.CONFIGURE_DEVICE:
        case ACTION_TYPES.CANCEL_REGISTRY:
            _action = "configure_device";
            _view = "Configure Device";
            _device = action.device;
            devicesStore.emitChange();
            break;
        case ACTION_TYPES.CONFIGURE_REGISTRY:
            _action = "configure_registry";
            _view = "Registry Configuration";
            _device = action.device;
            _data = action.data;
            devicesStore.emitChange();
            break;
        case ACTION_TYPES.CANCEL_REGISTRY:
            _action = "configure_registry";
            _view = "Registry Configuration";
            _device = action.device;
            devicesStore.emitChange();
            break;
    }
});

module.exports = devicesStore;
