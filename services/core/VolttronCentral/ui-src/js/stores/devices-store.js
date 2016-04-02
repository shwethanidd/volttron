'use strict';

var ACTION_TYPES = require('../constants/action-types');
var authorizationStore = require('../stores/authorization-store');
var dispatcher = require('../dispatcher');
var Store = require('../lib/store');

var devicesStore = new Store();

var _action = "get_scan_settings";
var _view = "Detect Devices";
var _device = null;

devicesStore.getState = function () {
    return { action: _action, view: _view, device: _device };
};

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
            _action = "configure_device";
            _view = "Configure Device";
            _device = action.device;
            devicesStore.emitChange();
            break;
        case ACTION_TYPES.CONFIGURE_REGISTRY:
            _action = "configure_registry";
            _view = "Registry Configuration";
            _device = action.device;
            devicesStore.emitChange();
            break;
    }
});

module.exports = devicesStore;
