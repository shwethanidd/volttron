'use strict';

var React = require('react');

var ControlButton = require('../control-button');

var ClearButton = React.createClass({
    render: function () {

        var taptipX = 60;
        var taptipY = 120;

        var tooltipX = 20;
        var tooltipY = 60;

        var clearIcon = (
            <i className="fa fa-ban"></i>
        );
        var clearTooltip = {
            "content": "Clear Search",
            "xOffset": tooltipX,
            "yOffset": tooltipY
        };

        return (
            <ControlButton 
                name="clearControlButton"
                icon={clearIcon}
                tooltip={clearTooltip}
                clickAction={this.props.onclear}></ControlButton>
        );
    },
});

module.exports = ClearButton;
