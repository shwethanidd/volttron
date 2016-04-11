'use strict';

var React = require('react');

var ControlButton = require('../control-button');

var AddButton = React.createClass({
    render: function () {

        var taptipX = 60;
        var taptipY = 120;

        var tooltipX = 20;
        var tooltipY = 60;

        var addIcon = <i className="fa fa-plus"></i>;

        var addTooltip = {
            "content": this.props.tooltipMsg,
            "xOffset": tooltipX,
            "yOffset": tooltipY
        };

        return (
            <ControlButton 
                name="addControlButton"
                icon={addIcon}
                tooltip={addTooltip}
                clickAction={this.props.onadd}></ControlButton>
        );
    },
});

module.exports = AddButton;
