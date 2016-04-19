'use strict';

var React = require('react');
var Router = require('react-router');

var devicesActionCreators = require('../action-creators/devices-action-creators');
var devicesStore = require('../stores/devices-store');

var ConfigureDevice = React.createClass({
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
    _updateSetting: function (evt) {
        var newVal = evt.target.value;
        var key = evt.currentTarget.dataset.setting;

        var tmpState = JSON.parse(JSON.stringify(this.state));

        var newSettings = tmpState.settings.map(function (item) {
            if (item.key === key)
            {
                item.value = newVal;                
            }

            return item;
        });

        this.setState({settings: newSettings});
    },
    _updateRegistryPath: function (evt) {
        this.setState({registry_config: evt.target.value});
    },
    _uploadRegistryFile: function (evt) {
        this.setState({registry_file: evt.target.value});
        this.setState({registry_config: evt.target.value});
    },
    _generateRegistryFile: function (device) {
        devicesActionCreators.configureRegistry(device);
    },
    render: function () {        
        
        var attributeRows = 
            this.props.device.map(function (device) {

                return (
                    <tr>
                        <td>{device.label}</td>
                        <td className="plain">{device.value}</td>
                    </tr>
                );

            });

        var tableStyle = {
            backgroundColor: "#E7E7E7"
        }

        var uneditableAttributes = 
            <table style={tableStyle}>
                <tbody>

                    { attributeRows }

                    <tr>
                        <td>Proxy Address</td>
                        <td className="plain">10.0.2.15</td>
                    </tr>
                    <tr>
                        <td>Network Interface</td>
                        <td className="plain">UDP/IP</td>
                    </tr>
                    <tr>
                        <td>Campus</td>
                        <td className="plain">PNNL</td>
                    </tr>

                </tbody>
            </table>;

        var buttonStyle = {
            height: "24px",
            lineHeight: "18px"
        }

        var firstStyle = {
            width: "30%",
            textAlign: "right"
        }

        var secondStyle = {
            width: "50%"
        }

        var buttonColumns = {
            width: "8%"
        }

        var settingsRows = 
            this.state.settings.map(function (setting) {

                var stateSetting = this.state.settings.find(function (s) {
                    return s.key === setting.key;
                })

                return (
                    <tr>
                        <td style={firstStyle}>{setting.label}</td>
                        <td style={secondStyle}
                            className="plain">
                            <input
                                className="form__control form__control--block"
                                type="text"
                                data-setting={setting.key}
                                onChange={this._updateSetting}
                                value={stateSetting.value}
                            />
                        </td>
                    </tr>
                );
            }, this);

        var registryConfigRow = 
            <tr>
                <td style={firstStyle}>Registry Configuration File</td>
                <td 
                    style={secondStyle}
                    className="plain">
                    <input
                        className="form__control form__control--block"
                        type="text"
                        onChange={this._updateRegistryPath}
                        value={this.state.registry_config}
                    />
                </td>
                <td 
                    style={buttonColumns}
                    className="plain">
                    <div className="buttonWrapper">
                        <div>Upload File</div>
                        <input 
                            className="uploadButton" 
                            type="file"
                            onChange={this._uploadRegistryFile}
                            value={this.state.registry_file}/>
                    </div>
                </td>
                <td 
                    style={buttonColumns}
                    className="plain">
                    <button 
                        style={buttonStyle} onClick={this._generateRegistryFile.bind(this, this.props.device)}>Generate</button>
                </td>
            </tr>

        var editableAttributes = 
            <table>
                <tbody>
                    { settingsRows }
                    { registryConfigRow }
                </tbody>
            </table>

        return (
            <div className="configDeviceContainer">
                <div className="uneditableAttributes">
                    { uneditableAttributes }
                </div>
                <div className="configDeviceBox">                    
                    { editableAttributes }
                </div>
            </div>
        );
    },
});

function getStateFromStores() {
    return {
        settings: [
            { key: "unit", value: "", label: "Unit" },
            { key: "building", value: "", label: "Building" },
            { key: "path", value: "", label: "Path" },
            { key: "interval", value: "", label: "Interval" },
            { key: "timezone", value: "", label: "Timezone" },
            { key: "heartbeat_point", value: "", label: "Heartbeat Point" },
            { key: "minimum_priority", value: "", label: "Minimum Priority" },
            { key: "max_objs_per_read", value: "", label: "Maximum Objects per Read" }
        ],
        registry_config: "",
        registry_file: ""
    };
}

module.exports = ConfigureDevice;
