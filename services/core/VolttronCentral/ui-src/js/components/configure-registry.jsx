'use strict';

var React = require('react');
var Router = require('react-router');

var devicesActionCreators = require('../action-creators/devices-action-creators');
var devicesStore = require('../stores/devices-store');
var FilterPointsButton = require('./control_buttons/filter-points-button');
var ControlButton = require('./control-button');
var EditColumnButton = require('./control_buttons/edit-columns-button');

var ConfirmForm = require('./confirm-form');
var modalActionCreators = require('../action-creators/modal-action-creators');

var ConfigureRegistry = React.createClass({    
    getInitialState: function () {
        var state = {};

        state.registryValues = getPointsFromStore(this.props.device);
        state.registryHeader = [];
        state.columnNames = [];
        state.pointNames = [];

        if (state.registryValues.length > 0)
        {
            state.registryHeader = getRegistryHeader(state.registryValues[0]);
            state.columnNames = state.registryValues[0].map(function (columns) {
                return columns.key;
            });

            state.pointNames = state.registryValues.map(function (points) {
                return points[0].value;
            });
        }

        state.pointsToDelete = [];
        state.allSelected = false;

        state.selectedCells = [];
        state.selectedCellRow = null;
        state.selectedColumn = null;

        this.scrollToBottom = false;
        this.resizeTable = false;

        return state;
    },
    componentDidMount: function () {
        // platformsStore.addChangeListener(this._onStoresChange);

        this.containerDiv = document.getElementsByClassName("fixed-table-container-inner")[0];
        this.fixedHeader = document.getElementsByClassName("header-background")[0];
        this.fixedInner = document.getElementsByClassName("fixed-table-container-inner")[0];
        this.registryTable = document.getElementsByClassName("registryConfigTable")[0];
    },
    componentWillUnmount: function () {
        // platformsStore.removeChangeListener(this._onStoresChange);
    },
    componentDidUpdate: function () {

        if (this.scrollToBottom)
        {
            this.containerDiv.scrollTop = this.containerDiv.scrollHeight;

            this.scrollToBottom = false;
        }

        if (this.resizeTable)
        {
            this.fixedHeader.style.width = this.registryTable.clientWidth + "px";
            this.fixedInner.style.width = this.registryTable.clientWidth + "px";

            this.resizeTable = false;
        }

        if (this.state.selectedCellRow)
        {
            var focusedCell = document.getElementsByClassName("focusedCell")[0];
            if (focusedCell)
            {
                focusedCell.focus();
            }
        }

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

        var pointNames = this.state.pointNames;

        pointNames.push("");

        this.setState({ pointNames: pointNames });

        var registryValues = this.state.registryValues;

        var pointValues = [];

        this.state.columnNames.map(function (column) {
            pointValues.push({ "key" : column, "value": "" });
        });

        registryValues.push(pointValues);

        this.setState({ registryValues: registryValues });

        this.scrollToBottom = true;
    },
    _onRemovePoints: function () {

        var promptText, confirmText, confirmAction, cancelText;

        if (this.state.pointsToDelete.length > 0)
        {
            promptText = "Are you sure you want to delete these points? " + this.state.pointsToDelete.join(", ");
            confirmText = "Delete";
            confirmAction = this._removePoints.bind(this, this.state.pointsToDelete);
        }  
        else
        {
            promptText = "Select points to delete.";
            cancelText = "OK";
        }
        
        modalActionCreators.openModal(
            <ConfirmForm
                promptTitle="Remove Points"
                promptText={ promptText }
                confirmText={ confirmText }
                onConfirm={ confirmAction }
                cancelText={ cancelText }
            ></ConfirmForm>
        );
    },
    _removePoints: function (pointsToDelete) {
        console.log("removing " + pointsToDelete.join(", "));

        var registryValues = this.state.registryValues.slice();
        var pointsList = this.state.pointsToDelete.slice();
        var namesList = this.state.pointNames.slice();

        pointsToDelete.forEach(function (pointToDelete) {

            var index = -1;
            var pointValue = "";

            registryValues.some(function (vals, i) {
                var pointMatched = (vals[0].value ===  pointToDelete);

                if (pointMatched)
                {
                    index = i;
                    pointValue = vals[0].value;
                }

                return pointMatched;
            })

            if (index > -1)
            {
                registryValues.splice(index, 1);
                
                index = pointsList.indexOf(pointValue);

                if (index > -1)
                {
                    pointsList.splice(index, 1);
                }

                index = namesList.indexOf(pointValue);

                if (index > -1)
                {
                    namesList.splice(index, 1);
                }
            }
        });

        this.setState({ registryValues: registryValues });
        this.setState({ pointsToDelete: pointsList });
        this.setState({ pointNames: namesList });

        modalActionCreators.closeModal();
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
            pointsToDelete.splice(index, 1);
        }

        this.setState({ pointsToDelete: pointsToDelete });

    },
    _selectAll: function () {
        var allSelected = !this.state.allSelected;

        this.setState({ allSelected: allSelected });

        this.setState({ pointsToDelete : (allSelected ? this.state.pointNames.slice() : []) }); 
    },
    _onAddColumn: function (columnFrom) {

        console.log(columnFrom);

        var registryHeader = this.state.registryHeader.slice();
        var registryValues = this.state.registryValues.slice();
        var columnNames = this.state.columnNames.slice();

        var index = registryHeader.indexOf(columnFrom);

        if (index > -1)
        {
            registryHeader.splice(index + 1, 0, registryHeader[index] + "2");

            this.setState({ registryHeader: registryHeader });

            columnNames.splice(index + 1, 0, columnFrom + "2");

            this.setState({ columnNames: columnNames });

            var newRegistryValues = registryValues.map(function (values) {

                values.splice(index + 1, 0, { "key": columnFrom.replace(/ /g, "_") + "2", "value": "" });
                var newValues = values;

                return newValues;
            });

            this.resizeTable = true;

            this.setState({ registryValues: newRegistryValues });
        }
    },
    _onRemoveColumn: function (column) {

        var promptText = ("Are you sure you want to delete the column, " + column + "?");
        
        modalActionCreators.openModal(
            <ConfirmForm
                promptTitle="Remove Column"
                promptText={ promptText }
                confirmText="Delete"
                onConfirm={this._removeColumn.bind(this, column)}
            ></ConfirmForm>
        );
        
    },
    _removeColumn: function (columnToDelete) {
        console.log("deleting " + columnToDelete);

        var registryHeader = this.state.registryHeader.slice();
        var registryValues = this.state.registryValues.slice();
        var columnNames = this.state.columnNames.slice();

        var index = columnNames.indexOf(columnToDelete.replace(/ /g, "_"));

        if (index > -1)
        {
            columnNames.splice(index, 1);
        }

        index = registryHeader.indexOf(columnToDelete);

        if (index > -1)
        {
            registryHeader.splice(index, 1);

            registryValues.forEach(function (values) {

                var itemFound = values.find(function (item, i) {

                    var matched = (item.key === columnToDelete.replace(/ /g, "_"));

                    if (matched)
                    {
                        index = i;
                    }

                    return matched;
                });

                if (itemFound)
                {
                    values.splice(index, 1);
                }
            });

            this.resizeTable = true;

            this.setState({ columnNames: columnNames });
            this.setState({ registryValues: registryValues });
            this.setState({ registryHeader: registryHeader });

            modalActionCreators.closeModal();
        }
    },
    _updateCell: function (e) {

        var currentTarget = e.currentTarget;
        var newRegistryValues = this.state.registryValues.slice();

        var rowIndex = currentTarget.dataset.rowIndex;
        var columnIndex = currentTarget.dataset.columnIndex;

        newRegistryValues[rowIndex][columnIndex].value = currentTarget.value;

        this.setState({ registryValues: newRegistryValues });
    },
    _onFindNext: function (findValue, column) {

        var registryValues = this.state.registryValues.slice();
        
        if (this.state.selectedCells.length === 0)
        {
            var selectedCells = [];

            this.setState({ registryValues: registryValues.map(function (values, row) {

                    //searching i-th column in each row, and if the cell contains the target value, select it
                    values[column].selected = (values[column].value.toUpperCase().indexOf(findValue.toUpperCase()) > -1);

                    if (values[column].selected)
                    {
                        selectedCells.push(row);
                    }

                    return values;
                })
            });

            if (selectedCells.length > 0)
            {
                this.setState({ selectedCells: selectedCells });
                this.setState({ selectedColumn: column });

                //set focus to the first selected cell
                this.setState({ selectedCellRow: selectedCells[0]})
            }
        }
        else
        {
            //we've already found the selected cells, so we need to advance focus to the next one
            if (this.state.selectedCells.length > 1)
            {
                var selectedCellRow;

                //this is the row with current focus
                var rowIndex = this.state.selectedCells.indexOf(this.state.selectedCellRow);

                //either set focus to the next one in the selected cells list
                if (rowIndex < this.state.selectedCells.length - 1)
                {
                    selectedCellRow = this.state.selectedCells[++rowIndex];
                }
                else //or if we're at the end of the list, go back to the first one
                {
                    selectedCellRow = this.state.selectedCells[0];
                }

                this.setState({ selectedCellRow: selectedCellRow})
            }
        }
    },
    _onReplaceNext: function () {

    },
    _onReplaceAll: function () {

    },
    _onClearFind: function (index) {
        var registryValues = this.state.registryValues.slice();

        this.setState({ registryValues: registryValues.map(function (values) {

                values[index].selected = false;

                return values;
            })
        });
    },
    render: function () {        
        
        var filterButton = <FilterPointsButton 
                                name="filterRegistryPoints" 
                                tooltipMsg="Filter Points"
                                onfilter={this._onFilterBoxChange} 
                                onclear={this._onClearFilter}/>

        var addPointTooltip = {
            content: "Add New Point"
        }

        var addPointButton = <ControlButton 
                                name="addRegistryPoint" 
                                tooltip={addPointTooltip}
                                fontAwesomeIcon="plus"
                                clickAction={this._onAddPoint}/>


        var removePointTooltip = {
            content: "Remove Points"
        }

        var removePointsButton = <ControlButton
                                name="removeRegistryPoints" 
                                fontAwesomeIcon="minus"
                                tooltip={removePointTooltip}
                                clickAction={this._onRemovePoints}/>        
        
        var registryRows, registryHeader;
        
        registryRows = this.state.registryValues.map(function (attributesList, rowIndex) {

            var registryCells = attributesList.map(function (item, columnIndex) {

                var selectedStyle = (item.selected ? {backgroundColor: "#CCCCCC"} : {});
                var focusedCell = (this.state.selectedColumn === columnIndex && this.state.selectedCellRow === rowIndex ? "focusedCell" : "");

                var itemCell = (columnIndex === 0 && item.value !== "" ? 
                                    <td>{ item.value }</td> : 
                                        <td><input 
                                                type="text"
                                                className={focusedCell}
                                                style={selectedStyle}
                                                data-row-index={rowIndex}
                                                data-column-index={columnIndex}
                                                onChange={this._updateCell} 
                                                value={ this.state.registryValues[rowIndex][columnIndex].value }/>
                                        </td>);

                return itemCell;
            }, this);

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

        var wideCell = {
            width: "100%"
        }

        registryHeader = this.state.registryHeader.map(function (item, index) {

            var addColumnTooltip = {
                content: "Add New Column"
            }

            var addColumnButton = <ControlButton 
                                name="addPointColumn" 
                                tooltip={addColumnTooltip}
                                fontAwesomeIcon="plus"
                                clickAction={this._onAddColumn.bind(this, item)}/>


            var removeColumnTooltip = {
                content: "Remove Column"
            }

            var removeColumnButton = <ControlButton 
                                name="removePointColumn" 
                                fontAwesomeIcon="minus"
                                tooltip={removeColumnTooltip}
                                clickAction={this._onRemoveColumn.bind(this, item)}/> 

            var editColumnButton = <EditColumnButton 
                                name={"searchPointColumns" + index}
                                column={index} 
                                tooltipMsg="Edit Column"
                                findnext={this._onFindNext}
                                replacenext={this._onReplaceNext}
                                replaceall={this._onReplaceAll}
                                onfilter={this._onFilterBoxChange} 
                                onclear={this._onClearFind}/>

            var headerCell = (index === 0 ?
                                ( <th>
                                    <div className="th-inner">
                                        { item } { filterButton } { addPointButton } { removePointsButton }
                                    </div>
                                </th>) :
                                ( <th>
                                    <div className="th-inner" style={wideCell}>
                                        { item }
                                        { editColumnButton }
                                        { addColumnButton } 
                                        { removeColumnButton }
                                    </div>
                                </th> ) )

            return headerCell;
        }, this);        

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
                                            <input type="checkbox"
                                                onChange={this._selectAll}
                                                checked={this.state.allSelected}/>
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
