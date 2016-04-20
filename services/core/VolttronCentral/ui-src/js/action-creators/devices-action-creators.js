'use strict';

var ACTION_TYPES = require('../constants/action-types');
var authorizationStore = require('../stores/authorization-store');
var dispatcher = require('../dispatcher');
var rpc = require('../lib/rpc');

var devicesActionCreators = {
    scanForDevices: function (platform) {
        dispatcher.dispatch({
            type: ACTION_TYPES.SCAN_FOR_DEVICES,
            platform: platform
        });
    },
    cancelScan: function (platform) {
        dispatcher.dispatch({
            type: ACTION_TYPES.CANCEL_SCANNING,
            platform: platform
        });
    },
    listDetectedDevices: function (platform) {
        dispatcher.dispatch({
            type: ACTION_TYPES.LIST_DETECTED_DEVICES,
            platform: platform
        });
    },
    configureDevice: function (device) {
        dispatcher.dispatch({
            type: ACTION_TYPES.CONFIGURE_DEVICE,
            device: device
        });
    },
    configureRegistry: function (device) {
        dispatcher.dispatch({
            type: ACTION_TYPES.CONFIGURE_REGISTRY,
            device: device
        });
    },
    cancelRegistry: function (device) {
        dispatcher.dispatch({
            type: ACTION_TYPES.CANCEL_REGISTRY,
            device: device
        });
    },
    loadRegistryCsv: function (device, csvData) {
        dispatcher.dispatch({
            type: ACTION_TYPES.CONFIGURE_REGISTRY,
            device: device,
            data: csvData
        });
    },
};



module.exports = devicesActionCreators;
