'use strict';

var React = require('react');

var ControlButton = require('../control-button');
// var controlButtonStore = require('../../stores/control-button-store');
var ClearButton = require('./clear-button');

var FilterPointsButton = React.createClass({
    getInitialState: function () {
        return getStateFromStores();
    },
    // componentDidMount: function () {
    //     controlButtonStore.addChangeListener(this._onStoresChange);
    // },
    // componentWillUnmount: function () {
    //     controlButtonStore.removeChangeListener(this._onStoresChange);
    // },
    // _onStoresChange: function () {

    //     if (controlButtonStore.getClearButton(this.props.name))
    //     {
    //         this.setState({ filterValue: "" });
    //     }
    // },
    _onFilterBoxChange: function (e) {
        var filterValue = e.target.value;

        this.setState({ filterValue: filterValue });

        if (filterValue !== "")
        {
            this.props.onfilter(e.target.value);
        }
        else
        {
            this.props.onclear();
        }
    },
    _onClearFilter: function (e) {
        this.setState({ filterValue: "" });
        this.props.onclear();
    },
    render: function () {

        var filterBoxContainer = {
            position: "relative"
        };

        var taptipX = 60;
        var taptipY = 120;

        var tooltipX = 20;
        var tooltipY = 60;

        var filterBox = (
            <div style={filterBoxContainer}>
                <ClearButton onclear={this._onClearFilter}/>
                <span className="fa fa-search"></span>
                <input
                    type="search"
                    onChange={this._onFilterBoxChange}
                    value={ this.state.filterValue }
                />
            </div> 
        );

        var filterTaptip = { 
            "title": "Search Points", 
            "content": filterBox,
            "xOffset": taptipX,
            "yOffset": taptipY,
            "styles": [{"key": "width", "value": "200px"}]
        };
        
        var filterIcon = (
            <i className="fa fa-search"></i>
        );
        
        var filterTooltip = {
            "content": "Search",
            "xOffset": tooltipX,
            "yOffset": tooltipY
        };

        var holdSelect = this.state.filterValue !== "";

        return (
            <ControlButton 
                name={"filterControlButton"}
                taptip={filterTaptip} 
                tooltip={filterTooltip}
                staySelected={holdSelect}
                icon={filterIcon}></ControlButton>
        );
    },
});

function getStateFromStores() {
    return {
        filterValue: ""
    };
}

module.exports = FilterPointsButton;
