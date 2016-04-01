'use strict';

var React = require('react');
var Router = require('react-router');

var devicesActionCreators = require('../action-creators/devices-action-creators');
var devicesStore = require('../stores/devices-store');

var DevicesFound = React.createClass({
    getInitialState: function () {
        return getStateFromStores();
    },
    componentDidMount: function () {
        // platformsStore.addChangeListener(this._onStoresChange);
    },
    componentWillUnmount: function () {
        // platformsStore.removeChangeListener(this._onStoresChange);
    },
    _onStoresChange: function () {
        this.setState(getStateFromStores());
    },
    _configureDevice: function (device) {
        devicesActionCreators.configureDevice(device);
    },
    render: function () {        
        
        var devices = 
            this.state.devices.map(function (device) {

                var tds = device.map(function (d) {
                                return (<td>{ d.value }</td>)
                            });
                return (
                    <tr>
                        { tds }

                        <td>
                            <button onClick={this._configureDevice.bind(this, device)}>Configure</button>
                        </td>
                    </tr>
                );

            }, this); 

        var ths = this.state.devices[0].map(function (d) {
                        return (<th>{d.label}</th>); 
                    });    

        return (
            <div>
                <table>
                    <tbody>
                        <tr>
                            { ths }
                            <th></th>
                        </tr>
                        {devices}
                    </tbody>
                </table>
            </div>
        );
    },
});

function getStateFromStores() {
    return {
        devices: [
            [ 
                { key: "address", label: "Address", value: "Address 192.168.1.42" }, 
                { key: "deviceId", label: "Device ID", value: "548" }, 
                { key: "description", label: "Description", value: "Temperature sensor" }, 
                { key: "vendorId", label: "Vendor ID", value: "18" }, 
                { key: "vendor", label: "Vendor", value: "Siemens" }
            ],
            [ 
                { key: "address", label: "Address", value: "RemoteStation 1002:11" }, 
                { key: "deviceId", label: "Device ID", value: "33" }, 
                { key: "description", label: "Description", value: "Actuator 3-pt for zone control" }, 
                { key: "vendorId", label: "Vendor ID", value: "12" }, 
                { key: "vendor", label: "Vendor", value: "Alerton" }
            ]
        ]
    };
}

module.exports = DevicesFound;
