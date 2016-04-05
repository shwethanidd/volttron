'use strict';

var React = require('react');
var Router = require('react-router');

var devicesActionCreators = require('../action-creators/devices-action-creators');
var devicesStore = require('../stores/devices-store');

var ConfigureRegistry = React.createClass({
    getInitialState: function () {
        return getStateFromStores(this.props.device);
    },
    componentDidMount: function () {
        // platformsStore.addChangeListener(this._onStoresChange);
    },
    componentWillUnmount: function () {
        // platformsStore.removeChangeListener(this._onStoresChange);
    },
    _onStoresChange: function () {
        this.setState(getStateFromStores(this.props.device));
    },
    _onFilterBoxChange: function (e) {
        this.setState({ filterValue: e.target.value });
    },
    render: function () {        
        
        var filterBoxContainer = {};

        var registryRows, registryHeader;

        if (this.state.registryValues.length > 0)
        {
            registryRows = this.state.registryValues.map(function (attributesList) {

                var registryCells = attributesList.map(function (item, index) {

                    var itemCell = (index === 0 ? 
                                        <td>{ item.value }</td> : 
                                            <td><input type="text" value={ item.value }/></td>);

                    return itemCell;
                });

                return ( 
                    <tr>
                        <td>
                            <input type="checkbox"/>
                        </td>
                        { registryCells }
                    </tr>
                )
            });

            registryHeader = this.state.registryValues[0].map(function (item) {

                return ( <th>
                            <div className="th-inner">
                                { item.key.replace(/_/g, " ") }
                            </div>
                        </th> );
            });
        }
        else
        {
            registryHeader = (
                <td>Nothing to report at this time</td>
            )
        }

        var wideDiv = {
            width: "100%",
            textAlign: "center"
        }

        var tableDiv = {
            width: "100%",
            height: "80vh",
            overflow: "auto"
        }
            
        return (
            <div>
                <div className="filter_box" style={filterBoxContainer}>
                    <span className="fa fa-search"></span>
                    <input
                        type="search"
                        onChange={this._onFilterBoxChange}
                        value={ this.state.filterValue }
                    />
                </div> 
                <div className="fixed-table-container"> 
                    <div className="header-background"></div>      
                    <div className="fixed-table-container-inner">    
                        <table className="registryConfigTable">
                            <thead>
                                <tr>
                                    <th>
                                        <div className="th-inner">
                                            <input type="checkbox"/>
                                        </div>
                                    </th>
                                    { registryHeader }
                                </tr>
                            </thead>
                            <tbody>                            
                                { registryRows }
                            </tbody>
                        </table>
                    </div>
                </div>
                <div style={wideDiv}>
                    <button>Save</button>
                </div>
            </div>
        );
    },
});

function getStateFromStores(device) {
    return {
        filterValue: "",
        registryValues: devicesStore.getRegistryValues(device)
    };
}

module.exports = ConfigureRegistry;
