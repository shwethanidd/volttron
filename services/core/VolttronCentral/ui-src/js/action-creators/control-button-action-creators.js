'use strict';

var ACTION_TYPES = require('../constants/action-types');
var dispatcher = require('../dispatcher');

var controlButtonActionCreators = {
	toggleTaptip: function (name) {
		dispatcher.dispatch({
			type: ACTION_TYPES.TOGGLE_TAPTIP,
			name: name,
		});
	},
	hideTaptip: function (name) {
		dispatcher.dispatch({
			type: ACTION_TYPES.HIDE_TAPTIP,
			name: name,
		});
	},
	showTaptip: function (name) {
		dispatcher.dispatch({
			type: ACTION_TYPES.SHOW_TAPTIP,
			name: name,
		});
	},
	clearButton: function (name) {
		dispatcher.dispatch({
			type: ACTION_TYPES.CLEAR_BUTTON,
			name: name,
		});
	},
	buttonCleared: function (name) {
		dispatcher.dispatch({
			type: ACTION_TYPES.BUTTON_CLEARED,
			name: name,
		});
	},
};



module.exports = controlButtonActionCreators;