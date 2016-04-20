'use strict';

var React = require('react');
var Router = require('react-router');
// var CsvParse = require('../lib/rpc');
var CsvParse = require('babyparse');

var devicesActionCreators = require('../action-creators/devices-action-creators');
var devicesStore = require('../stores/devices-store');

var ConfigureDevice = React.createClass({
    getInitialState: function () {
        return getStateFromStores(this.props.device);
    },
    componentDidMount: function () {
        devicesStore.addChangeListener(this._onStoresChange);
    },
    componentWillUnmount: function () {
        devicesStore.removeChangeListener(this._onStoresChange);
    },
    _onStoresChange: function () {
        this.setState(getStateFromStores(this.props.device));
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

        var csvFile = evt.target.files[0];

        if (!csvFile)
        {
            return;
        }

        var reader = new FileReader();

        var fileName = evt.target.value;

        reader.onload = function (e) {

            var contents = e.target.result;

            var results = parseCsvFile(contents);

            if (results.error)
            {
                var errorMsg = "The file is not a valid CSV document: " + err;

                modalActionCreators.openModal(
                    <ConfirmForm
                        promptTitle="Error Reading File"
                        promptText={ errorMsg }
                        cancelText="OK"
                    ></ConfirmForm>
                );
            }
            else if (results.data)
            {

                devicesActionCreators.loadRegistryCsv(this.props.device, results.data);

                // this.setState({csv_data: results.data});
                // // this.setState({registry_file: fileName});
                this.setState({registry_config: fileName});
            }
        }.bind(this)

        reader.readAsText(csvFile);

        // // var contents = reader.result;

        // if (contents)
        // {
        //     var results = parseCsvFile(contents);

        //     if (results.data)
        //     {
        //         this.setState({csv_data: results.data});
        //         this.setState({registry_file: evt.target.value});
        //         this.setState({registry_config: evt.target.value});
        //     }
        // }
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

function getStateFromStores(device) {
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

function parseCsvFile(contents) {

    var results = CsvParse.parse(contents, {
        error: function (err) {
            var errorMsg = "The file is not a valid CSV document: " + err;

            modalActionCreators.openModal(
                <ConfirmForm
                    promptTitle="Error Reading File"
                    promptText={ errorMsg }
                    cancelText="OK"
                ></ConfirmForm>
            );
        }
    });

    return results;
}



module.exports = ConfigureDevice;
