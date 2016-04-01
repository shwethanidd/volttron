'use strict';

var React = require('react');
var Router = require('react-router');

var platformsStore = require('../stores/platforms-store');
var devicesActionCreators = require('../action-creators/devices-action-creators');

var DetectDevices = React.createClass({
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
    _doScan: function () {
        devicesActionCreators.scanForDevices(this.props.platform);
    },
    _cancelScan: function () {
        devicesActionCreators.cancelScan(this.props.platform);
    },
    _continue: function () {
        devicesActionCreators.listDetectedDevices(this.props.platform);
    },
    render: function () {        
        
        var devices;

        switch (this.props.action)
        {
            case "start_scan":

                devices = (
                    <div>
                        <progress/>
                        <div>
                            <button onClick={this._cancelScan}>Cancel</button>
                        </div>
                        <div>
                            <button onClick={this._continue}>Continue</button>
                        </div>
                    </div>
                )

                break;
            case "get_scan_settings":

                devices = (
                    <div>
                        <div>
                            <table>
                                <tbody>
                                    <tr>
                                        <td>Network Interface</td>
                                        <td>
                                            <select>
                                                <option>UDP/IP</option>
                                                <option>IPC</option>
                                                <option>TCP</option>
                                            </select>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>UDP Port</td>
                                        <td>
                                            <input type="number"></input>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>
                                            <input type="radio" name="scan_method">Device ID Range</input>
                                        </td>
                                        <td>
                                            <input type="number"></input>&nbsp;<input type="number"></input>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>
                                            <input type="radio" name="scan_method">Address</input>
                                        </td>
                                        <td>
                                            <input type="text"></input>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <div>
                            <button onClick={this._doScan}>Scan</button>
                        </div>
                        
                    </div>
                )


                break;
        }

        return (
            <div>
                {devices}  
            </div>
        );
    },
});

function getStateFromStores() {
    return {
        platform: { name: "PNNL", uuid: "99090"}
    };
}

module.exports = DetectDevices;
