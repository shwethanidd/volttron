'use strict';

var React = require('react');
var Router = require('react-router');

var devicesActionCreators = require('../action-creators/devices-action-creators');
var devicesStore = require('../stores/devices-store');
var FilterPointsButton = require('./control_buttons/filter-points-button');
var AddPointButton = require('./control_buttons/add-button');
var RemovePointsButton = require('./control_buttons/remove-button');

var ConfirmForm = require('./confirm-form');
var modalActionCreators = require('../action-creators/modal-action-creators');

var ConfigureRegistry = React.createClass({
    getInitialState: function () {
        var state = {};

        state.registryValues = getPointsFromStore(this.props.device);
        state.registryHeader = [];

        if (state.registryValues.length > 0)
        {
            state.registryHeader = getRegistryHeader(state.registryValues[0]);
        }

        state.pointsToDelete = [];

        return state;
    },
    componentDidMount: function () {
        // platformsStore.addChangeListener(this._onStoresChange);
    },
    componentWillUnmount: function () {
        // platformsStore.removeChangeListener(this._onStoresChange);
    },
    _onStoresChange: function () {
        this.setState({registryValues: getPointsFromStore(this.props.device) });
    },
    _onFilterBoxChange: function (filterValue) {
        this.setState({ registryValues: getFilteredPoints(this.props.device, filterValue) });
    },
    _onClearFilter: function () {
        this.setState({registryValues: getPointsFromStore(this.props.device) }); //TODO: when filtering, set nonmatches to hidden so they're
                                                                                //still there and we don't lose information in inputs
                                                                                //then to clear filter, set all to not hidden
    },
    _onAddPoint: function () {

    },
    _onRemovePoints: function () {

        var promptText = (this.state.pointsToDelete.length > 0 ? 
                            "Are you sure you want to delete these points? " + this.state.pointsToDelete.join(", ") :
                                "Select points to delete.");
        
        modalActionCreators.openModal(
            <ConfirmForm
                promptTitle="Remove Points"
                promptText={ promptText }
                confirmText="Delete"
                onConfirm={this._removePoints}
            ></ConfirmForm>
        );
    },
    _removePoitns: function () {

    },
    _selectForDelete: function (attributesList) {
        
        var pointsToDelete = this.state.pointsToDelete;

        var index = pointsToDelete.indexOf(attributesList[0].value);

        if (index < 0)
        {
            pointsToDelete.push(attributesList[0].value);
        }
        else
        {
            pointsToDelete = pointsToDelete.splice(index, 1);
        }

        this.setState({ pointsToDelete: pointsToDelete });

    },
    render: function () {        
        
        var filterButton = <FilterPointsButton 
                                name="filterRegistryPoints" 
                                onfilter={this._onFilterBoxChange} 
                                onclear={this._onClearFilter}/>

        var addButton = <AddPointButton 
                                name="addRegistryPoint" 
                                onadd={this._onAddPoint}/>

        var removeButton = <RemovePointsButton 
                                name="removeRegistryPoints" 
                                onremove={this._onRemovePoints}/>
        
        var registryRows, registryHeader;
        
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
                        <input type="checkbox"
                            onChange={this._selectForDelete.bind(this, attributesList)}
                            checked={this.state.pointsToDelete.indexOf(attributesList[0].value) > -1}>
                        </input>
                    </td>
                    { registryCells }
                </tr>
            )
        }, this);

        registryHeader = this.state.registryHeader.map(function (item, index) {

            var headerCell = (index === 0 ?
                                ( <th>
                                    <div className="th-inner">
                                        { item } { filterButton } { addButton } { removeButton }
                                    </div>
                                </th>) :
                                ( <th>
                                    <div className="th-inner">
                                        { item }
                                    </div>
                                </th> ) )

            return headerCell;
        });        

        var wideDiv = {
            width: "100%",
            textAlign: "center",
            paddingTop: "20px"
        }
            
        return (
            <div>                
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

function getFilteredPoints(device, filterStr) {
    return devicesStore.getFilteredRegistryValues(device, filterStr);
}

function getPointsFromStore(device) {
    return devicesStore.getRegistryValues(device);
}

function getRegistryHeader(registryItem) {
    return registryItem.map(function (item) {
            return item.key.replace(/_/g, " ");
        });
}

module.exports = ConfigureRegistry;
