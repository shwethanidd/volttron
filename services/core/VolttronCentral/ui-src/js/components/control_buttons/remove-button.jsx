'use strict';

var React = require('react');

var ControlButton = require('../control-button');

var RemoveButton = React.createClass({
    render: function () {

        var taptipX = 60;
        var taptipY = 120;

        var tooltipX = 20;
        var tooltipY = 60;

        var removeIcon = (
            <div>
                <span>-</span>
            </div>
        );
        var removeTooltip = {
            "content": "Remove Points",
            "xOffset": tooltipX,
            "yOffset": tooltipY
        };

        return (
            <ControlButton 
                name="removeControlButton"
                icon={removeIcon}
                tooltip={removeTooltip}
                clickAction={this.props.onremove}></ControlButton>
        );
    },
});

module.exports = RemoveButton;
