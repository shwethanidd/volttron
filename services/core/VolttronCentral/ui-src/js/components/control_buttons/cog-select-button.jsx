'use strict';

var React = require('react');

var ControlButton = require('../control-button');
var EditColumnButton = require('./edit-columns-button');
// var controlButtonStore = require('../../stores/control-button-store');

var CogButton = React.createClass({
    getInitialState: function () {
        
        var state = {};

        state.selectedOption = "";

        return state;
    },
    componentDidMount: function () {
        // this.opSelector = document.getElementsByClassName("opSelector")[0];
        // this.opSelector.selectedIndex = -1;
    },
    componentDidUpdate: function () {
    },
    _onClose: function () {

    },
    _onCloneColumn: function () {
        this.props.onclone(this.props.column);
    },
    _onAddColumn: function () {
        this.props.onadd(this.props.item);
    },
    _onRemoveColumn: function () {
        this.props.onremove(this.props.item);
    },
    _updateSelect: function (evt) {

        var operation = evt.target.value;

        switch (operation)
        {
            case "edit":
                break;
            case "clone":
                this.props.onclone(this.props.column);
                break;
            case "add":
                this.props.onadd(this.props.item);
                break;
            case "remove":
                this.props.onremove(this.props.item);
                break;
        }
        this.setState({ selectedOption: evt.target.value });
    },
    render: function () {

        var cogBoxContainer = {
            position: "relative"
        };

        var clearTooltip = {
            content: "Clear Search",
            x: 50,
            y: 0
        }

        var cloneColumnTooltip = {
            content: "Duplicate Column",
            "x": 180,
            "y": 0
        }

        var cloneColumnButton = <ControlButton 
                            name="clonePointColumn" 
                            tooltip={cloneColumnTooltip}
                            fontAwesomeIcon="clone"
                            clickAction={this._onCloneColumn.bind(this, this.props.column)}/>

        var addColumnTooltip = {
            content: "Add New Column",
            "x": 180,
            "y": 0
        }

        var addColumnButton = <ControlButton 
                            name="addPointColumn" 
                            tooltip={addColumnTooltip}
                            fontAwesomeIcon="plus"
                            clickAction={this._onAddColumn.bind(this, this.props.item)}/>


        var removeColumnTooltip = {
            content: "Remove Column",
            "x": 200,
            "y": 0
        }

        var removeColumnButton = <ControlButton 
                            name="removePointColumn" 
                            fontAwesomeIcon="minus"
                            tooltip={removeColumnTooltip}
                            clickAction={this._onRemoveColumn.bind(this, this.props.item)}/> 

        var editColumnButton = <EditColumnButton 
                            name={"searchPointColumns" + this.props.column}
                            column={this.props.column} 
                            tooltipMsg="Edit Column"
                            findnext={this.props.onfindnext}
                            replace={this.props.onreplace}
                            replaceall={this.props.onreplaceall}
                            onfilter={this.props.onfilterboxchange} 
                            onclear={this.props.onclearfind}/>
        

        var cogBox = (
            <div style={cogBoxContainer}>
                <ul
                    className="opList">
                    <li 
                        className="opListItem edit"
                        onClick={this._onRemoveColumn}>Edit</li>
                    <li 
                        className="opListItem clone"
                        onClick={this._onCloneColumn}>Duplicate</li>
                    <li 
                        className="opListItem add"
                        onClick={this._onAddColumn}>Add</li>
                    <li 
                        className="opListItem remove"
                        onClick={this._onRemoveColumn}>Remove</li>
                </ul>
            </div> 
        );

        var cogTaptip = { 
            "content": cogBox,
            "x": 100,
            "y": 24,
            "styles": [{"key": "width", "value": "100px"}],
            "break": "",
            "padding": "0px"
        };

        var columnIndex = this.props.column;

        var cogIcon = (<i className={"fa fa-cog "}></i>);

        return (
            <ControlButton
                name={"cogControlButton" + columnIndex}
                taptip={cogTaptip}
                controlclass="cog_button"
                fontAwesomeIcon="cog"
                closeAction={this._onClose}/>
        );
    },
});

module.exports = CogButton;
