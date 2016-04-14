'use strict';

var React = require('react');

var ControlButton = require('../control-button');
// var controlButtonStore = require('../../stores/control-button-store');

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
    _findNext: function () {

        if (this.state.findValue === "")
        {
            this.props.onclear(this.props.column);
        }
        else
        {
            this.props.findnext(this.state.findValue, this.props.column);
        }
    },
    _onClearEdit: function (e) {
        this.props.onclear(this.props.column);

        this.setState({ findValue: "" });
    },
    _replaceNext: function () {

        // if (this.state.findValue === "")
        // {
        //     this.props.onclear(this.props.column);
        // }
        // else
        // {
        //     this.props.replacenext(this.state.findValue, this.props.column);
        // }
    },
    _replaceAll: function () {

        // if (this.state.findValue === "")
        // {
        //     this.props.onclear(this.props.column);
        // }
        // else
        // {
        //     this.props.replacenext(this.props.column);
        // }
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

        var clearTooltip = {
            content: "Clear Search"
        }

        var forwardTooltip = {
            content: "Find Next"
        }

        var replaceTooltip = {
            content: "Replace Next"
        }

        var replaceAllTooltip = {
            content: "Replace All"
        }

        var editBox = (
            <div style={editBoxContainer}>
                <ControlButton 
                    fontAwesomeIcon="ban"
                    tooltip={clearTooltip}
                    clickAction={this._onClearEdit}/>
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
                        <ControlButton 
                            fontAwesomeIcon="step-forward"
                            tooltip={forwardTooltip}
                            clickAction={this._findNext}/>
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
                        <ControlButton 
                            fontAwesomeIcon="pencil"
                            tooltip={replaceTooltip}
                            clickAction={this._replaceNext}/>
                        <ControlButton 
                            fontAwesomeIcon="edit"
                            tooltip={replaceAllTooltip}
                            clickAction={this._replaceAll}/>
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
                fontAwesomeIcon="pencil"/>
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
