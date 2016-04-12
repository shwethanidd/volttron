'use strict';

var React = require('react');

var ControlButton = require('../control-button');
// var controlButtonStore = require('../../stores/control-button-store');
var ClearButton = require('./clear-button');

var EditColumnButton = React.createClass({
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
    _onFindBoxChange: function (e) {
        var findValue = e.target.value;

        this.setState({ findValue: findValue });

        // if (filterValue !== "")
        // {
        //     this.props.onfilter(e.target.value);
        // }
        // else
        // {
        //     this.props.onclear();
        // }
    },
    _onReplaceBoxChange: function (e) {
        var replaceValue = e.target.value;

        this.setState({ replaceValue: replaceValue });

        // if (filterValue !== "")
        // {
        //     this.props.onfilter(e.target.value);
        // }
        // else
        // {
        //     this.props.onclear();
        // }
    },
    _onClearEdit: function (e) {
        // this.setState({ filterValue: "" });
        // this.props.onclear();
    },
    render: function () {

        var editBoxContainer = {
            position: "relative"
        };

        var taptipX = 60;
        var taptipY = 120;

        var tooltipX = 20;
        var tooltipY = 60;

        var inputStyle = {
            width: "100%",
            marginLeft: "10px",
            fontWeight: "normal"
        }

        var divWidth = {
            width: "85%"
        }

        var editBox = (
            <div style={editBoxContainer}>
                <ClearButton onclear={this._onClearEdit}/>
                <div>
                    <div className="inlineBlock">
                        Find in Column
                    </div>
                    <div className="inlineBlock" style={divWidth}>
                        <input
                            type="text"
                            style={inputStyle}
                            onChange={this._onFindBoxChange}
                            value={ this.state.findValue }
                        />
                    </div>
                </div>
                <div>
                    <div className="inlineBlock">
                        Replace With
                    </div>
                    <div className="inlineBlock" style={divWidth}>
                        <input
                            type="text"
                            style={inputStyle}
                            onChange={this._onReplaceBoxChange}
                            value={ this.state.replaceValue }
                        />
                    </div>
                </div>
            </div> 
        );

        var editTaptip = { 
            "title": "Edit Column", 
            "content": editBox,
            "xOffset": taptipX,
            "yOffset": taptipY,
            "styles": [{"key": "width", "value": "200px"}]
        };
        
        var editIcon = (
            <i className="fa fa-edit"></i>
        );
        
        var editTooltip = {
            "content": this.props.tooltipMsg,
            "xOffset": tooltipX,
            "yOffset": tooltipY
        };

        var columnIndex = this.props.column;

        return (
            <ControlButton 
                name={"editControlButton" + columnIndex}
                taptip={editTaptip} 
                tooltip={editTooltip}
                icon={editIcon}></ControlButton>
        );
    },
});

function getStateFromStores() {
    return {
        findValue: "",
        replaceValue: ""
    };
}

module.exports = EditColumnButton;
