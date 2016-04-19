(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
'use strict';

var React = require('react');
var Router = require('react-router');

var authorizationStore = require('./stores/authorization-store');
var Dashboard = require('./components/dashboard');
var LoginForm = require('./components/login-form');
var PageNotFound = require('./components/page-not-found');
var Platform = require('./components/platform');
var PlatformManager = require('./components/platform-manager');
var Platforms = require('./components/platforms');
var Devices = require('./components/devices');

var _afterLoginPath = '/dashboard';

function checkAuth(Component) {
    return React.createClass({
        statics: {
            willTransitionTo: function (transition) {
                if (transition.path !== '/login') {
                    _afterLoginPath = transition.path;

                    if (!authorizationStore.getAuthorization()) {
                        transition.redirect('/login');
                    }
                } else if (transition.path === '/login' && authorizationStore.getAuthorization()) {
                    transition.redirect(_afterLoginPath);
                }
            },
        },
        render: function () {
            return (
                React.createElement(Component, React.__spread({},  this.props))
            );
        },
    });
}

var AfterLogin = React.createClass({displayName: "AfterLogin",
    statics: {
        willTransitionTo: function (transition) {
            transition.redirect(_afterLoginPath);
        },
    },
    render: function () {},
});

var routes = (
    React.createElement(Router.Route, {path: "/", handler: PlatformManager}, 
        React.createElement(Router.Route, {name: "login", path: "login", handler: checkAuth(LoginForm)}), 
        React.createElement(Router.Route, {name: "dashboard", path: "dashboard", handler: checkAuth(Dashboard)}), 
        React.createElement(Router.Route, {name: "platforms", path: "platforms", handler: checkAuth(Platforms)}), 
        React.createElement(Router.Route, {name: "platform", path: "platforms/:uuid", handler: checkAuth(Platform)}), 
        React.createElement(Router.Route, {name: "devices", path: "devices", handler: checkAuth(Devices)}), 
        React.createElement(Router.NotFoundRoute, {handler: checkAuth(PageNotFound)}), 
        React.createElement(Router.DefaultRoute, {handler: AfterLogin})
    )
);

var router = Router.create(routes);

router.run(function (Handler) {
    React.render(
        React.createElement(Handler, null),
        document.getElementById('app')
    );

    authorizationStore.addChangeListener(function () {
        if (authorizationStore.getAuthorization() && router.isActive('/login')) {
            router.replaceWith(_afterLoginPath);
        } else if (!authorizationStore.getAuthorization() && !router.isActive('/login')) {
            router.replaceWith('/login');
        }
    });
});


},{"./components/dashboard":20,"./components/devices":24,"./components/login-form":28,"./components/page-not-found":31,"./components/platform":33,"./components/platform-manager":32,"./components/platforms":34,"./stores/authorization-store":46,"react":undefined,"react-router":undefined}],2:[function(require,module,exports){
'use strict';

var ACTION_TYPES = require('../constants/action-types');
var dispatcher = require('../dispatcher');
var RpcExchange = require('../lib/rpc/exchange');

var consoleActionCreators = {
    toggleConsole: function () {
        dispatcher.dispatch({
            type: ACTION_TYPES.TOGGLE_CONSOLE,
        });
    },
    updateComposerValue: function (value) {
        dispatcher.dispatch({
            type: ACTION_TYPES.UPDATE_COMPOSER_VALUE,
            value: value,
        });
    },
    makeRequest: function (opts) {
        new RpcExchange(opts).promise.catch(function ignore() {});
    }
};

module.exports = consoleActionCreators;


},{"../constants/action-types":37,"../dispatcher":38,"../lib/rpc/exchange":40}],3:[function(require,module,exports){
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

},{"../constants/action-types":37,"../dispatcher":38}],4:[function(require,module,exports){
'use strict';

var ACTION_TYPES = require('../constants/action-types');
var authorizationStore = require('../stores/authorization-store');
var dispatcher = require('../dispatcher');
var rpc = require('../lib/rpc');

var devicesActionCreators = {
    scanForDevices: function (platform) {
        dispatcher.dispatch({
            type: ACTION_TYPES.SCAN_FOR_DEVICES,
            platform: platform
        });
    },
    cancelScan: function (platform) {
        dispatcher.dispatch({
            type: ACTION_TYPES.CANCEL_SCANNING,
            platform: platform
        });
    },
    listDetectedDevices: function (platform) {
        dispatcher.dispatch({
            type: ACTION_TYPES.LIST_DETECTED_DEVICES,
            platform: platform
        });
    },
    configureDevice: function (device) {
        dispatcher.dispatch({
            type: ACTION_TYPES.CONFIGURE_DEVICE,
            device: device
        });
    },
    configureRegistry: function (device) {
        dispatcher.dispatch({
            type: ACTION_TYPES.CONFIGURE_REGISTRY,
            device: device
        });
    },
};



module.exports = devicesActionCreators;


},{"../constants/action-types":37,"../dispatcher":38,"../lib/rpc":41,"../stores/authorization-store":46}],5:[function(require,module,exports){
'use strict';

var ACTION_TYPES = require('../constants/action-types');
var dispatcher = require('../dispatcher');

var modalActionCreators = {
	openModal: function (content) {
		dispatcher.dispatch({
			type: ACTION_TYPES.OPEN_MODAL,
			content: content,
		});
	},
	closeModal: function () {
		dispatcher.dispatch({
			type: ACTION_TYPES.CLOSE_MODAL,
		});
	},
};

module.exports = modalActionCreators;


},{"../constants/action-types":37,"../dispatcher":38}],6:[function(require,module,exports){
'use strict';

var ACTION_TYPES = require('../constants/action-types');
var authorizationStore = require('../stores/authorization-store');
var dispatcher = require('../dispatcher');
var rpc = require('../lib/rpc');

var platformActionCreators = {
    loadPlatform: function (platform) {
        platformActionCreators.loadAgents(platform);
        platformActionCreators.loadCharts(platform);
    },
    clearPlatformError: function (platform) {
        dispatcher.dispatch({
            type: ACTION_TYPES.CLEAR_PLATFORM_ERROR,
            platform: platform,
        });
    },
    loadAgents: function (platform) {
        var authorization = authorizationStore.getAuthorization();

        new rpc.Exchange({
            method: 'platforms.uuid.' + platform.uuid + '.list_agents',
            authorization: authorization,
        }).promise
            .then(function (agentsList) {
                platform.agents = agentsList;

                dispatcher.dispatch({
                    type: ACTION_TYPES.RECEIVE_PLATFORM,
                    platform: platform,
                });

                if (!agentsList.length) { return; }

                new rpc.Exchange({
                    method: 'platforms.uuid.' + platform.uuid + '.status_agents',
                    authorization: authorization,
                }).promise
                    .then(function (agentStatuses) {
                        platform.agents.forEach(function (agent) {
                            if (!agentStatuses.some(function (status) {
                                if (agent.uuid === status.uuid) {
                                    agent.actionPending = false;
                                    agent.process_id = status.process_id;
                                    agent.return_code = status.return_code;

                                    return true;
                                }
                            })) {
                                agent.actionPending = false;
                                agent.process_id = null;
                                agent.return_code = null;
                            }

                        });

                        dispatcher.dispatch({
                            type: ACTION_TYPES.RECEIVE_PLATFORM,
                            platform: platform,
                        });
                    });
            })
            .catch(rpc.Error, handle401);
    },
    startAgent: function (platform, agent) {
        var authorization = authorizationStore.getAuthorization();

        agent.actionPending = true;

        dispatcher.dispatch({
            type: ACTION_TYPES.RECEIVE_PLATFORM,
            platform: platform,
        });

        new rpc.Exchange({
            method: 'platforms.uuid.' + platform.uuid + '.start_agent',
            params: [agent.uuid],
            authorization: authorization,
        }).promise
            .then(function (status) {
                agent.process_id = status.process_id;
                agent.return_code = status.return_code;
            })
            .catch(rpc.Error, handle401)
            .finally(function () {
                agent.actionPending = false;

                dispatcher.dispatch({
                    type: ACTION_TYPES.RECEIVE_PLATFORM,
                    platform: platform,
                });
            });
    },
    stopAgent: function (platform, agent) {
        var authorization = authorizationStore.getAuthorization();

        agent.actionPending = true;

        dispatcher.dispatch({
            type: ACTION_TYPES.RECEIVE_PLATFORM,
            platform: platform,
        });

        new rpc.Exchange({
            method: 'platforms.uuid.' + platform.uuid + '.stop_agent',
            params: [agent.uuid],
            authorization: authorization,
        }).promise
            .then(function (status) {
                agent.process_id = status.process_id;
                agent.return_code = status.return_code;
            })
            .catch(rpc.Error, handle401)
            .finally(function () {
                agent.actionPending = false;

                dispatcher.dispatch({
                    type: ACTION_TYPES.RECEIVE_PLATFORM,
                    platform: platform,
                });
            });
    },
    removeAgent: function (platform, agent) {
        var authorization = authorizationStore.getAuthorization();

        agent.actionPending = true;
        

        dispatcher.dispatch({
            type: ACTION_TYPES.CLOSE_MODAL,
        });

        dispatcher.dispatch({
            type: ACTION_TYPES.RECEIVE_PLATFORM,
            platform: platform,
        });

        var methodStr = 'platforms.uuid.' + platform.uuid + '.remove_agent';
        var agentId = [agent.uuid];
        
        new rpc.Exchange({
            method: methodStr,
            params: agentId,
            authorization: authorization,
        }).promise
            .then(function (result) {
                
                if (result.error) {
                    dispatcher.dispatch({
                        type: ACTION_TYPES.RECEIVE_PLATFORM_ERROR,
                        platform: platform,
                        error: result.error,
                    });
                }
                else
                {
                    platformActionCreators.loadPlatform(platform);
                }
            })
            .catch(rpc.Error, handle401);
    },
    installAgents: function (platform, files) {
        platformActionCreators.clearPlatformError(platform);

        var authorization = authorizationStore.getAuthorization();

        new rpc.Exchange({
            method: 'platforms.uuid.' + platform.uuid + '.install',
            params: { files: files },
            authorization: authorization,
        }).promise
            .then(function (results) {
                var errors = [];

                results.forEach(function (result) {
                    if (result.error) {
                        errors.push(result.error);
                    }
                });

                if (errors.length) {
                    dispatcher.dispatch({
                        type: ACTION_TYPES.RECEIVE_PLATFORM_ERROR,
                        platform: platform,
                        error: errors.join('\n'),
                    });
                }

                if (errors.length !== files.length) {
                    platformActionCreators.loadPlatform(platform);
                }
            })
            .catch(rpc.Error, handle401);
    },
    loadCharts: function (platform) {
        var authorization = authorizationStore.getAuthorization();

        new rpc.Exchange({
            method: 'platforms.uuid.' + platform.uuid + '.get_setting',
            params: { key: 'charts' },
            authorization: authorization,
        }).promise
            .then(function (charts) {
                if (charts && charts.length) {
                    platform.charts = charts;
                } else {
                    // Provide default set of charts if none are configured
                    platform.charts = [
//                        {
//                          "topic": "datalogger/log/platform/status/cpu/percent",
//                          "refreshInterval": 15000,
//                          "type": "line",
//                          "min": 0,
//                          "max": 100
//                        },
//                        {
//                          "topic": "datalogger/log/platform/status/cpu/times_percent/idle",
//                          "refreshInterval": 15000,
//                          "type": "line",
//                          "min": 0,
//                          "max": 100
//                        },
//                        {
//                          "topic": "datalogger/log/platform/status/cpu/times_percent/nice",
//                          "refreshInterval": 15000,
//                          "type": "line",
//                          "min": 0,
//                          "max": 100
//                        },
//                        {
//                          "topic": "datalogger/log/platform/status/cpu/times_percent/system",
//                          "refreshInterval": 15000,
//                          "type": "line",
//                          "min": 0,
//                          "max": 100
//                        },
//                        {
//                          "topic": "datalogger/log/platform/status/cpu/times_percent/user",
//                          "refreshInterval": 15000,
//                          "type": "line",
//                          "min": 0,
//                          "max": 100
//                        },
                    ];
                }

                dispatcher.dispatch({
                    type: ACTION_TYPES.RECEIVE_PLATFORM,
                    platform: platform,
                });
            })
            .catch(rpc.Error, handle401);
    },
    getTopicData: function (platform, topic) {
        var authorization = authorizationStore.getAuthorization();

        new rpc.Exchange({
            method: 'platforms.uuid.' + platform.uuid + '.historian.query',
            params: {
                topic: topic,
                count: 20,
                order: 'LAST_TO_FIRST',
            },
            authorization: authorization,
        }).promise
            .then(function (result) {
                dispatcher.dispatch({
                    type: ACTION_TYPES.RECEIVE_PLATFORM_TOPIC_DATA,
                    platform: platform,
                    topic: topic,
                    data: result.values,
                });
            })
            .catch(rpc.Error, handle401);
    },
    saveChart: function (platform, oldChart, newChart) {
        var authorization = authorizationStore.getAuthorization();
        var newCharts;

        if (!oldChart) {
            newCharts = platform.charts.concat([newChart]);
        } else {
            newCharts = platform.charts.map(function (chart) {
                if (chart === oldChart) {
                    return newChart;
                }

                return chart;
            });
        }

        new rpc.Exchange({
            method: 'platforms.uuid.' + platform.uuid + '.set_setting',
            params: { key: 'charts', value: newCharts },
            authorization: authorization,
        }).promise
            .then(function () {
                platform.charts = newCharts;

                dispatcher.dispatch({
                    type: ACTION_TYPES.CLOSE_MODAL,
                });

                dispatcher.dispatch({
                    type: ACTION_TYPES.RECEIVE_PLATFORM,
                    platform: platform,
                });
            });
    },
    deleteChart: function (platform, chartToDelete) {
        var authorization = authorizationStore.getAuthorization();

        var newCharts = platform.charts.filter(function (chart) {
            return (chart !== chartToDelete);
        });

        new rpc.Exchange({
            method: 'platforms.uuid.' + platform.uuid + '.set_setting',
            params: { key: 'charts', value: newCharts },
            authorization: authorization,
        }).promise
            .then(function () {
                platform.charts = newCharts;

                dispatcher.dispatch({
                    type: ACTION_TYPES.CLOSE_MODAL,
                });

                dispatcher.dispatch({
                    type: ACTION_TYPES.RECEIVE_PLATFORM,
                    platform: platform,
                });
            });
    },
};

function handle401(error) {
    if (error.code && error.code === 401) {
        dispatcher.dispatch({
            type: ACTION_TYPES.RECEIVE_UNAUTHORIZED,
            error: error,
        });

        platformActionCreators.clearAuthorization();
    }
}

module.exports = platformActionCreators;


},{"../constants/action-types":37,"../dispatcher":38,"../lib/rpc":41,"../stores/authorization-store":46}],7:[function(require,module,exports){
'use strict';

var ACTION_TYPES = require('../constants/action-types');
var authorizationStore = require('../stores/authorization-store');
var dispatcher = require('../dispatcher');
var platformActionCreators = require('../action-creators/platform-action-creators');
var rpc = require('../lib/rpc');

var initializing = false;

var platformManagerActionCreators = {
    initialize: function () {
        if (!authorizationStore.getAuthorization()) { return; }

        platformManagerActionCreators.loadPlatforms();
    },
    requestAuthorization: function (username, password) {
        new rpc.Exchange({
            method: 'get_authorization',
            params: {
                username: username,
                password: password,
            },
        }, ['password']).promise
            .then(function (result) {
                dispatcher.dispatch({
                    type: ACTION_TYPES.RECEIVE_AUTHORIZATION,
                    authorization: result,
                });
            })
            .then(platformManagerActionCreators.initialize)
            .catch(rpc.Error, handle401);
    },
    clearAuthorization: function () {
        dispatcher.dispatch({
            type: ACTION_TYPES.CLEAR_AUTHORIZATION,
        });
    },
    loadPlatforms: function () {
        var authorization = authorizationStore.getAuthorization();

        return new rpc.Exchange({
            method: 'list_platforms',
            authorization: authorization,
        }).promise
            .then(function (platforms) {
                dispatcher.dispatch({
                    type: ACTION_TYPES.RECEIVE_PLATFORMS,
                    platforms: platforms,
                });

                platforms.forEach(function (platform) {
                    platformActionCreators.loadPlatform(platform);
                });
            })
            .catch(rpc.Error, handle401);
    },
    registerPlatform: function (name, address) {
        var authorization = authorizationStore.getAuthorization();

        new rpc.Exchange({
            method: 'register_platform',
            authorization: authorization,
            params: {
                identity: 'platform.agent',
                agentid: name,
                address: address,
            },
        }).promise
            .then(function () {
                dispatcher.dispatch({
                    type: ACTION_TYPES.CLOSE_MODAL,
                });

                platformManagerActionCreators.loadPlatforms();
            })
            .catch(rpc.Error, function (error) {
                dispatcher.dispatch({
                    type: ACTION_TYPES.REGISTER_PLATFORM_ERROR,
                    error: error,
                });

                handle401(error);
            });
    },
    deregisterPlatform: function (platform) {
        var authorization = authorizationStore.getAuthorization();

        new rpc.Exchange({
            method: 'unregister_platform',
            authorization: authorization,
            params: {
                platform_uuid: platform.uuid
            },
        }).promise
            .then(function (platform) {
                dispatcher.dispatch({
                    type: ACTION_TYPES.CLOSE_MODAL,
                });

                platformManagerActionCreators.loadPlatforms();
            })
            .catch(rpc.Error, function (error) {
                dispatcher.dispatch({
                    type: ACTION_TYPES.DEREGISTER_PLATFORM_ERROR,
                    error: error,
                });

                handle401(error);
            });
    },
};

function handle401(error) {
    if (error.code && error.code === 401) {
        dispatcher.dispatch({
            type: ACTION_TYPES.RECEIVE_UNAUTHORIZED,
            error: error,
        });

        platformManagerActionCreators.clearAuthorization();
    }
}

module.exports = platformManagerActionCreators;


},{"../action-creators/platform-action-creators":6,"../constants/action-types":37,"../dispatcher":38,"../lib/rpc":41,"../stores/authorization-store":46}],8:[function(require,module,exports){
'use strict';

var React = require('react');

var platformActionCreators = require('../action-creators/platform-action-creators');
var modalActionCreators = require('../action-creators/modal-action-creators');

var RemoveAgentForm = require('./remove-agent-form');

var AgentRow = React.createClass({displayName: "AgentRow",
    _onStop: function () {
        platformActionCreators.stopAgent(this.props.platform, this.props.agent);
    },
    _onStart: function () {
        platformActionCreators.startAgent(this.props.platform, this.props.agent);
    },
    _onRemove: function () {
        modalActionCreators.openModal(React.createElement(RemoveAgentForm, {platform: this.props.platform, agent: this.props.agent}));
    },
    render: function () {
        var agent = this.props.agent, status, action, remove;

        if (agent.actionPending === undefined) {
            status = 'Retrieving status...';
        } else if (agent.actionPending) {
            if (agent.process_id === null || agent.return_code !== null) {
                status = 'Starting...';
                action = (
                    React.createElement("input", {className: "button button--agent-action", type: "button", value: "Start", disabled: true})
                );
            } else {
                status = 'Stopping...';
                action = (
                    React.createElement("input", {className: "button button--agent-action", type: "button", value: "Stop", disabled: true})
                );
            }
        } else {
            if (agent.process_id === null) {
                status = 'Never started';
                action = (
                    React.createElement("input", {className: "button button--agent-action", type: "button", value: "Start", onClick: this._onStart})
                );
            } else if (agent.return_code === null) {
                status = 'Running (PID ' + agent.process_id + ')';
                action = (
                    React.createElement("input", {className: "button button--agent-action", type: "button", value: "Stop", onClick: this._onStop})
                );
            } else {
                status = 'Stopped (returned ' + agent.return_code + ')';
                action = (
                    React.createElement("input", {className: "button button--agent-action", type: "button", value: "Start", onClick: this._onStart})
                );
            }
        }

        remove = ( React.createElement("input", {className: "button button--agent-action", type: "button", value: "Remove", onClick: this._onRemove}) );

        return (
            React.createElement("tr", null, 
                React.createElement("td", null, agent.name), 
                React.createElement("td", null, agent.uuid), 
                React.createElement("td", null, status), 
                React.createElement("td", null, action, " ", remove)
            )
        );
    },
});

module.exports = AgentRow;


},{"../action-creators/modal-action-creators":5,"../action-creators/platform-action-creators":6,"./remove-agent-form":36,"react":undefined}],9:[function(require,module,exports){
'use strict';

var React = require('react');

var topicDataStore = require('../stores/topic-data-store');
var platformActionCreators = require('../action-creators/platform-action-creators');
var LineChart = require('./line-chart');

var chartTypes = {
    'line': LineChart,
};

var Chart = React.createClass({displayName: "Chart",
    getInitialState: function () {
        return getStateFromStores(this.props.platform, this.props.chart);
    },
    componentDidMount: function () {
        topicDataStore.addChangeListener(this._onStoreChange);

        if (!this._getTopicDataTimeout) {
            this._getTopicDataTimeout = setTimeout(this._getTopicData, 0);
        }
    },
    componentWillUnmount: function () {
        topicDataStore.removeChangeListener(this._onStoreChange);
        clearTimeout(this._getTopicDataTimeout);
    },
    _initTopicData: function () {

    },
    _onStoreChange: function () {
        this.setState(getStateFromStores(this.props.platform, this.props.chart));
    },
    _getTopicData: function () {
        platformActionCreators.getTopicData(
            this.props.platform,
            this.props.chart.topic
        );

        if (this.props.chart.refreshInterval) {
            this._getTopicDataTimeout = setTimeout(this._getTopicData, this.props.chart.refreshInterval);
        }
    },
    render: function () {
        var ChartClass = chartTypes[this.props.chart.type];

        return (
            React.createElement(ChartClass, {
                className: "chart", 
                chart: this.props.chart, 
                data: this.state.data || []}
            )
        );
    },
});

function getStateFromStores(platform, chart) {
    return { data: topicDataStore.getTopicData(platform, chart.topic) };
}

module.exports = Chart;


},{"../action-creators/platform-action-creators":6,"../stores/topic-data-store":54,"./line-chart":27,"react":undefined}],10:[function(require,module,exports){
'use strict';

var React = require('react');

var consoleActionCreators = require('../action-creators/console-action-creators');
var consoleStore = require('../stores/console-store');

var Composer = React.createClass({displayName: "Composer",
    getInitialState: getStateFromStores,
    componentDidMount: function () {
        consoleStore.addChangeListener(this._onChange);
    },
    componentWillUnmount: function () {
        consoleStore.removeChangeListener(this._onChange);
    },
    _onChange: function () {
        this.replaceState(getStateFromStores());
    },
    _onSendClick: function () {
        consoleActionCreators.makeRequest(JSON.parse(this.state.composerValue));
    },
    _onTextareaChange: function (e) {
        consoleActionCreators.updateComposerValue(e.target.value);
    },
    render: function () {
        return (
            React.createElement("div", {className: "composer"}, 
                React.createElement("textarea", {
                    key: this.state.composerId, 
                    onChange: this._onTextareaChange, 
                    defaultValue: this.state.composerValue}
                ), 
                React.createElement("input", {
                    className: "button", 
                    ref: "send", 
                    type: "button", 
                    value: "Send", 
                    disabled: !this.state.valid, 
                    onClick: this._onSendClick}
                )
            )
        );
    },
});

function getStateFromStores() {
    var composerValue = consoleStore.getComposerValue();
    var valid = true;

    try {
        JSON.parse(composerValue);
    } catch (ex) {
        if (ex instanceof SyntaxError) {
            valid = false;
        } else {
            throw ex;
        }
    }

    return {
        composerId: consoleStore.getComposerId(),
        composerValue: composerValue,
        valid: valid,
    };
}

module.exports = Composer;


},{"../action-creators/console-action-creators":2,"../stores/console-store":47,"react":undefined}],11:[function(require,module,exports){
'use strict';

var React = require('react');
var Router = require('react-router');

var devicesActionCreators = require('../action-creators/devices-action-creators');
var devicesStore = require('../stores/devices-store');

var ConfigureDevice = React.createClass({displayName: "ConfigureDevice",
    getInitialState: function () {
        return getStateFromStores();
    },
    componentDidMount: function () {
        // platformsStore.addChangeListener(this._onStoresChange);
    },
    componentWillUnmount: function () {
        // platformsStore.removeChangeListener(this._onStoresChange);
    },
    _onStoresChange: function () {
        this.setState(getStateFromStores());
    },
    _configureDevice: function (device) {
        devicesActionCreators.configureDevice(device);
    },
    _updateSetting: function (evt) {
        var newVal = evt.target.value;
        var key = evt.currentTarget.dataset.setting;

        var tmpState = JSON.parse(JSON.stringify(this.state));

        var newSettings = tmpState.settings.map(function (item) {
            if (item.key === key)
            {
                item.value = newVal;                
            }

            return item;
        });

        this.setState({settings: newSettings});
    },
    _updateRegistryPath: function (evt) {
        this.setState({registry_config: evt.target.value});
    },
    _uploadRegistryFile: function (evt) {

    },
    _generateRegistryFile: function (device) {
        devicesActionCreators.configureRegistry(device);
    },
    render: function () {        
        
        var attributeRows = 
            this.props.device.map(function (device) {

                return (
                    React.createElement("tr", null, 
                        React.createElement("td", null, device.label), 
                        React.createElement("td", {className: "plain"}, device.value)
                    )
                );

            });

        var tableStyle = {
            backgroundColor: "#E7E7E7"
        }

        var uneditableAttributes = 
            React.createElement("table", {style: tableStyle}, 
                React.createElement("tbody", null, 

                     attributeRows, 

                    React.createElement("tr", null, 
                        React.createElement("td", null, "Proxy Address"), 
                        React.createElement("td", {className: "plain"}, "10.0.2.15")
                    ), 
                    React.createElement("tr", null, 
                        React.createElement("td", null, "Network Interface"), 
                        React.createElement("td", {className: "plain"}, "UDP/IP")
                    ), 
                    React.createElement("tr", null, 
                        React.createElement("td", null, "Campus"), 
                        React.createElement("td", {className: "plain"}, "PNNL")
                    )

                )
            );

        var buttonStyle = {
            height: "24px",
            lineHeight: "18px"
        }

        var firstStyle = {
            width: "30%",
            textAlign: "right"
        }

        var secondStyle = {
            width: "50%"
        }

        var buttonColumns = {
            width: "8%"
        }

        var settingsRows = 
            this.state.settings.map(function (setting) {

                var stateSetting = this.state.settings.find(function (s) {
                    return s.key === setting.key;
                })

                return (
                    React.createElement("tr", null, 
                        React.createElement("td", {style: firstStyle}, setting.label), 
                        React.createElement("td", {style: secondStyle, 
                            className: "plain"}, 
                            React.createElement("input", {
                                className: "form__control form__control--block", 
                                type: "text", 
                                "data-setting": setting.key, 
                                onChange: this._updateSetting, 
                                value: stateSetting.value}
                            )
                        )
                    )
                );
            }, this);

        var registryConfigRow = 
            React.createElement("tr", null, 
                React.createElement("td", {style: firstStyle}, "Registry Configuration File"), 
                React.createElement("td", {
                    style: secondStyle, 
                    className: "plain"}, 
                    React.createElement("input", {
                        className: "form__control form__control--block", 
                        type: "text", 
                        onChange: this._updateRegistryPath, 
                        value: this.state.registry_config}
                    )
                ), 
                React.createElement("td", {
                    style: buttonColumns, 
                    className: "plain"}, 
                    React.createElement("button", {
                        style: buttonStyle}, "Upload")
                ), 
                React.createElement("td", {
                    style: buttonColumns, 
                    className: "plain"}, 
                    React.createElement("button", {
                        style: buttonStyle, onClick: this._generateRegistryFile.bind(this, this.props.device)}, "Generate")
                )
            )

        var editableAttributes = 
            React.createElement("table", null, 
                React.createElement("tbody", null, 
                     settingsRows, 
                     registryConfigRow 
                )
            )

        return (
            React.createElement("div", {className: "configDeviceContainer"}, 
                React.createElement("div", {className: "uneditableAttributes"}, 
                     uneditableAttributes 
                ), 
                React.createElement("div", {className: "configDeviceBox"}, 
                     editableAttributes 
                )
            )
        );
    },
});

function getStateFromStores() {
    return {
        settings: [
            { key: "unit", value: "", label: "Unit" },
            { key: "building", value: "", label: "Building" },
            { key: "path", value: "", label: "Path" },
            { key: "interval", value: "", label: "Interval" },
            { key: "timezone", value: "", label: "Timezone" },
            { key: "heartbeat_point", value: "", label: "Heartbeat Point" },
            { key: "minimum_priority", value: "", label: "Minimum Priority" },
            { key: "max_objs_per_read", value: "", label: "Maximum Objects per Read" }
        ],
        registry_config: ""
    };
}

module.exports = ConfigureDevice;


},{"../action-creators/devices-action-creators":4,"../stores/devices-store":49,"react":undefined,"react-router":undefined}],12:[function(require,module,exports){
'use strict';

var React = require('react');
var Router = require('react-router');

var devicesActionCreators = require('../action-creators/devices-action-creators');
var devicesStore = require('../stores/devices-store');
var FilterPointsButton = require('./control_buttons/filter-points-button');
var ControlButton = require('./control-button');
var CogButton = require('./control_buttons/cog-select-button');
var EditColumnButton = require('./control_buttons/edit-columns-button');

var ConfirmForm = require('./confirm-form');
var modalActionCreators = require('../action-creators/modal-action-creators');

var ConfigureRegistry = React.createClass({displayName: "ConfigureRegistry",    
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
        state.selectedCellColumn = null;

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
            React.createElement(ConfirmForm, {
                promptTitle: "Remove Points", 
                promptText:  promptText, 
                confirmText:  confirmText, 
                onConfirm:  confirmAction, 
                cancelText:  cancelText 
            })
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
    _onCloneColumn: function (index) {

        var registryHeader = this.state.registryHeader.slice();
        var registryValues = this.state.registryValues.slice();
        var columnNames = this.state.columnNames.slice();
        
        registryHeader.splice(index + 1, 0, registryHeader[index]);

        this.setState({ registryHeader: registryHeader });

        columnNames.splice(index + 1, 0, registryHeader[index]);

        this.setState({ columnNames: columnNames });

        var newRegistryValues = registryValues.map(function (values, row) {

            var clonedValue = {};

            for (var key in values[index])
            {
                clonedValue[key] = values[index][key];
            }

            values.splice(index + 1, 0, clonedValue);

            return values;
        });

        this.resizeTable = true;

        this.setState({ registryValues: newRegistryValues });

    },
    _onRemoveColumn: function (column) {

        var promptText = ("Are you sure you want to delete the column, " + column + "?");
        
        modalActionCreators.openModal(
            React.createElement(ConfirmForm, {
                promptTitle: "Remove Column", 
                promptText:  promptText, 
                confirmText: "Delete", 
                onConfirm: this._removeColumn.bind(this, column)
            })
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
    _updateCell: function (row, column, e) {

        var currentTarget = e.currentTarget;
        var newRegistryValues = this.state.registryValues.slice();

        newRegistryValues[row][column].value = currentTarget.value;

        this.setState({ registryValues: newRegistryValues });
    },
    _onFindNext: function (findValue, column) {

        var registryValues = this.state.registryValues.slice();
        
        if (this.state.selectedCells.length === 0)
        {
            var selectedCells = [];

            this.setState({ registryValues: registryValues.map(function (values, row) {

                    //searching i-th column in each row, and if the cell contains the target value, select it
                    values[column].selected = (values[column].value.indexOf(findValue) > -1);

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
                this.setState({ selectedCellColumn: column });

                //set focus to the first selected cell
                this.setState({ selectedCellRow: selectedCells[0]});
            }
        }
        else
        {
            //we've already found the selected cells, so we need to advance focus to the next one
            if (this.state.selectedCells.length > 1)
            {
                var selectedCellRow = this._goToNext(this.state.selectedCellRow, this.state.selectedCells);

                this.setState({ selectedCellRow: selectedCellRow});
            }
        }
    },
    _onReplace: function (findValue, replaceValue, column) {

        if (!this.state.selectedCellRow)
        {
            this._onFindNext(findValue, column);
        }
        else
        {
            var registryValues = this.state.registryValues.slice();
            registryValues[this.state.selectedCellRow][column].value = registryValues[this.state.selectedCellRow][column].value.replace(findValue, replaceValue);        

            //If the cell no longer has the target value, deselect it and move focus to the next selected cell
            if (registryValues[this.state.selectedCellRow][column].value.indexOf(findValue) < 0)
            {
                registryValues[this.state.selectedCellRow][column].selected = false;

                //see if there will even be another selected cell to move to
                var selectedCells = this.state.selectedCells.slice();
                var index = selectedCells.indexOf(this.state.selectedCellRow);

                if (index > -1)
                {
                    selectedCells.splice(index, 1);
                }

                if (selectedCells.length > 0)
                {
                    var selectedCellRow = this._goToNext(this.state.selectedCellRow, this.state.selectedCells);
                
                    this.setState({ selectedCellRow: selectedCellRow});
                    this.setState({ selectedCells: selectedCells });
                }
                else
                {
                    //there were no more selected cells, so clear everything out
                    this.setState({ selectedCells: [] });
                    this.setState({ selectedCellRow: null });
                    this.setState({ selectedCellColumn: null });
                }
            }

            this.setState({ registryValues: registryValues});
        }
    },
    _onReplaceAll: function (findValue, replaceValue, column) {

        if (!this.state.selectedCellRow)
        {
            this._onFindNext(findValue, column);
        }
        else
        {
            var registryValues = this.state.registryValues.slice();
            var selectedCells = this.state.selectedCells.slice();
            var selectedCellRow = this.state.selectedCellRow;

            while (selectedCells.length > 0)
            {
                registryValues[selectedCellRow][column].value = registryValues[this.state.selectedCellRow][column].value.replace(findValue, replaceValue);        

                if (registryValues[selectedCellRow][column].value.indexOf(findValue) < 0)
                {
                    registryValues[selectedCellRow][column].selected = false;

                    var index = selectedCells.indexOf(selectedCellRow);

                    if (index > -1)
                    {
                        selectedCells.splice(index, 1);
                    }
                    else
                    {
                        //something went wrong, so stop the while loop
                        break;
                    }

                    if (selectedCells.length > 0)
                    {
                        selectedCellRow = this._goToNext(selectedCellRow, this.state.selectedCells);
                    }
                }
            }

            this.setState({ selectedCellRow: null});
            this.setState({ selectedCells: [] });
            this.setState({ selectedCellColumn: null });
            this.setState({ registryValues: registryValues});
        }
    },
    _onClearFind: function (column) {

        var registryValues = this.state.registryValues.slice();

        this.state.selectedCells.map(function (row) {
            registryValues[row][column].selected = false;
        });

        this.setState({ registryValues: registryValues });
        this.setState({ selectedCells: [] });
        this.setState({ selectedCellRow: null });
        this.setState({ selectedCellColumn: null });

    },
    _goToNext: function (selectedCellRow, selectedCells) {

        //this is the row with current focus
        var rowIndex = selectedCells.indexOf(selectedCellRow);

        if (rowIndex > -1)
        {
            //either set focus to the next one in the selected cells list
            if (rowIndex < selectedCells.length - 1)
            {
                selectedCellRow = selectedCells[++rowIndex];
            }
            else //or if we're at the end of the list, go back to the first one
            {
                selectedCellRow = selectedCells[0];
            }
        }

        return selectedCellRow;
    },
    render: function () {        
        
        var filterPointsTooltip = {
            content: "Filter Points",
            "x": 160,
            "y": 0
        }

        var filterButton = React.createElement(FilterPointsButton, {
                                name: "filterRegistryPoints", 
                                tooltipMsg: filterPointsTooltip, 
                                onfilter: this._onFilterBoxChange, 
                                onclear: this._onClearFilter})

        var addPointTooltip = {
            content: "Add New Point",
            "x": 160,
            "y": 0
        }

        var addPointButton = React.createElement(ControlButton, {
                                name: "addRegistryPoint", 
                                tooltip: addPointTooltip, 
                                controlclass: "add_point_button", 
                                fontAwesomeIcon: "plus", 
                                clickAction: this._onAddPoint})


        var removePointTooltip = {
            content: "Remove Points",
            "x": 160,
            "y": 0
        }

        var removePointsButton = React.createElement(ControlButton, {
                                name: "removeRegistryPoints", 
                                fontAwesomeIcon: "minus", 
                                tooltip: removePointTooltip, 
                                controlclass: "remove_point_button", 
                                clickAction: this._onRemovePoints})        
        
        var registryRows, registryHeader;
        
        registryRows = this.state.registryValues.map(function (attributesList, rowIndex) {

            var registryCells = attributesList.map(function (item, columnIndex) {

                var selectedStyle = (item.selected ? {backgroundColor: "#F5B49D"} : {});
                var focusedCell = (this.state.selectedCellColumn === columnIndex && this.state.selectedCellRow === rowIndex ? "focusedCell" : "");

                var itemCell = (columnIndex === 0 && item.value !== "" ? 
                                    React.createElement("td", null,  item.value) : 
                                        React.createElement("td", null, React.createElement("input", {
                                                id: this.state.registryValues[rowIndex][columnIndex].key + "-" + columnIndex + "-" + rowIndex, 
                                                type: "text", 
                                                className: focusedCell, 
                                                style: selectedStyle, 
                                                onChange: this._updateCell.bind(this, rowIndex, columnIndex), 
                                                value:  this.state.registryValues[rowIndex][columnIndex].value})
                                        ));

                // console.log(itemCell);

                return itemCell;
            }, this);

            return ( 
                React.createElement("tr", null, 
                    React.createElement("td", null, 
                        React.createElement("input", {type: "checkbox", 
                            onChange: this._selectForDelete.bind(this, attributesList), 
                            checked: this.state.pointsToDelete.indexOf(attributesList[0].value) > -1}
                        )
                    ), 
                     registryCells 
                )
            )
        }, this);

        var wideCell = {
            width: "100%"
        }

        registryHeader = this.state.registryHeader.map(function (item, index) {

            var cogButton = (React.createElement(CogButton, {
                                onremove: this._onRemoveColumn, 
                                onadd: this._onAddColumn, 
                                onclone: this._onCloneColumn, 
                                column: index, 
                                item: item}));

            var editColumnButton = React.createElement(EditColumnButton, {
                            column: index, 
                            tooltipMsg: "Edit Column", 
                            findnext: this._onFindNext, 
                            replace: this._onReplace, 
                            replaceall: this._onReplaceAll, 
                            onfilter: this._onFilterBoxChange, 
                            onclear: this._onClearFind})

            var headerCell = (index === 0 ?
                                ( React.createElement("th", null, 
                                    React.createElement("div", {className: "th-inner"}, 
                                         item, " ",  filterButton, " ",  addPointButton, " ",  removePointsButton 
                                    )
                                )) :
                                ( React.createElement("th", null, 
                                    React.createElement("div", {className: "th-inner", style: wideCell}, 
                                         item, 
                                         cogButton, 
                                         editColumnButton 
                                    )
                                ) ) );

            return headerCell;
        }, this);        

        var wideDiv = {
            width: "100%",
            textAlign: "center",
            paddingTop: "20px"
        }
            
        return (
            React.createElement("div", null, 
                React.createElement("div", {className: "fixed-table-container"}, 
                    React.createElement("div", {className: "header-background"}), 
                    React.createElement("div", {className: "fixed-table-container-inner"}, 
                        React.createElement("table", {className: "registryConfigTable"}, 
                            React.createElement("thead", null, 
                                React.createElement("tr", null, 
                                    React.createElement("th", null, 
                                        React.createElement("div", {className: "th-inner"}, 
                                            React.createElement("input", {type: "checkbox", 
                                                onChange: this._selectAll, 
                                                checked: this.state.allSelected})
                                        )
                                    ), 
                                     registryHeader 
                                )
                            ), 
                            React.createElement("tbody", null, 
                                 registryRows 
                            )
                        )
                    )
                ), 
                React.createElement("div", {style: wideDiv}, 
                    React.createElement("button", null, "Save")
                )
            )
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


},{"../action-creators/devices-action-creators":4,"../action-creators/modal-action-creators":5,"../stores/devices-store":49,"./confirm-form":13,"./control-button":15,"./control_buttons/cog-select-button":16,"./control_buttons/edit-columns-button":17,"./control_buttons/filter-points-button":18,"react":undefined,"react-router":undefined}],13:[function(require,module,exports){
'use strict';

var React = require('react');

var modalActionCreators = require('../action-creators/modal-action-creators');

var ConfirmForm = React.createClass({displayName: "ConfirmForm",
    _onCancelClick: modalActionCreators.closeModal,
    _onSubmit: function () {
        this.props.onConfirm();
    },
    render: function () {

        var confirmButton;

        if (this.props.confirmText)
        {
            confirmButton = (React.createElement("button", {className: "button"}, this.props.confirmText));
        }

        var cancelText = (this.props.cancelText ? this.props.cancelText : "Cancel");

        return (
            React.createElement("form", {className: "confirmation-form", onSubmit: this._onSubmit}, 
                React.createElement("h1", null, this.props.promptTitle), 
                React.createElement("p", null, 
                    this.props.promptText
                ), 
                React.createElement("div", {className: "form__actions"}, 
                    React.createElement("button", {
                        className: "button button--secondary", 
                        type: "button", 
                        onClick: this._onCancelClick, 
                        autoFocus: true
                    }, 
                        cancelText
                    ), 
                    confirmButton
                )
            )
        );
    },
});

module.exports = ConfirmForm;


},{"../action-creators/modal-action-creators":5,"react":undefined}],14:[function(require,module,exports){
'use strict';

var React = require('react');

var Composer = require('./composer');
var Conversation = require('./conversation');

var Console = React.createClass({displayName: "Console",
    render: function () {
        return (
            React.createElement("div", {className: "console"}, 
                React.createElement(Conversation, null), 
                React.createElement(Composer, null)
            )
        );
    }
});

module.exports = Console;


},{"./composer":10,"./conversation":19,"react":undefined}],15:[function(require,module,exports){
'use strict';

var React = require('react');
var Router = require('react-router');
var controlButtonStore = require('../stores/control-button-store');
var controlButtonActionCreators = require('../action-creators/control-button-action-creators');


var ControlButton = React.createClass({displayName: "ControlButton",
	getInitialState: function () {
		var state = {};

		state.showTaptip = false;
		state.showTooltip = false;
		state.deactivateTooltip = false;

        state.selected = (this.props.selected === true);

		state.taptipX = 0;
		state.taptipY = 0;
        state.tooltipX = 0;
        state.tooltipY = 0;

        state.tooltipOffsetX = 0;
        state.tooltipOffsetY = 0;
        state.taptipOffsetX = 0;
        state.taptipOffsetY = 0;

        if (this.props.hasOwnProperty("tooltip"))
        {
            if (this.props.tooltip.hasOwnProperty("x"))
                state.tooltipX = this.props.tooltip.x;

            if (this.props.tooltip.hasOwnProperty("y"))
                state.tooltipY = this.props.tooltip.y;
            
            if (this.props.tooltip.hasOwnProperty("xOffset"))
                state.tooltipOffsetX = this.props.tooltip.xOffset;

            if (this.props.tooltip.hasOwnProperty("yOffset"))
                state.tooltipOffsetY = this.props.tooltip.yOffset;
        }

        if (this.props.hasOwnProperty("taptip"))
        {
            if (this.props.taptip.hasOwnProperty("x"))
                state.taptipX = this.props.taptip.x;

            if (this.props.taptip.hasOwnProperty("y"))
                state.taptipY = this.props.taptip.y;
            
            if (this.props.taptip.hasOwnProperty("xOffset"))
                state.taptipOffsetX = this.props.taptip.xOffset;

            if (this.props.taptip.hasOwnProperty("yOffset"))
                state.taptipOffsetY = this.props.taptip.yOffset;
        }

		return state;
	},
    componentDidMount: function () {
        controlButtonStore.addChangeListener(this._onStoresChange);

        window.addEventListener('keydown', this._hideTaptip);
    },
    componentWillUnmount: function () {
        controlButtonStore.removeChangeListener(this._onStoresChange);

        window.removeEventListener('keydown', this._hideTaptip);
    },
    componentWillReceiveProps: function (nextProps) {
    	this.setState({ selected: (nextProps.selected === true) });

    	if (nextProps.selected === true) 
    	{
    		this.setState({ showTooltip: false });
    	}    	
    },
    _onStoresChange: function () {

    	var showTaptip = controlButtonStore.getTaptip(this.props.name);
    	
    	if (showTaptip !== null)
    	{
	    	if (showTaptip !== this.state.showTaptip)
	    	{
	    		this.setState({ showTaptip: showTaptip });	
	    	}
            
            this.setState({ selected: (showTaptip === true) }); 

	    	if (showTaptip === true)
	    	{
	    		this.setState({ showTooltip: false });
	    	}
            else
            {
                if (typeof this.props.closeAction == 'function')
                {
                    this.props.closeAction();
                }
            }
	    }
    },
	_showTaptip: function (evt) {

		if (!this.state.showTaptip)
		{
            if (!(this.props.taptip.hasOwnProperty("x") && this.props.taptip.hasOwnProperty("y")))
            {
                this.setState({taptipX: evt.clientX - this.state.taptipOffsetX});
                this.setState({taptipY: evt.clientY - this.state.taptipOffsetY});    
            }
			
            // console.log("clientX: " + evt.clientX + ", clientY: " + evt.clientY);
            // console.log("taptipOffsetX: " + this.state.taptipOffsetX + ", taptipOffsetY: " + this.state.taptipOffsetY);
            // console.log("left: " + (evt.clientX - this.state.taptipOffsetX) + ", top: " + (evt.clientY - this.state.taptipOffsetY));
		}

		controlButtonActionCreators.toggleTaptip(this.props.name);
	},
	_hideTaptip: function (evt) {
		if (evt.keyCode === 27) 
		{
	        controlButtonActionCreators.hideTaptip(this.props.name);
        }
	},
    _showTooltip: function (evt) {
        this.setState({showTooltip: true});

        if (!(this.props.tooltip.hasOwnProperty("x") && this.props.tooltip.hasOwnProperty("y")))
        {
            this.setState({tooltipX: evt.clientX - this.state.tooltipOffsetX});
            this.setState({tooltipY: evt.clientY - this.state.tooltipOffsetY});
        }
    },
    _hideTooltip: function () {
        this.setState({showTooltip: false});
    },
    render: function () {
        
        var taptip;
        var tooltip;
        var clickAction;
        var selectedStyle;

        var tooltipShow;
        var tooltipHide;

        var buttonIcon = (this.props.icon ? this.props.icon :
                            (this.props.fontAwesomeIcon ? 
                                (React.createElement("i", {className: "fa fa-" + this.props.fontAwesomeIcon})) : 
                                    (React.createElement("div", {className: this.props.buttonClass}, React.createElement("span", null, this.props.unicodeIcon))) ) );

        if (this.props.staySelected || this.state.selected === true || this.state.showTaptip === true)
        {
        	selectedStyle = {
	        	backgroundColor: "#ccc"
	        }
        }
        else if (this.props.tooltip)
        {
        	var tooltipStyle = {
	            display: (this.state.showTooltip ? "block" : "none"),
	            position: "absolute",
	            top: this.state.tooltipY + "px",
	            left: this.state.tooltipX + "px"
	        };

	        var toolTipClasses = (this.state.showTooltip ? "tooltip_outer delayed-show-slow" : "tooltip_outer");

	        tooltipShow = this._showTooltip;
	        tooltipHide = this._hideTooltip;

        	tooltip = (React.createElement("div", {className: toolTipClasses, 
                        style: tooltipStyle}, 
                        React.createElement("div", {className: "tooltip_inner"}, 
                            React.createElement("div", {className: "opaque_inner"}, 
                                this.props.tooltip.content
                            )
                        )
                    ))
        }
        

        if (this.props.taptip)
        {
        	var taptipStyle = {
		        display: (this.state.showTaptip ? "block" : "none"),
		        position: "absolute",
		        left: this.state.taptipX + "px",
		        top: this.state.taptipY + "px"
		    };

            //TODO: add this to repository
            if (this.props.taptip.styles)
            {
                this.props.taptip.styles.forEach(function (styleToAdd) {
                    taptipStyle[styleToAdd.key] = styleToAdd.value;
                });
            }
            //end TODO

		    var tapTipClasses = "taptip_outer";

            var taptipBreak = (this.props.taptip.hasOwnProperty("break") ? this.props.taptip.break : React.createElement("br", null));
            var taptipTitle = (this.props.taptip.hasOwnProperty("title") ? (React.createElement("h4", null, this.props.taptip.title)) : "");

            var innerStyle = {};

            if (this.props.taptip.hasOwnProperty("padding"))
            {
                innerStyle = {
                    padding: this.props.taptip.padding
                }
            } 

		    taptip = (
		    	React.createElement("div", {className: tapTipClasses, 
	                style: taptipStyle}, 
	                React.createElement("div", {className: "taptip_inner", 
                        style: innerStyle}, 
	                    React.createElement("div", {className: "opaque_inner"}, 
	                        taptipTitle, 
	                        taptipBreak, 
	                        this.props.taptip.content
	                    )
	                )
	            )
        	);

        	clickAction = (this.props.taptip.action ? this.props.taptip.action : this._showTaptip);
        }
        else if (this.props.clickAction)
        {
        	clickAction = this.props.clickAction;
        }

        var controlButtonClass = (this.props.controlclass ? this.props.controlclass : "control_button");

        return (
            React.createElement("div", {className: "inlineBlock"}, 
            	taptip, 
            	tooltip, 
                React.createElement("div", {className: controlButtonClass, 
                    onClick: clickAction, 
                    onMouseEnter: tooltipShow, 
                    onMouseLeave: tooltipHide, 
                    style: selectedStyle}, 
                    React.createElement("div", {className: "centeredDiv"}, 
                        buttonIcon
                    )
                )
            )
        );
    },
});







module.exports = ControlButton;

},{"../action-creators/control-button-action-creators":3,"../stores/control-button-store":48,"react":undefined,"react-router":undefined}],16:[function(require,module,exports){
'use strict';

var React = require('react');

var ControlButton = require('../control-button');
var EditColumnButton = require('./edit-columns-button');
var controlButtonActionCreators = require('../../action-creators/control-button-action-creators');
// var controlButtonStore = require('../../stores/control-button-store');

var CogButton = React.createClass({displayName: "CogButton",
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
        controlButtonActionCreators.hideTaptip("cogControlButton" + this.props.column);
    },
    _onAddColumn: function () {
        this.props.onadd(this.props.item);
        controlButtonActionCreators.hideTaptip("cogControlButton" + this.props.column);
    },
    _onRemoveColumn: function () {
        this.props.onremove(this.props.item);
        controlButtonActionCreators.hideTaptip("cogControlButton" + this.props.column);
    },
    _onEditColumn: function () {
        controlButtonActionCreators.hideTaptip("cogControlButton" + this.props.column);
        controlButtonActionCreators.showTaptip("editControlButton" + this.props.column);
    },
    render: function () {

        var cogBoxContainer = {
            position: "relative"
        };

        var cogBox = (
            React.createElement("div", {style: cogBoxContainer}, 
                React.createElement("ul", {
                    className: "opList"}, 
                    React.createElement("li", {
                        className: "opListItem edit", 
                        onClick: this._onEditColumn}, "Find and Replace"), 
                    React.createElement("li", {
                        className: "opListItem clone", 
                        onClick: this._onCloneColumn}, "Duplicate"), 
                    React.createElement("li", {
                        className: "opListItem add", 
                        onClick: this._onAddColumn}, "Add"), 
                    React.createElement("li", {
                        className: "opListItem remove", 
                        onClick: this._onRemoveColumn}, "Remove")
                )
            ) 
        );

        var cogTaptip = { 
            "content": cogBox,
            "x": 100,
            "y": 24,
            "styles": [{"key": "width", "value": "120px"}],
            "break": "",
            "padding": "0px"
        };

        var columnIndex = this.props.column;

        var cogIcon = (React.createElement("i", {className: "fa fa-cog "}));

        return (
            React.createElement(ControlButton, {
                name: "cogControlButton" + columnIndex, 
                taptip: cogTaptip, 
                controlclass: "cog_button", 
                fontAwesomeIcon: "pencil", 
                closeAction: this._onClose})
        );
    },
});

module.exports = CogButton;


},{"../../action-creators/control-button-action-creators":3,"../control-button":15,"./edit-columns-button":17,"react":undefined}],17:[function(require,module,exports){
'use strict';

var React = require('react');

var ControlButton = require('../control-button');
var controlButtonActionCreators = require('../../action-creators/control-button-action-creators');
// var controlButtonStore = require('../../stores/control-button-store');

var EditColumnButton = React.createClass({displayName: "EditColumnButton",
    getInitialState: function () {
        return getStateFromStores();
    },
    _onFindBoxChange: function (e) {
        var findValue = e.target.value;

        this.setState({ findValue: findValue });        

        this.props.onclear(this.props.column);        
    },
    _onReplaceBoxChange: function (e) {
        var replaceValue = e.target.value;

        this.setState({ replaceValue: replaceValue });
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
        this.setState({ replaceValue: "" });
        controlButtonActionCreators.hideTaptip("editControlButton" + this.props.column);

    },
    _replace: function () {        
        this.props.replace(this.state.findValue, this.state.replaceValue, this.props.column);
    },
    _replaceAll: function () {
        this.props.replaceall(this.state.findValue, this.state.replaceValue, this.props.column);
    },
    render: function () {

        var editBoxContainer = {
            position: "relative"
        };

        var inputStyle = {
            width: "100%",
            marginLeft: "10px",
            fontWeight: "normal"
        }

        var divWidth = {
            width: "85%"
        }

        var clearTooltip = {
            content: "Clear Search",
            x: 50,
            y: 0
        }

        var findTooltip = {
            content: "Find Next",
            x: 100,
            y: 0
        }

        var replaceTooltip = {
            content: "Replace",
            x: 100,
            y: 80
        }

        var replaceAllTooltip = {
            content: "Replace All",
            x: 100,
            y: 80
        }

        var buttonsStyle={
            marginTop: "8px"
        }

        var editBox = (
            React.createElement("div", {style: editBoxContainer}, 
                React.createElement(ControlButton, {
                    fontAwesomeIcon: "ban", 
                    tooltip: clearTooltip, 
                    clickAction: this._onClearEdit}), 
                React.createElement("div", null, 
                    React.createElement("table", null, 
                        React.createElement("tbody", null, 
                            React.createElement("tr", null, 
                                React.createElement("td", {colSpan: "2"}, 
                                    "Find in Column"
                                )
                            ), 
                            React.createElement("tr", null, 
                                React.createElement("td", {width: "70%"}, 
                                    React.createElement("input", {
                                        type: "text", 
                                        style: inputStyle, 
                                        onChange: this._onFindBoxChange, 
                                        value:  this.state.findValue}
                                    )
                                ), 
                                React.createElement("td", null, 
                                    React.createElement("div", {style: buttonsStyle}, 
                                        React.createElement(ControlButton, {
                                            fontAwesomeIcon: "step-forward", 
                                            tooltip: findTooltip, 
                                            clickAction: this._findNext})
                                    )
                                )
                            ), 
                            React.createElement("tr", null, 
                                React.createElement("td", {colSpan: "2"}, 
                                    "Replace With"
                                )
                            ), 
                            React.createElement("tr", null, 
                                React.createElement("td", null, 
                                    React.createElement("input", {
                                        type: "text", 
                                        style: inputStyle, 
                                        onChange: this._onReplaceBoxChange, 
                                        value:  this.state.replaceValue}
                                    )
                                ), 
                                React.createElement("td", null, 
                                    React.createElement("div", {className: "inlineBlock", 
                                            style: buttonsStyle}, 
                                        React.createElement(ControlButton, {
                                            fontAwesomeIcon: "step-forward", 
                                            tooltip: replaceTooltip, 
                                            clickAction: this._replace}), 

                                        React.createElement(ControlButton, {
                                            fontAwesomeIcon: "fast-forward", 
                                            tooltip: replaceAllTooltip, 
                                            clickAction: this._replaceAll})
                                    )
                                )
                            )
                        )
                    )
                )
            ) 
        );

        var editTaptip = { 
            "title": "Search Column", 
            "content": editBox,
            "x": 100,
            "y": 24,
            "styles": [{"key": "width", "value": "250px"}]
        };
        
        var editTooltip = {
            "content": this.props.tooltipMsg,
            "x": 160,
            "y": 0
        };

        var columnIndex = this.props.column;

        

        return (
            React.createElement(ControlButton, {
                name: "editControlButton" + columnIndex, 
                taptip: editTaptip, 
                tooltip: editTooltip, 
                fontAwesomeIcon: "pencil", 
                controlclass: "edit_column_button"})
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


},{"../../action-creators/control-button-action-creators":3,"../control-button":15,"react":undefined}],18:[function(require,module,exports){
'use strict';

var React = require('react');

var ControlButton = require('../control-button');
// var controlButtonStore = require('../../stores/control-button-store');

var FilterPointsButton = React.createClass({displayName: "FilterPointsButton",
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

        var inputStyle = {
            width: "100%",
            marginLeft: "10px",
            fontWeight: "normal"
        }

        var divWidth = {
            width: "85%"
        }

        var clearTooltip = {
            content: "Clear Filter",
            "x": 80,
            "y": 0
        }

        var filterBox = (
            React.createElement("div", {style: filterBoxContainer}, 
                React.createElement(ControlButton, {
                    fontAwesomeIcon: "ban", 
                    tooltip: clearTooltip, 
                    clickAction: this._onClearFilter}), 
                React.createElement("div", {className: "inlineBlock"}, 
                    React.createElement("div", {className: "inlineBlock"}, 
                        React.createElement("span", {className: "fa fa-filter"})
                    ), 
                    React.createElement("div", {className: "inlineBlock", style: divWidth}, 
                        React.createElement("input", {
                            type: "search", 
                            style: inputStyle, 
                            onChange: this._onFilterBoxChange, 
                            value:  this.state.filterValue}
                        )
                    )
                )
            ) 
        );

        var filterTaptip = { 
            "title": "Filter Points", 
            "content": filterBox,
            "xOffset": 60,
            "yOffset": 120,
            "styles": [{"key": "width", "value": "200px"}]
        };

        var filterIcon = (
            React.createElement("i", {className: "fa fa-filter"})
        );
        
        var holdSelect = this.state.filterValue !== "";

        return (
            React.createElement(ControlButton, {
                name: "filterControlButton", 
                taptip: filterTaptip, 
                tooltip: this.props.tooltipMsg, 
                controlclass: "filter_button", 
                staySelected: holdSelect, 
                icon: filterIcon})
        );
    },
});

function getStateFromStores() {
    return {
        filterValue: ""
    };
}

module.exports = FilterPointsButton;


},{"../control-button":15,"react":undefined}],19:[function(require,module,exports){
'use strict';

var $ = require('jquery');
var React = require('react');

var Exchange = require('./exchange');
var consoleStore = require('../stores/console-store');

var Conversation = React.createClass({displayName: "Conversation",
    getInitialState: getStateFromStores,
    componentDidMount: function () {
        var $conversation = $(this.refs.conversation.getDOMNode());

        if ($conversation.prop('scrollHeight') > $conversation.height()) {
            $conversation.scrollTop($conversation.prop('scrollHeight'));
        }

        consoleStore.addChangeListener(this._onChange);
    },
    componentDidUpdate: function () {
        var $conversation = $(this.refs.conversation.getDOMNode());

        $conversation.stop().animate({ scrollTop: $conversation.prop('scrollHeight') }, 500);
    },
    componentWillUnmount: function () {
        consoleStore.removeChangeListener(this._onChange);
    },
    _onChange: function () {
        this.setState(getStateFromStores());
    },
    render: function () {
        return (
            React.createElement("div", {ref: "conversation", className: "conversation"}, 
                this.state.exchanges.map(function (exchange, index) {
                    return (
                        React.createElement(Exchange, {key: index, exchange: exchange})
                    );
                })
            )
        );
    }
});

function getStateFromStores() {
    return { exchanges: consoleStore.getExchanges() };
}

module.exports = Conversation;


},{"../stores/console-store":47,"./exchange":26,"jquery":undefined,"react":undefined}],20:[function(require,module,exports){
'use strict';

var React = require('react');
var Router = require('react-router');

var platformsStore = require('../stores/platforms-store');
var Chart = require('./chart');
var EditChartForm = require('./edit-chart-form');
var modalActionCreators = require('../action-creators/modal-action-creators');

var Dashboard = React.createClass({displayName: "Dashboard",
    getInitialState: getStateFromStores,
    componentDidMount: function () {
        platformsStore.addChangeListener(this._onStoreChange);
    },
    componentWillUnmount: function () {
        platformsStore.removeChangeListener(this._onStoreChange);
    },
    _onStoreChange: function () {
        this.setState(getStateFromStores());
    },
    _onEditChartClick: function (platform, chart) {
        modalActionCreators.openModal(React.createElement(EditChartForm, {platform: platform, chart: chart}));
    },
    render: function () {
        var charts;

        if (!this.state.platforms) {
            charts = (
                React.createElement("p", null, "Loading charts...")
            );
        } else {
            charts = [];

            this.state.platforms
                .sort(function (a, b) {
                    return a.name.toLowerCase().localeCompare(b.name.toLowerCase());
                })
                .forEach(function (platform) {
                    if (!platform.charts) { return; }

                    platform.charts
                        .filter(function (chart) { return chart.pin; })
                        .forEach(function (chart) {
                            var key = [
                                platform.uuid,
                                chart.topic,
                                chart.type,
                            ].join('::');

                            charts.push(
                                React.createElement("div", {key: key, className: "view__item view__item--tile chart"}, 
                                    React.createElement("h3", {className: "chart__title"}, 
                                        React.createElement(Router.Link, {
                                            to: "platform", 
                                            params: {uuid: platform.uuid}
                                        }, 
                                            platform.name
                                        ), 
                                        ": ", chart.topic
                                    ), 
                                    React.createElement(Chart, {
                                        platform: platform, 
                                        chart: chart}
                                    ), 
                                    React.createElement("div", {className: "chart__actions"}, 
                                        React.createElement("a", {
                                            className: "chart__edit", 
                                            onClick: this._onEditChartClick.bind(this, platform, chart)
                                        }, 
                                            "Edit"
                                        )
                                    )
                                )
                            );
                        }, this);
                }, this);

            if (!charts.length) {
                charts = (
                    React.createElement("p", {className: "empty-help"}, 
                        "Pin a platform chart to have it appear on the dashboard"
                    )
                );
            }
        }

        return (
            React.createElement("div", {className: "view"}, 
                React.createElement("h2", null, "Dashboard"), 
                charts
            )
        );
    },
});

function getStateFromStores() {
    return {
        platforms: platformsStore.getPlatforms(),
    };
}

module.exports = Dashboard;


},{"../action-creators/modal-action-creators":5,"../stores/platforms-store":53,"./chart":9,"./edit-chart-form":25,"react":undefined,"react-router":undefined}],21:[function(require,module,exports){
'use strict';

var React = require('react');

var modalActionCreators = require('../action-creators/modal-action-creators');
var platformManagerActionCreators = require('../action-creators/platform-manager-action-creators');
var platformRegistrationStore = require('../stores/platform-registration-store');

var RegisterPlatformForm = React.createClass({displayName: "RegisterPlatformForm",
    getInitialState: function () {
        return getStateFromStores(this);
    },
    componentDidMount: function () {
        platformRegistrationStore.addChangeListener(this._onStoresChange);
    },
    componentWillUnmount: function () {
        platformRegistrationStore.removeChangeListener(this._onStoresChange);
    },
    _onStoresChange: function () {
        this.setState(getStateFromStores());
    },
    _onCancelClick: modalActionCreators.closeModal,
    _onSubmit: function () {
        platformManagerActionCreators.deregisterPlatform(this.props.platform);
    },
    render: function () {
        return (
            React.createElement("form", {className: "register-platform-form", onSubmit: this._onSubmit}, 
                React.createElement("h1", null, "Deregister platform"), 
                React.createElement("p", null, 
                    "Deregister ", React.createElement("strong", null, this.props.platform.name), "?"
                ), 
                React.createElement("div", {className: "form__actions"}, 
                    React.createElement("button", {
                        className: "button button--secondary", 
                        type: "button", 
                        onClick: this._onCancelClick, 
                        autoFocus: true
                    }, 
                        "Cancel"
                    ), 
                    React.createElement("button", {className: "button"}, "Deregister")
                )
            )
        );
    },
});

function getStateFromStores() {
    return { error: platformRegistrationStore.getLastDeregisterError() };
}

module.exports = RegisterPlatformForm;


},{"../action-creators/modal-action-creators":5,"../action-creators/platform-manager-action-creators":7,"../stores/platform-registration-store":52,"react":undefined}],22:[function(require,module,exports){
'use strict';

var React = require('react');
var Router = require('react-router');

var platformsStore = require('../stores/platforms-store');
var devicesActionCreators = require('../action-creators/devices-action-creators');

var DetectDevices = React.createClass({displayName: "DetectDevices",
    getInitialState: function () {
        var state = getStateFromStores();

        state.deviceRangeSelected = true;
        state.selectedProtocol = "udp_ip";
        state.udpPort = "";
        state.deviceStart = "";
        state.deviceEnd = "";
        state.address = "";

        return state;
    },
    componentDidMount: function () {
        // platformsStore.addChangeListener(this._onStoresChange);
    },
    componentWillUnmount: function () {
        // platformsStore.removeChangeListener(this._onStoresChange);
    },
    _onStoresChange: function () {
        this.setState(getStateFromStores());
    },
    _doScan: function () {
        devicesActionCreators.scanForDevices(this.props.platform);
    },
    _cancelScan: function () {
        devicesActionCreators.cancelScan(this.props.platform);
    },
    _continue: function () {
        devicesActionCreators.listDetectedDevices(this.props.platform);
    },
    _onDeviceRangeSelect: function (evt) {
        var deviceRangeSelected = evt.target.checked;
        this.setState({ deviceRangeSelected: deviceRangeSelected });
    },
    _onAddressSelect: function (evt) {
        var addressSelected = evt.target.checked;
        this.setState({ deviceRangeSelected: !addressSelected });
    },
    _onIpSelect: function (evt) {
        var selectedProtocol = evt.target.value;
        this.setState({ selectedProtocol: selectedProtocol });
    },
    _onPortInput: function (evt) {
        var udpPort = evt.target.value;
        this.setState({ udpPort: udpPort });
    },
    _onDeviceStart: function (evt) {
        var deviceStart = evt.target.value;
        this.setState({ deviceStart: deviceStart });
    },
    _onDeviceEnd: function (evt) {
        var deviceEnd = evt.target.value;
        this.setState({ deviceEnd: deviceEnd });
    },
    _onAddress: function (evt) {
        var address = evt.target.value;
        this.setState({ address: address });
    },
    render: function () {        
        
        var devices;

        switch (this.props.action)
        {
            case "start_scan":

                var containerStyle = {
                    width: "400px",
                    height: "400px"
                }

                var progressStyle = {
                    height: "40%",
                    clear: "both",
                    padding: "80px 0px 0px 200px"
                }

                var labelStyle = {
                    fontSize: "24px"
                }

                devices = (
                    React.createElement("div", {style: containerStyle}, 
                        React.createElement("div", {style: progressStyle}, 
                            React.createElement("i", {className: "fa fa-cog fa-spin fa-5x fa-fw margin-bottom"}), 
                            React.createElement("br", null), 
                            React.createElement("div", {style: labelStyle}, 
                                React.createElement("span", null, "Detecting...")
                            )
                        ), 
                        React.createElement("div", {className: "inlineBlock"}, 
                            React.createElement("div", {className: "inlineBlock"}, 
                                React.createElement("button", {onClick: this._cancelScan}, "Cancel")
                            ), 
                            React.createElement("div", {className: "inlineBlock"}, 
                                React.createElement("button", {onClick: this._continue}, "Continue")
                            )
                        )
                    )
                )

                break;
            case "get_scan_settings":

                var selectStyle = {
                    height: "24px",
                    width: "151px"
                }

                var radioStyle = {
                    width: "20px",
                    float: "left",
                    height: "20px",
                    paddingTop: "4px"
                }

                var buttonStyle = {
                    display: (((this.state.deviceRangeSelected 
                                    && this.state.deviceStart !== "" 
                                    && this.state.deviceEnd !== "") || 
                                (!this.state.deviceRangeSelected 
                                    && this.state.address !== "")) &&
                              (this.state.udpPort !== "") ? "block" : "none")
                }

                var addressStyle = {
                    color: (this.state.deviceRangeSelected ? "gray" : "black")
                };

                var deviceRangeStyle = {
                    color: (this.state.deviceRangeSelected ? "black" : "gray")
                };

                devices = (
                    React.createElement("div", {className: "detectDevicesContainer"}, 
                        React.createElement("div", {className: "detectDevicesBox"}, 
                            React.createElement("table", null, 
                                React.createElement("tbody", null, 
                                    React.createElement("tr", null, 
                                        React.createElement("td", {className: "table_label"}, "Network Interface"), 
                                        React.createElement("td", {className: "plain"}, 
                                            React.createElement("select", {
                                                style: selectStyle, 
                                                onChange: this._onIpSelect, 
                                                value: this.state.selectedProtocol}, 
                                                React.createElement("option", {value: "udp_ip"}, "UDP/IP"), 
                                                React.createElement("option", {value: "ipc"}, "IPC"), 
                                                React.createElement("option", {value: "tcp"}, "TCP")
                                            )
                                        )
                                    ), 
                                    React.createElement("tr", null, 
                                        React.createElement("td", {className: "table_label buffer_row"}, "UDP Port"), 
                                        React.createElement("td", {className: "plain buffer_row"}, 
                                            React.createElement("input", {
                                                type: "number", 
                                                onChange: this._onPortInput, 
                                                value: this.state.udpPort})
                                        )
                                    ), 
                                    React.createElement("tr", null, 
                                        React.createElement("td", {className: "table_label"}, 
                                            React.createElement("div", null, 
                                                React.createElement("div", {style: radioStyle}, 
                                                    React.createElement("input", {
                                                        type: "radio", 
                                                        name: "scan_method", 
                                                        onChange: this._onDeviceRangeSelect, 
                                                        checked: this.state.deviceRangeSelected})
                                                ), 
                                                React.createElement("span", {style: deviceRangeStyle}, "Device ID Range")
                                            )
                                        ), 
                                        React.createElement("td", {className: "plain"}, 
                                            React.createElement("input", {
                                                disabled: !this.state.deviceRangeSelected, 
                                                style: deviceRangeStyle, 
                                                type: "number", 
                                                onChange: this._onDeviceStart, 
                                                value: this.state.deviceStart}), " ", 
                                            React.createElement("input", {
                                                disabled: !this.state.deviceRangeSelected, 
                                                style: deviceRangeStyle, 
                                                type: "number", 
                                                onChange: this._onDeviceEnd, 
                                                value: this.state.deviceEnd})
                                        )
                                    ), 
                                    React.createElement("tr", null, 
                                        React.createElement("td", {className: "table_label"}, 
                                            React.createElement("div", null, 
                                                React.createElement("div", {style: radioStyle}, 
                                                    React.createElement("input", {
                                                        type: "radio", 
                                                        name: "scan_method", 
                                                        onChange: this._onAddressSelect, 
                                                        checked: !this.state.deviceRangeSelected})
                                                ), 
                                                React.createElement("span", {style: addressStyle}, "Address")
                                            )
                                        ), 
                                        React.createElement("td", {className: "plain"}, 
                                            React.createElement("input", {
                                                disabled: this.state.deviceRangeSelected, 
                                                style: addressStyle, 
                                                type: "text", 
                                                onChange: this._onAddress, 
                                                value: this.state.address})
                                        )
                                    )
                                )
                            )
                        ), 
                        React.createElement("div", {
                            style: buttonStyle}, 
                            React.createElement("button", {onClick: this._doScan}, "Scan")
                        )
                        
                    )
                )


                break;
        }

        return (
            React.createElement("div", null, 
                devices
            )
        );
    },
});

function getStateFromStores() {
    return {
        platform: { name: "PNNL", uuid: "99090"}
    };
}

module.exports = DetectDevices;


},{"../action-creators/devices-action-creators":4,"../stores/platforms-store":53,"react":undefined,"react-router":undefined}],23:[function(require,module,exports){
'use strict';

var React = require('react');
var Router = require('react-router');

var devicesActionCreators = require('../action-creators/devices-action-creators');
var devicesStore = require('../stores/devices-store');

var DevicesFound = React.createClass({displayName: "DevicesFound",
    getInitialState: function () {
        return getStateFromStores();
    },
    componentDidMount: function () {
        // platformsStore.addChangeListener(this._onStoresChange);
    },
    componentWillUnmount: function () {
        // platformsStore.removeChangeListener(this._onStoresChange);
    },
    _onStoresChange: function () {
        this.setState(getStateFromStores());
    },
    _configureDevice: function (device) {
        devicesActionCreators.configureDevice(device);
    },
    render: function () {        
        
        var devices = 
            this.state.devices.map(function (device) {

                var buttonStyle = {
                    height: "24px",
                    lineHeight: "18px"
                }

                var tds = device.map(function (d) {
                                return (React.createElement("td", {className: "plain"},  d.value))
                            });
                return (
                    React.createElement("tr", null, 
                         tds, 

                        React.createElement("td", {className: "plain"}, 
                            React.createElement("button", {
                                onClick: this._configureDevice.bind(this, device), 
                                style: buttonStyle}, "Configure")
                        )
                    )
                );

            }, this); 

        var ths = this.state.devices[0].map(function (d) {
                        return (React.createElement("th", {className: "plain"}, d.label)); 
                    });    

        return (
            React.createElement("div", {className: "devicesFoundContainer"}, 
                React.createElement("div", {className: "devicesFoundBox"}, 
                    React.createElement("table", null, 
                        React.createElement("tbody", null, 
                            React.createElement("tr", null, 
                                 ths, 
                                React.createElement("th", {className: "plain"})
                            ), 
                            devices
                        )
                    )
                )
            )
        );
    },
});

function getStateFromStores() {
    return {
        devices: [
            [ 
                { key: "address", label: "Address", value: "Address 192.168.1.42" }, 
                { key: "deviceId", label: "Device ID", value: "548" }, 
                { key: "description", label: "Description", value: "Temperature sensor" }, 
                { key: "vendorId", label: "Vendor ID", value: "18" }, 
                { key: "vendor", label: "Vendor", value: "Siemens" }
            ],
            [ 
                { key: "address", label: "Address", value: "RemoteStation 1002:11" }, 
                { key: "deviceId", label: "Device ID", value: "33" }, 
                { key: "description", label: "Description", value: "Actuator 3-pt for zone control" }, 
                { key: "vendorId", label: "Vendor ID", value: "12" }, 
                { key: "vendor", label: "Vendor", value: "Alerton" }
            ]
        ]
    };
}

module.exports = DevicesFound;


},{"../action-creators/devices-action-creators":4,"../stores/devices-store":49,"react":undefined,"react-router":undefined}],24:[function(require,module,exports){
'use strict';

var React = require('react');
var Router = require('react-router');

// var platformsStore = require('../stores/platforms-store');
var DetectDevices = require('./detect-devices');
var DevicesFound = require('./devices-found');
var ConfigureDevice = require('./configure-device');
var ConfigureRegistry = require('./configure-registry');
var devicesStore = require('../stores/devices-store');

var Devices = React.createClass({displayName: "Devices",
    // mixins: [Router.State],
    getInitialState: function () {
        return getStateFromStores();
    },
    componentDidMount: function () {
        devicesStore.addChangeListener(this._onStoresChange);
    },
    componentWillUnmount: function () {
        devicesStore.removeChangeListener(this._onStoresChange);
    },
    _onStoresChange: function () {
        this.setState(getStateFromStores());
    },
    render: function () {

        var view_component;
        var platform = this.state.platform;

        switch (this.state.view)
        {
            case "Detect Devices":

                view_component = (React.createElement(DetectDevices, {platform: this.state.platform, action: this.state.action}))

                break;
            case "Configure Devices":
                view_component = (React.createElement(DevicesFound, {platform: this.state.platform, action: this.state.action}))
                break;
            case "Configure Device":
                view_component = (React.createElement(ConfigureDevice, {device: this.state.device, action: this.state.action}))
                break;
            case "Registry Configuration":
                view_component = (React.createElement(ConfigureRegistry, {device: this.state.device, action: this.state.action}))
                break;
        }
        
        return (
            React.createElement("div", {className: "view"}, 
                React.createElement("h2", null, this.state.view), 
                React.createElement("div", null, 
                    React.createElement("label", null, React.createElement("b", null, "Instance: ")), React.createElement("label", null, platform.name), 
                    view_component
                
                )
                
            )
        );
    },
});


function getStateFromStores() {

    var deviceState = devicesStore.getState();
    
    return {
        // platform: platformsStore.getPlatform(component.getParams().uuid),
        platform: { name: "PNNL", uuid: "99090"},
        view: deviceState.view,
        action: deviceState.action,
        device: deviceState.device
    };
}

module.exports = Devices;


},{"../stores/devices-store":49,"./configure-device":11,"./configure-registry":12,"./detect-devices":22,"./devices-found":23,"react":undefined,"react-router":undefined}],25:[function(require,module,exports){
'use strict';

var React = require('react');

var modalActionCreators = require('../action-creators/modal-action-creators');
var platformActionCreators = require('../action-creators/platform-action-creators');

var EditChartForm = React.createClass({displayName: "EditChartForm",
    getInitialState: function () {
        var state = {};

        for (var prop in this.props.chart) {
            state[prop] = this.props.chart[prop];
        }

        return state;
    },
    _onPropChange: function (e) {
        var state = {};

        switch (e.target.type) {
        case 'checkbox':
            state[e.target.id] = e.target.checked;
            break;
        case 'number':
            state[e.target.id] = parseFloat(e.target.value);
            break;
        default:
            state[e.target.id] = e.target.value;
        }

        this.setState(state);
    },
    _onCancelClick: modalActionCreators.closeModal,
    _onSubmit: function () {
        platformActionCreators.saveChart(this.props.platform, this.props.chart, this.state);
    },
    render: function () {
        var typeOptions;

        switch (this.state.type) {
        case 'line':
            typeOptions = (
                React.createElement("div", {className: "form__control-group"}, 
                    React.createElement("label", null, "Y-axis range"), 
                    React.createElement("label", {htmlFor: "min"}, "Min:"), " ", 
                    React.createElement("input", {
                        className: "form__control form__control--inline", 
                        type: "number", 
                        id: "min", 
                        onChange: this._onPropChange, 
                        value: this.state.min, 
                        placeholder: "auto"}
                    ), " ", 
                    React.createElement("label", {htmlFor: "max"}, "Max:"), " ", 
                    React.createElement("input", {
                        className: "form__control form__control--inline", 
                        type: "number", 
                        id: "max", 
                        onChange: this._onPropChange, 
                        value: this.state.max, 
                        placeholder: "auto"}
                    ), React.createElement("br", null), 
                    React.createElement("span", {className: "form__control-help"}, 
                        "Omit either to determine from data"
                    )
                )
            );
        }

        return (
            React.createElement("form", {className: "edit-chart-form", onSubmit: this._onSubmit}, 
                React.createElement("h1", null, this.props.chart ? 'Edit' : 'Add', " chart"), 
                this.state.error && (
                    React.createElement("div", {className: "error"}, this.state.error.message)
                ), 
                React.createElement("div", {className: "form__control-group"}, 
                    React.createElement("label", {htmlFor: "topic"}, "Platform"), 
                    this.props.platform.name, " (", this.props.platform.uuid, ")"
                ), 
                React.createElement("div", {className: "form__control-group"}, 
                    React.createElement("label", {htmlFor: "topic"}, "Topic"), 
                    React.createElement("input", {
                        className: "form__control form__control--block", 
                        type: "text", 
                        id: "topic", 
                        onChange: this._onPropChange, 
                        value: this.state.topic, 
                        placeholder: "e.g. some/published/topic", 
                        required: true}
                    )
                ), 
                React.createElement("div", {className: "form__control-group"}, 
                    React.createElement("label", null, "Dashboard"), 
                    React.createElement("input", {
                        className: "form__control form__control--inline", 
                        type: "checkbox", 
                        id: "pin", 
                        onChange: this._onPropChange, 
                        checked: this.state.pin}
                    ), " ", 
                    React.createElement("label", {htmlFor: "pin"}, "Pin to dashboard")
                ), 
                React.createElement("div", {className: "form__control-group"}, 
                    React.createElement("label", {htmlFor: "refreshInterval"}, "Refresh interval (ms)"), 
                    React.createElement("input", {
                        className: "form__control form__control--inline", 
                        type: "number", 
                        id: "refreshInterval", 
                        onChange: this._onPropChange, 
                        value: this.state.refreshInterval, 
                        min: "250", 
                        step: "1", 
                        placeholder: "disabled"}
                    ), 
                    React.createElement("span", {className: "form__control-help"}, 
                        "Omit to disable"
                    )
                ), 
                React.createElement("div", {className: "form__control-group"}, 
                    React.createElement("label", {htmlFor: "type"}, "Chart type"), 
                    React.createElement("select", {
                        id: "type", 
                        onChange: this._onPropChange, 
                        value: this.state.type, 
                        autoFocus: true, 
                        required: true
                    }, 
                        React.createElement("option", {value: ""}, "-- Select type --"), 
                        React.createElement("option", {value: "line"}, "Line")
                    )
                ), 
                typeOptions, 
                React.createElement("div", {className: "form__actions"}, 
                    React.createElement("button", {
                        className: "button button--secondary", 
                        type: "button", 
                        onClick: this._onCancelClick
                    }, 
                        "Cancel"
                    ), 
                    React.createElement("button", {
                        className: "button", 
                        disabled: !this.state.topic || !this.state.type
                    }, 
                        "Save"
                    )
                )
            )
        );
    },
});

module.exports = EditChartForm;


},{"../action-creators/modal-action-creators":5,"../action-creators/platform-action-creators":6,"react":undefined}],26:[function(require,module,exports){
'use strict';

var React = require('react');

var Exchange = React.createClass({displayName: "Exchange",
    _formatTime: function (time) {
        var d = new Date();

        d.setTime(time);

        return d.toLocaleString();
    },
    _formatMessage: function (message) {
        return JSON.stringify(message, null, '    ');
    },
    render: function () {
        var exchange = this.props.exchange;
        var classes = ['response'];
        var responseText;

        if (!exchange.completed) {
            classes.push('response--pending');
            responseText = 'Waiting for response...';
        } else if (exchange.error) {
            classes.push('response--error');
            responseText = exchange.error.message;
        } else {
            if (exchange.response.error) {
                classes.push('response--error');
            }

            responseText = this._formatMessage(exchange.response);
        }

        return (
            React.createElement("div", {className: "exchange"}, 
                React.createElement("div", {className: "request"}, 
                    React.createElement("div", {className: "time"}, this._formatTime(exchange.initiated)), 
                    React.createElement("pre", null, this._formatMessage(exchange.request))
                ), 
                React.createElement("div", {className: classes.join(' ')}, 
                    exchange.completed && React.createElement("div", {className: "time"}, this._formatTime(exchange.completed)), 
                    React.createElement("pre", null, responseText)
                )
            )
        );
    }
});

module.exports = Exchange;


},{"react":undefined}],27:[function(require,module,exports){
'use strict';

var d3 = require('d3');
var moment = require('moment');
var React = require('react');

var LineChart = React.createClass({displayName: "LineChart",
    getInitialState: function () {
        var initialState = {
            data: this.props.data,
            xDates: false,
        };

        if (this.props.data.length &&
            typeof this.props.data[0][0] === 'string' &&
            Date.parse(this.props.data[0][0] + 'Z')) {
            initialState.data = this.props.data.map(function (value) {
                return[Date.parse(value[0] + 'Z'), value[1]];
            });
            initialState.xDates = true;
        }

        return initialState;
    },
    componentDidMount: function () {
        this._updateSize();
        window.addEventListener('resize', this._onResize);
    },
    componentWillReceiveProps: function (newProps) {
        var newState = {
            data: newProps.data,
            xDates: false,
        };

        if (newProps.data.length &&
            typeof newProps.data[0][0] === 'string' &&
            Date.parse(newProps.data[0][0] + 'Z')) {
            newState.data = newProps.data.map(function (value) {
                return[Date.parse(value[0] + 'Z'), value[1]];
            });
            newState.xDates = true;
        }

        this.setState(newState);
    },
    componentWillUpdate: function () {
        this._updateSize();
    },
    componentWillUnmount: function () {
        window.removeEventListener('resize', this._onResize);
    },
    _onResize: function () {
        this.forceUpdate();
    },
    _updateSize: function () {
        var computedStyles = window.getComputedStyle(React.findDOMNode(this.refs.svg));
        this._width = parseInt(computedStyles.width, 10);
        this._height = parseInt(computedStyles.height, 10);
    },
    render: function () {
        var contents = [];

        if (this._width && this._height) {
            contents.push(
                React.createElement("path", {
                    key: "xAxis", 
                    className: "axis", 
                    strokeLinecap: "square", 
                    d: 'M3,' + (this._height - 19) + 'L' + (this._width - 3) + ',' + (this._height - 19)}
                )
            );

            contents.push(
                React.createElement("path", {
                    key: "yAxis", 
                    className: "axis", 
                    strokeLinecap: "square", 
                    d: 'M3,17L3,' + (this._height - 19)}
                )
            );

            if (!this.state.data.length) {
                contents.push(
                    React.createElement("text", {
                        key: "noData", 
                        className: "no-data-text", 
                        x: this._width / 2, 
                        y: this._height / 2, 
                        textAnchor: "middle"
                    }, 
                        "No data available"
                    )
                );
            } else {
                var xRange = d3.extent(this.state.data, function (d) { return d[0]; });
                var yMin = (this.props.chart.min === 0 || this.props.chart.min) ?
                    this.props.chart.min : d3.min(this.state.data, function (d) { return d[1]; });
                var yMax = (this.props.chart.max === 0 || this.props.chart.max) ?
                    this.props.chart.max : d3.max(this.state.data, function (d) { return d[1]; });

                var x = d3.scale.linear()
                    .range([4, this._width - 4])
                    .domain(xRange);
                var y = d3.scale.linear()
                    .range([this._height - 20, 18])
                    .domain([yMin, yMax]);

                var line = d3.svg.line()
                    .x(function (d) { return x(d[0]); })
                    .y(function (d) { return y(d[1]); });

                contents.push(
                    React.createElement("text", {
                        key: "xMinLabel", 
                        className: "label", 
                        x: "2", 
                        y: this._height - 4
                    }, 
                        this.state.xDates ? moment(xRange[0]).fromNow() : xRange[0]
                    )
                );

                contents.push(
                    React.createElement("text", {
                        key: "xMaxLabel", 
                        className: "label", 
                        x: this._width - 2, 
                        y: this._height - 4, 
                        textAnchor: "end"
                    }, 
                        this.state.xDates ? moment(xRange[1]).fromNow() : xRange[1]
                    )
                );

                contents.push(
                    React.createElement("text", {
                        key: "yMaxLabel", 
                        className: "label", x: "2", y: "10"}, 
                        yMax
                    )
                );

                contents.push(
                    React.createElement("path", {
                        key: "line", 
                        className: "line", 
                        strokeLinecap: "round", 
                        d: line(this.state.data)}
                    )
                );

                this.state.data.forEach(function (d, index) {
                    var text;

                    if (this.state.xDates) {
                        text = d[1]  + ' @ ' + moment(d[0]).format('MMM D, YYYY h:mm:ss A');
                    } else {
                        text = d.join(', ');
                    }

                    contents.push(
                        React.createElement("g", {key: 'point' + index, className: "dot"}, 
                            React.createElement("circle", {className: "outer", cx: x(d[0]), cy: y(d[1]), r: "4"}), 
                            React.createElement("circle", {className: "inner", cx: x(d[0]), cy: y(d[1]), r: "2"}), 
                            React.createElement("text", {
                                x: this._width / 2, 
                                y: "10", 
                                textAnchor: "middle"
                            }, 
                                text
                            )
                        )
                    );
                }, this);
            }
        }

        return (
            React.createElement("svg", {className: "chart__svg chart__svg--line", ref: "svg"}, 
                contents
            )
        );
    },
});

module.exports = LineChart;


},{"d3":undefined,"moment":undefined,"react":undefined}],28:[function(require,module,exports){
'use strict';

var React = require('react');
var Router = require('react-router');

var loginFormStore = require('../stores/login-form-store');
var platformManagerActionCreators = require('../action-creators/platform-manager-action-creators');

var LoginForm = React.createClass({displayName: "LoginForm",
    getInitialState: getStateFromStores,
    componentDidMount: function () {
        loginFormStore.addChangeListener(this._onStoresChange);
    },
    componentWillUnmount: function () {
        loginFormStore.removeChangeListener(this._onStoresChange);
    },
    _onStoresChange: function () {
        this.setState(getStateFromStores());
    },
    _onUsernameChange: function (e) {
        this.setState({
            username: e.target.value,
            error: null,
        });
    },
    _onPasswordChange: function (e) {
        this.setState({
            password: e.target.value,
            error: null,
        });
    },
    _onSubmit: function (e) {
        e.preventDefault();
        platformManagerActionCreators.requestAuthorization(
            this.state.username,
            this.state.password
        );
    },
    render: function () {
        return (
            React.createElement("form", {className: "login-form", onSubmit: this._onSubmit}, 
                React.createElement("input", {
                    className: "login-form__field", 
                    type: "text", 
                    placeholder: "Username", 
                    autoFocus: true, 
                    onChange: this._onUsernameChange}
                ), 
                React.createElement("input", {
                    className: "login-form__field", 
                    type: "password", 
                    placeholder: "Password", 
                    onChange: this._onPasswordChange}
                ), 
                React.createElement("input", {
                    className: "button login-form__submit", 
                    type: "submit", 
                    value: "Log in", 
                    disabled: !this.state.username || !this.state.password}
                ), 
                this.state.error ? (
                    React.createElement("span", {className: "login-form__error error"}, 
                        this.state.error.message, " (", this.state.error.code, ")"
                    )
                ) : null
            )
        );
    }
});

function getStateFromStores() {
    return { error: loginFormStore.getLastError() };
}

module.exports = LoginForm;


},{"../action-creators/platform-manager-action-creators":7,"../stores/login-form-store":50,"react":undefined,"react-router":undefined}],29:[function(require,module,exports){
'use strict';

var React = require('react');

var modalActionCreators = require('../action-creators/modal-action-creators');

var Modal = React.createClass({displayName: "Modal",
	_onClick: function (e) {
		if (e.target === e.currentTarget) {
			modalActionCreators.closeModal();
		}
	},
	render: function () {
		return (
			React.createElement("div", {className: "modal__overlay", onClick: this._onClick}, 
				React.createElement("div", {className: "modal__dialog"}, 
					this.props.children
				)
			)
		);
	},
});

module.exports = Modal;


},{"../action-creators/modal-action-creators":5,"react":undefined}],30:[function(require,module,exports){
'use strict';

var React = require('react');
var Router = require('react-router');

var platformManagerActionCreators = require('../action-creators/platform-manager-action-creators');
var authorizationStore = require('../stores/authorization-store');

var Navigation = React.createClass({displayName: "Navigation",
    getInitialState: getStateFromStores,
    componentDidMount: function () {
        authorizationStore.addChangeListener(this._onStoreChange);
    },
    componentWillUnmount: function () {
        authorizationStore.removeChangeListener(this._onStoreChange);
    },
    _onStoreChange: function () {
        this.setState(getStateFromStores());
    },
    _onLogOutClick: function () {
        platformManagerActionCreators.clearAuthorization();
    },
    render: function () {
        var navItems;

        if (this.state.loggedIn) {
            navItems = ['Dashboard', 'Platforms'].map(function (navItem) {
                var route = navItem.toLowerCase();

                return (
                    React.createElement(Router.Link, {
                        key: route, 
                        to: route, 
                        className: "navigation__item", 
                        activeClassName: "navigation__item--active"
                    }, 
                        navItem
                    )
                );
            });

            navItems.push(
                React.createElement("a", {
                    key: "logout", 
                    className: "navigation__item", 
                    tabIndex: "0", 
                    onClick: this._onLogOutClick
                }, 
                    "Log out"
                )
            );
        }

        return (
            React.createElement("nav", {className: "navigation"}, 
                React.createElement("h1", {className: "logo"}, 
                    React.createElement("span", {className: "logo__name"}, "VOLTTRON"), 
                    React.createElement("span", {className: "logo__tm"}, "™"), 
                    React.createElement("span", {className: "logo__central"}, " Central"), 
                    React.createElement("span", {className: "logo__beta"}, "BETA")
                ), 
                navItems
            )
        );
    }
});

function getStateFromStores() {
    return {
        loggedIn: !!authorizationStore.getAuthorization(),
    };
}

module.exports = Navigation;


},{"../action-creators/platform-manager-action-creators":7,"../stores/authorization-store":46,"react":undefined,"react-router":undefined}],31:[function(require,module,exports){
'use strict';

var React = require('react');

var PageNotFound = React.createClass({displayName: "PageNotFound",
    render: function () {
        return (
            React.createElement("div", {className: "view"}, 
                React.createElement("h2", null, "Page not found")
            )
        );
    },
});

module.exports = PageNotFound;


},{"react":undefined}],32:[function(require,module,exports){
'use strict';

var $ = require('jquery');
var React = require('react');
var Router = require('react-router');

var authorizationStore = require('../stores/authorization-store');
var Console = require('./console');
var consoleActionCreators = require('../action-creators/console-action-creators');
var consoleStore = require('../stores/console-store');
var Modal = require('./modal');
var modalActionCreators = require('../action-creators/modal-action-creators');
var modalStore = require('../stores/modal-store');
var Navigation = require('./navigation');
var platformManagerActionCreators = require('../action-creators/platform-manager-action-creators');

var PlatformManager = React.createClass({displayName: "PlatformManager",
    mixins: [Router.Navigation, Router.State],
    getInitialState: getStateFromStores,
    componentWillMount: function () {
        platformManagerActionCreators.initialize();
    },
    componentDidMount: function () {
        authorizationStore.addChangeListener(this._onStoreChange);
        consoleStore.addChangeListener(this._onStoreChange);
        modalStore.addChangeListener(this._onStoreChange);
        this._doModalBindings();
    },
    componentDidUpdate: function () {
        this._doModalBindings();
    },
    _doModalBindings: function () {
        if (this.state.modalContent) {
            window.addEventListener('keydown', this._closeModal);
            this._focusDisabled = $('input,select,textarea,button,a', React.findDOMNode(this.refs.main)).attr('tabIndex', -1);
        } else {
            window.removeEventListener('keydown', this._closeModal);
            if (this._focusDisabled) {
                this._focusDisabled.removeAttr('tabIndex');
                delete this._focusDisabled;
            }
        }
    },
    componentWillUnmount: function () {
        authorizationStore.removeChangeListener(this._onStoreChange);
        consoleStore.removeChangeListener(this._onStoreChange);
        modalStore.removeChangeListener(this._onStoreChange);
        this._modalCleanup();
    },
    _onStoreChange: function () {
        this.setState(getStateFromStores());
    },
    _onToggleClick: function () {
        consoleActionCreators.toggleConsole();
    },
    _closeModal: function (e) {
        if (e.keyCode === 27) {
            modalActionCreators.closeModal();
        }
    },
    render: function () {
        var classes = ['platform-manager'];
        var modal;

        if (this.state.consoleShown) {
            classes.push('platform-manager--console-open');
        }

        classes.push(this.state.loggedIn ?
            'platform-manager--logged-in' : 'platform-manager--not-logged-in');

        if (this.state.modalContent) {
            classes.push('platform-manager--modal-open');
            modal = (
                React.createElement(Modal, null, this.state.modalContent)
            );
        }

        return (
            React.createElement("div", {className: classes.join(' ')}, 
                modal, 
                React.createElement("div", {ref: "main", className: "main"}, 
                    React.createElement(Navigation, null), 
                    React.createElement(Router.RouteHandler, null)
                ), 
                React.createElement("input", {
                    className: "toggle", 
                    type: "button", 
                    value: 'Console ' + (this.state.consoleShown ? '\u25bc' : '\u25b2'), 
                    onClick: this._onToggleClick}
                ), 
                this.state.consoleShown && React.createElement(Console, {className: "console"})
            )
        );
    },
});

function getStateFromStores() {
    return {
        consoleShown: consoleStore.getConsoleShown(),
        loggedIn: !!authorizationStore.getAuthorization(),
        modalContent: modalStore.getModalContent(),
    };
}

module.exports = PlatformManager;


},{"../action-creators/console-action-creators":2,"../action-creators/modal-action-creators":5,"../action-creators/platform-manager-action-creators":7,"../stores/authorization-store":46,"../stores/console-store":47,"../stores/modal-store":51,"./console":14,"./modal":29,"./navigation":30,"jquery":undefined,"react":undefined,"react-router":undefined}],33:[function(require,module,exports){
'use strict';

var React = require('react');
var Router = require('react-router');

var AgentRow = require('./agent-row');
var Chart = require('./chart');
var EditChartForm = require('./edit-chart-form');
var ConfirmForm = require('./confirm-form');
var modalActionCreators = require('../action-creators/modal-action-creators');
var platformActionCreators = require('../action-creators/platform-action-creators');
var platformsStore = require('../stores/platforms-store');

var Platform = React.createClass({displayName: "Platform",
    mixins: [Router.State],
    getInitialState: function () {
        return getStateFromStores(this);
    },
    componentDidMount: function () {
        platformsStore.addChangeListener(this._onStoresChange);
    },
    componentWillUnmount: function () {
        platformsStore.removeChangeListener(this._onStoresChange);
        if (this.state.error) {
            platformActionCreators.clearPlatformError(this.state.platform);
        }
    },
    _onStoresChange: function () {
        this.setState(getStateFromStores(this));
    },
    _onEditChartClick: function (platform, chart) {
        modalActionCreators.openModal(React.createElement(EditChartForm, {platform: platform, chart: chart}));
    },
    _onDeleteChartClick: function (platform, chart) {
        modalActionCreators.openModal(
            React.createElement(ConfirmForm, {
                promptTitle: "Delete chart", 
                promptText: 'Delete ' + chart.type + ' chart for ' + chart.topic + '?', 
                confirmText: "Delete", 
                onConfirm: platformActionCreators.deleteChart.bind(null, platform, chart)}
            )
        );
    },
    _onAddChartClick: function (platform) {
        modalActionCreators.openModal(React.createElement(EditChartForm, {platform: platform}));
    },
    _onFileChange: function (e) {
        if (!e.target.files.length) { return; }

        var reader = new FileReader();
        var platform = this.state.platform;
        var files = e.target.files;
        var parsedFiles = [];

        function doFile(index) {
            if (index === files.length) {
                platformActionCreators.installAgents(platform, parsedFiles);
                return;
            }

            reader.onload = function () {
                parsedFiles.push({
                    file_name: files[index].name,
                    file: reader.result,
                });
                doFile(index + 1);
            };

            reader.readAsDataURL(files[index]);
        }

        doFile(0);
    },
    render: function () {
        var platform = this.state.platform;

        if (!platform) {
            return (
                React.createElement("div", {className: "view"}, 
                    React.createElement("h2", null, 
                        React.createElement(Router.Link, {to: "platforms"}, "Platforms"), 
                        " / ", 
                        this.getParams().uuid
                    ), 
                    React.createElement("p", null, "Platform not found.")
                )
            );
        }

        var charts;
        var agents;

        if (!platform.charts) {
            charts = (
                React.createElement("p", null, "Loading charts...")
            );
        } else {
            charts = platform.charts.map(function (chart) {
                var key = [
                    platform.uuid,
                    chart.topic,
                    chart.type,
                ].join('::');

                return (
                    React.createElement("div", {key: key, className: "view__item view__item--tile chart"}, 
                        React.createElement("h4", {className: "chart__title"}, chart.topic), 
                        React.createElement(Chart, {
                            platform: platform, 
                            chart: chart}
                        ), 
                        React.createElement("div", {className: "chart__actions"}, 
                            React.createElement("a", {onClick: this._onEditChartClick.bind(this, platform, chart)}, 
                                "Edit"
                            ), 
                            React.createElement("a", {onClick: this._onDeleteChartClick.bind(this, platform, chart)}, 
                                "Delete"
                            )
                        )
                    )
                );
            }, this);
        }

        if (!platform.agents) {
            agents = (
                React.createElement("p", null, "Loading agents...")
            );
        } else if (!platform.agents.length) {
            agents = (
                React.createElement("p", null, "No agents installed.")
            );
        } else {
            agents = (
                React.createElement("table", null, 
                    React.createElement("thead", null, 
                        React.createElement("tr", null, 
                            React.createElement("th", null, "Agent"), 
                            React.createElement("th", null, "UUID"), 
                            React.createElement("th", null, "Status"), 
                            React.createElement("th", null, "Action")
                        )
                    ), 
                    React.createElement("tbody", null, 
                        platform.agents
                            .sort(function (a, b) {
                                if (a.name.toLowerCase() > b.name.toLowerCase()) { return 1; }
                                if (a.name.toLowerCase() < b.name.toLowerCase()) { return -1; }
                                return 0;
                            })
                            .map(function (agent) {
                                return (
                                    React.createElement(AgentRow, {
                                        key: agent.uuid, 
                                        platform: platform, 
                                        agent: agent})
                                );
                            })
                        
                    )
                )
            );
        }

        return (
            React.createElement("div", {className: "view"}, 
                this.state.error && (
                    React.createElement("div", {className: "view__error error"}, this.state.error)
                ), 
                React.createElement("h2", null, 
                    React.createElement(Router.Link, {to: "platforms"}, "Platforms"), 
                    " / ", 
                    platform.name, " (", platform.uuid, ")"
                ), 
                React.createElement("h3", null, "Charts"), 
                charts, 
                React.createElement("div", null, 
                    React.createElement("button", {
                        className: "button", 
                        onClick: this._onAddChartClick.bind(null, this.state.platform)
                    }, 
                        "Add chart"
                    )
                ), 
                React.createElement("h3", null, "Agents"), 
                agents, 
                React.createElement("h3", null, "Install agents"), 
                React.createElement("input", {type: "file", multiple: true, onChange: this._onFileChange})
            )
        );
    },
});

function getStateFromStores(component) {
    return {
        platform: platformsStore.getPlatform(component.getParams().uuid),
        error: platformsStore.getLastError(component.getParams().uuid),
    };
}

module.exports = Platform;


},{"../action-creators/modal-action-creators":5,"../action-creators/platform-action-creators":6,"../stores/platforms-store":53,"./agent-row":8,"./chart":9,"./confirm-form":13,"./edit-chart-form":25,"react":undefined,"react-router":undefined}],34:[function(require,module,exports){
'use strict';

var React = require('react');
var Router = require('react-router');

var modalActionCreators = require('../action-creators/modal-action-creators');
var platformsStore = require('../stores/platforms-store');
var RegisterPlatformForm = require('../components/register-platform-form');
var DeregisterPlatformConfirmation = require('../components/deregister-platform-confirmation');

var Platforms = React.createClass({displayName: "Platforms",
    getInitialState: getStateFromStores,
    componentDidMount: function () {
        platformsStore.addChangeListener(this._onStoresChange);
    },
    componentWillUnmount: function () {
        platformsStore.removeChangeListener(this._onStoresChange);
    },
    _onStoresChange: function () {
        this.setState(getStateFromStores());
    },
    _onRegisterClick: function () {
        modalActionCreators.openModal(React.createElement(RegisterPlatformForm, null));
    },
    _onDeregisterClick: function (platform) {
        modalActionCreators.openModal(React.createElement(DeregisterPlatformConfirmation, {platform: platform}));
    },
    render: function () {
        var platforms;

        if (!this.state.platforms) {
            platforms = (
                React.createElement("p", null, "Loading platforms...")
            );
        } else if (!this.state.platforms.length) {
            platforms = (
                React.createElement("p", null, "No platforms found.")
            );
        } else {
            platforms = this.state.platforms
                .sort(function (a, b) {
                    if (a.name.toLowerCase() > b.name.toLowerCase()) { return 1; }
                    if (a.name.toLowerCase() < b.name.toLowerCase()) { return -1; }
                    return 0;
                })
                .map(function (platform) {
                    var status = [platform.uuid];

                    if (platform.agents) {
                        var running = 0;
                        var stopped = 0;

                        platform.agents.forEach(function (agent) {
                            if (agent.process_id !== null) {
                                if (agent.return_code === null) {
                                    running++;
                                } else {
                                    stopped++;
                                }
                            }
                        });

                        status.push('Agents: ' + running + ' running, ' + stopped + ' stopped, ' + platform.agents.length + ' installed');
                    }

                    return (
                        React.createElement("div", {
                            key: platform.uuid, 
                            className: "view__item view__item--list"
                        }, 
                            React.createElement("h3", null, 
                                React.createElement(Router.Link, {
                                    to: "platform", 
                                    params: {uuid: platform.uuid}
                                }, 
                                    platform.name
                                )
                            ), 
                            React.createElement("button", {
                                className: "deregister-platform", 
                                onClick: this._onDeregisterClick.bind(this, platform), 
                                title: "Deregister platform"
                            }, 
                                "×"
                            ), 
                            React.createElement("code", null, status.join(' | '))
                        )
                    );
                }, this);
        }

        return (
            React.createElement("div", {className: "view"}, 
                React.createElement("h2", null, "Platforms"), 
                React.createElement("div", {className: "view__actions"}, 
                    React.createElement("button", {className: "button", onClick: this._onRegisterClick}, 
                        "Register platform"
                    )
                ), 
                platforms
            )
        );
    },
});

function getStateFromStores() {
    return {
        platforms: platformsStore.getPlatforms(),
    };
}

module.exports = Platforms;


},{"../action-creators/modal-action-creators":5,"../components/deregister-platform-confirmation":21,"../components/register-platform-form":35,"../stores/platforms-store":53,"react":undefined,"react-router":undefined}],35:[function(require,module,exports){
'use strict';

var React = require('react');

var modalActionCreators = require('../action-creators/modal-action-creators');
var platformManagerActionCreators = require('../action-creators/platform-manager-action-creators');
var platformRegistrationStore = require('../stores/platform-registration-store');

var RegisterPlatformForm = React.createClass({displayName: "RegisterPlatformForm",
    getInitialState: function () {
        var state = getStateFromStores();
        
        state.name = state.ipaddress = state.serverKey = state.publicKey = state.secretKey = '';
        state.protocol = 'tcp';

        return state;
    },
    componentDidMount: function () {
        platformRegistrationStore.addChangeListener(this._onStoresChange);
    },
    componentWillUnmount: function () {
        platformRegistrationStore.removeChangeListener(this._onStoresChange);
    },
    _onStoresChange: function () {
        this.setState(getStateFromStores());
    },
    _onNameChange: function (e) {
        this.setState({ name: e.target.value });
    },
    _onAddressChange: function (e) {
        this.setState({ ipaddress: e.target.value });
    },
    _onProtocolChange: function (e) {
        this.setState({ protocol: e.target.value });
    },
    _onServerKeyChange: function (e) {
        this.setState({ serverKey: e.target.value });
    },
    _onPublicKeyChange: function (e) {
        this.setState({ publicKey: e.target.value });
    },
    _onSecretKeyChange: function (e) {
        this.setState({ secretKey: e.target.value });
    },
    _onCancelClick: modalActionCreators.closeModal,
    _onSubmit: function () {

        platformManagerActionCreators.registerPlatform(
            this.state.name, 
            this._formatAddress());
        
    },
    _formatAddress: function () {

        var fullAddress = this.state.protocol + "://" + this.state.ipaddress;

        if (this.state.serverKey)
        {
            fullAddress = fullAddress + "?serverkey=" + this.state.serverKey;
        }

        if (this.state.publicKey)
        {
            fullAddress = fullAddress + "&publickey=" + this.state.publicKey;
        }

        if (this.state.secretKey)
        {
            fullAddress = fullAddress + "&secretkey=" + this.state.secretKey;
        }

        return fullAddress;
    },
    render: function () {
        
        var fullAddress = this._formatAddress();

        return (
            React.createElement("form", {className: "register-platform-form", onSubmit: this._onSubmit}, 
                React.createElement("h1", null, "Register platform"), 
                this.state.error && (
                    React.createElement("div", {className: "error"}, this.state.error.message)
                ), 
                React.createElement("div", {className: "tableDiv"}, 
                    React.createElement("div", {className: "rowDiv"}, 
                        React.createElement("div", {className: "cellDiv firstCell"}, 
                            React.createElement("label", {className: "formLabel"}, "Name"), 
                            React.createElement("input", {
                                className: "form__control form__control--block", 
                                type: "text", 
                                onChange: this._onNameChange, 
                                value: this.state.name, 
                                autoFocus: true, 
                                required: true}
                            )
                        ), 
                        React.createElement("div", {className: "cellDiv", 
                            width: "10%"}, 
                            React.createElement("label", {className: "formLabel"}, "Protocol"), React.createElement("br", null), 
                            React.createElement("select", {
                                className: "form__control", 
                                onChange: this._onProtocolChange, 
                                value: this.state.protocol, 
                                required: true
                            }, 
                                React.createElement("option", {value: "tcp"}, "TCP"), 
                                React.createElement("option", {value: "ipc"}, "IPC")
                            )
                        ), 
                        React.createElement("div", {className: "cellDiv", 
                            width: "56%"}, 
                            React.createElement("label", {className: "formLabel"}, "VIP address"), 
                            React.createElement("input", {
                                className: "form__control form__control--block", 
                                type: "text", 
                                onChange: this._onAddressChange, 
                                value: this.state.ipaddress, 
                                required: true}
                            )
                        )
                    )
                ), 
                React.createElement("div", {className: "tableDiv"}, 
                    React.createElement("div", {className: "rowDiv"}, 
                        React.createElement("div", {className: "cellDiv", 
                            width: "80%"}, 
                            React.createElement("label", {className: "formLabel"}, "Server Key"), 
                            React.createElement("input", {
                                className: "form__control form__control--block", 
                                type: "text", 
                                onChange: this._onServerKeyChange, 
                                value: this.state.serverKey}
                            )
                        )
                    )
                ), 
                React.createElement("div", {className: "tableDiv"}, 
                    React.createElement("div", {className: "rowDiv"}, 
                        React.createElement("div", {className: "cellDiv", 
                            width: "80%"}, 
                            React.createElement("label", {className: "formLabel"}, "Public Key"), 
                            React.createElement("input", {
                                className: "form__control form__control--block", 
                                type: "text", 
                                onChange: this._onPublicKeyChange, 
                                value: this.state.publicKey}
                            )
                        )
                    )
                ), 
                React.createElement("div", {className: "tableDiv"}, 
                    React.createElement("div", {className: "rowDiv"}, 
                        React.createElement("div", {className: "cellDiv", 
                            width: "80%"}, 
                            React.createElement("label", {className: "formLabel"}, "Secret Key"), 
                            React.createElement("input", {
                                className: "form__control form__control--block", 
                                type: "text", 
                                onChange: this._onSecretKeyChange, 
                                value: this.state.secretKey}
                            )
                        )
                    )
                ), 
                React.createElement("div", {className: "tableDiv"}, 
                    React.createElement("div", {className: "rowDiv"}, 
                        React.createElement("div", {className: "cellDiv", 
                            width: "100%"}, 
                            React.createElement("label", {className: "formLabel"}, "Preview"), 
                            React.createElement("div", {
                                className: "preview"}, 
                                fullAddress
                            )
                        )
                    )
                ), 
                React.createElement("div", {className: "form__actions"}, 
                    React.createElement("button", {
                        className: "button button--secondary", 
                        type: "button", 
                        onClick: this._onCancelClick
                    }, 
                        "Cancel"
                    ), 
                    React.createElement("button", {
                        className: "button", 
                        disabled: !this.state.name || !this.state.protocol || !this.state.ipaddress 
                            || !((this.state.serverKey && this.state.publicKey && this.state.secretKey) 
                                    || (!this.state.publicKey && !this.state.secretKey))
                    }, 
                        "Register"
                    )
                )
            )
        );
    },
});

function getStateFromStores() {
    return { error: platformRegistrationStore.getLastDeregisterError() };
}

module.exports = RegisterPlatformForm;


},{"../action-creators/modal-action-creators":5,"../action-creators/platform-manager-action-creators":7,"../stores/platform-registration-store":52,"react":undefined}],36:[function(require,module,exports){
'use strict';

var React = require('react');

var modalActionCreators = require('../action-creators/modal-action-creators');
var platformActionCreators = require('../action-creators/platform-action-creators');

var RemoveAgentForm = React.createClass({displayName: "RemoveAgentForm",
    getInitialState: function () {
        var state = {};

        for (var prop in this.props.agent) {
            state[prop] = this.props.agent[prop];
        }

        return state;
    }, 
    _onPropChange: function (e) {
        var state = {};

        this.setState(state);
    },
    _onCancelClick: modalActionCreators.closeModal,
    _onSubmit: function () {
        platformActionCreators.removeAgent(this.props.platform, this.props.agent);
    },
    render: function () {

        var removeMsg = 'Remove agent ' + this.props.agent.uuid + ' (' + this.props.agent.name + 
            ', ' + this.props.agent.tag + ')?';

        return (
            React.createElement("form", {className: "remove-agent-form", onSubmit: this._onSubmit}, 
                React.createElement("div", null, removeMsg), 
                React.createElement("div", {className: "form__actions"}, 
                    React.createElement("button", {
                        className: "button button--secondary", 
                        type: "button", 
                        onClick: this._onCancelClick
                    }, 
                        "Cancel"
                    ), 
                    React.createElement("button", {
                        className: "button", 
                        type: "submit", 
                        disabled: !this.props.agent.uuid
                    }, 
                        "Remove"
                    )
                )
            )
        );
    },
});

module.exports = RemoveAgentForm;


},{"../action-creators/modal-action-creators":5,"../action-creators/platform-action-creators":6,"react":undefined}],37:[function(require,module,exports){
'use strict';

var keyMirror = require('react/lib/keyMirror');

module.exports = keyMirror({
    OPEN_MODAL: null,
    CLOSE_MODAL: null,

    TOGGLE_CONSOLE: null,

    UPDATE_COMPOSER_VALUE: null,

    MAKE_REQUEST: null,
    FAIL_REQUEST: null,
    RECEIVE_RESPONSE: null,

    RECEIVE_AUTHORIZATION: null,
    RECEIVE_UNAUTHORIZED: null,
    CLEAR_AUTHORIZATION: null,

    REGISTER_PLATFORM_ERROR: null,
    DEREGISTER_PLATFORM_ERROR: null,

    RECEIVE_PLATFORMS: null,
    RECEIVE_PLATFORM: null,
    RECEIVE_PLATFORM_ERROR: null,
    CLEAR_PLATFORM_ERROR: null,

    RECEIVE_PLATFORM_TOPIC_DATA: null,

    SCAN_FOR_DEVICES: null,
    CANCEL_SCANNING: null,
    LIST_DETECTED_DEVICES: null,
    CONFIGURE_DEVICE: null,
    CONFIGURE_REGISTRY: null,

    TOGGLE_TAPTIP: null,
    HIDE_TAPTIP: null,
    SHOW_TAPTIP: null,
    CLEAR_BUTTON: null,
});


},{"react/lib/keyMirror":undefined}],38:[function(require,module,exports){
'use strict';

var Dispatcher = require('flux').Dispatcher;

var ACTION_TYPES = require('../constants/action-types');

var dispatcher = new Dispatcher();

dispatcher.dispatch = function (action) {
    if (action.type in ACTION_TYPES) {
        return Object.getPrototypeOf(this).dispatch.call(this, action);
    }

    throw 'Dispatch error: invalid action type ' + action.type;
};

module.exports = dispatcher;


},{"../constants/action-types":37,"flux":undefined}],39:[function(require,module,exports){
'use strict';

function RpcError(error) {
    this.name = 'RpcError';
    this.code = error.code;
    this.message = error.message;
    this.data = error.data;
}
RpcError.prototype = Object.create(Error.prototype);
RpcError.prototype.constructor = RpcError;

module.exports = RpcError;


},{}],40:[function(require,module,exports){
'use strict';

var uuid = require('node-uuid');

var ACTION_TYPES = require('../../constants/action-types');
var dispatcher = require('../../dispatcher');
var RpcError = require('./error');
var xhr = require('../xhr');

function RpcExchange(request, redactedParams) {
    if (!(this instanceof RpcExchange)) {
        return new RpcExchange(request);
    }

    var exchange = this;

    // TODO: validate request
    request.jsonrpc = '2.0';
    request.id = uuid.v1();

    // stringify before redacting params
    var data = JSON.stringify(request);

    if (redactedParams && redactedParams.length) {
        redactedParams.forEach(function (paramPath) {
            paramPath = paramPath.split('.');

            var paramParent = request.params;

            while (paramPath.length > 1) {
                paramParent = paramParent[paramPath.shift()];
            }

            paramParent[paramPath[0]] = '[REDACTED]';
        });
    }

    exchange.initiated = Date.now();
    exchange.request = request;

    dispatcher.dispatch({
        type: ACTION_TYPES.MAKE_REQUEST,
        exchange: exchange,
        request: exchange.request,
    });

    exchange.promise = new xhr.Request({
        method: 'POST',
        url: '/jsonrpc',
        contentType: 'application/json',
        data: data,
        timeout: 60000,
    })
        .finally(function () {
            exchange.completed = Date.now();
        })
        .then(function (response) {
            exchange.response = response;

            dispatcher.dispatch({
                type: ACTION_TYPES.RECEIVE_RESPONSE,
                exchange: exchange,
                response: response,
            });

            if (response.error) {
                throw new RpcError(response.error);
            }

            return JSON.parse(JSON.stringify(response.result));
        })
        .catch(xhr.Error, function (error) {
            exchange.error = error;

            dispatcher.dispatch({
                type: ACTION_TYPES.FAIL_REQUEST,
                exchange: exchange,
                error: error,
            });

            throw error;
        });
}

module.exports = RpcExchange;


},{"../../constants/action-types":37,"../../dispatcher":38,"../xhr":44,"./error":39,"node-uuid":undefined}],41:[function(require,module,exports){
'use strict';

module.exports = {
    Error: require('./error'),
    Exchange: require('./exchange'),
};


},{"./error":39,"./exchange":40}],42:[function(require,module,exports){
'use strict';

var EventEmitter = require('events').EventEmitter;

var CHANGE_EVENT = 'change';

function Store() {
    EventEmitter.call(this);
    this.setMaxListeners(0);
}
Store.prototype = EventEmitter.prototype;

Store.prototype.emitChange = function() {
    this.emit(CHANGE_EVENT);
};

Store.prototype.addChangeListener = function (callback) {
    this.on(CHANGE_EVENT, callback);
};

Store.prototype.removeChangeListener = function (callback) {
    this.removeListener(CHANGE_EVENT, callback);
};

module.exports = Store;


},{"events":undefined}],43:[function(require,module,exports){
'use strict';

function XhrError(message, response) {
    this.name = 'XhrError';
    this.message = message;
    this.response = response;
}
XhrError.prototype = Object.create(Error.prototype);
XhrError.prototype.constructor = XhrError;

module.exports = XhrError;


},{}],44:[function(require,module,exports){
'use strict';

module.exports = {
    Request: require('./request'),
    Error: require('./error'),
};


},{"./error":43,"./request":45}],45:[function(require,module,exports){
'use strict';

var jQuery = require('jquery');
var Promise = require('bluebird');

var XhrError = require('./error');

function XhrRequest(opts) {
    return new Promise(function (resolve, reject) {
        opts.success = resolve;
        opts.error = function (response, type) {
            switch (type) {
            case 'error':
                reject(new XhrError('Server returned ' + response.status + ' status', response));
                break;
            case 'timeout':
                reject(new XhrError('Request timed out', response));
                break;
            default:
                reject(new XhrError('Request failed: ' + type, response));
            }
        };

        jQuery.ajax(opts);
    });
}

module.exports = XhrRequest;


},{"./error":43,"bluebird":undefined,"jquery":undefined}],46:[function(require,module,exports){
'use strict';

var ACTION_TYPES = require('../constants/action-types');
var dispatcher = require('../dispatcher');
var Store = require('../lib/store');

var _authorization = sessionStorage.getItem('authorization');

var authorizationStore = new Store();

authorizationStore.getAuthorization = function () {
    return _authorization;
};

authorizationStore.dispatchToken = dispatcher.register(function (action) {
    switch (action.type) {
        case ACTION_TYPES.RECEIVE_AUTHORIZATION:
            _authorization = action.authorization;
            sessionStorage.setItem('authorization', _authorization);
            authorizationStore.emitChange();
            break;

        case ACTION_TYPES.RECEIVE_UNAUTHORIZED:
            authorizationStore.emitChange();
            break;

        case ACTION_TYPES.CLEAR_AUTHORIZATION:
            _authorization = null;
            sessionStorage.removeItem('authorization');
            authorizationStore.emitChange();
            break;
    }
});

module.exports = authorizationStore;


},{"../constants/action-types":37,"../dispatcher":38,"../lib/store":42}],47:[function(require,module,exports){
'use strict';

var ACTION_TYPES = require('../constants/action-types');
var dispatcher = require('../dispatcher');
var authorizationStore = require('../stores/authorization-store');
var Store = require('../lib/store');

var _composerId = Date.now();
var _composerValue = '';
var _consoleShown = false;
var _exchanges = [];

var consoleStore = new Store();

consoleStore.getComposerId = function () {
    return _composerId;
};

consoleStore.getComposerValue = function () {
    return _composerValue;
};

consoleStore.getConsoleShown = function () {
    return _consoleShown;
};

consoleStore.getExchanges = function () {
    return _exchanges;
};

function _resetComposerValue() {
    var authorization = authorizationStore.getAuthorization();
    var parsed;

    try {
        parsed = JSON.parse(_composerValue);
    } catch (e) {
        parsed = { method: '' };
    }

    if (authorization) {
        parsed.authorization = authorization;
    } else {
        delete parsed.authorization;
    }

    _composerValue = JSON.stringify(parsed, null, '    ');
}

_resetComposerValue();

consoleStore.dispatchToken = dispatcher.register(function (action) {
    dispatcher.waitFor([authorizationStore.dispatchToken]);

    switch (action.type) {
        case ACTION_TYPES.TOGGLE_CONSOLE:
            _consoleShown = !_consoleShown;
            consoleStore.emitChange();
            break;

        case ACTION_TYPES.UPDATE_COMPOSER_VALUE:
            _composerValue = action.value;
            consoleStore.emitChange();
            break;

        case ACTION_TYPES.RECEIVE_AUTHORIZATION:
        case ACTION_TYPES.RECEIVE_UNAUTHORIZED:
        case ACTION_TYPES.CLEAR_AUTHORIZATION:
            _composerId = Date.now();
            _resetComposerValue();
            consoleStore.emitChange();
            break;

        case ACTION_TYPES.MAKE_REQUEST:
            if (_consoleShown) {
                _exchanges.push(action.exchange);
                consoleStore.emitChange();
            }
            break;

        case ACTION_TYPES.FAIL_REQUEST:
        case ACTION_TYPES.RECEIVE_RESPONSE:
            if (_consoleShown) {
                consoleStore.emitChange();
            }
            break;
    }
});

module.exports = consoleStore;


},{"../constants/action-types":37,"../dispatcher":38,"../lib/store":42,"../stores/authorization-store":46}],48:[function(require,module,exports){
'use strict';

var ACTION_TYPES = require('../constants/action-types');
var authorizationStore = require('../stores/authorization-store');
var dispatcher = require('../dispatcher');
var Store = require('../lib/store');


var _controlButtons = {};
// var _clearButtons = {};

var controlButtonStore = new Store();



controlButtonStore.getTaptip = function (name) {
    
    var showTaptip = null;

    if (_controlButtons.hasOwnProperty([name]))
    {
        if (_controlButtons[name].hasOwnProperty("showTaptip"))
        {
            showTaptip = _controlButtons[name].showTaptip;
        }
    }

    return showTaptip;
}

// controlButtonStore.getClearButton = function (name) {
    
//     var clearButton = false;

//     if (_clearButtons.hasOwnProperty([name]))
//     {
//         delete _clearButtons[name];
//         clearButton = true;
//     }

//     return clearButton;
// }

controlButtonStore.dispatchToken = dispatcher.register(function (action) {
    switch (action.type) {

        case ACTION_TYPES.TOGGLE_TAPTIP:             

            var showTaptip;

            if (_controlButtons.hasOwnProperty(action.name))
            {
                _controlButtons[action.name].showTaptip = showTaptip = !_controlButtons[action.name].showTaptip;
            }
            else
            {
                _controlButtons[action.name] = { "showTaptip": true };
                showTaptip = true;
            }

            if (showTaptip === true) 
            {            
                //close other taptips    
                for (var key in _controlButtons)
                {
                    if (key !== action.name)
                    {
                        _controlButtons[key].showTaptip = false;
                    }
                }
            }

            controlButtonStore.emitChange();

            break;

        case ACTION_TYPES.HIDE_TAPTIP:             

            if (_controlButtons.hasOwnProperty(action.name))
            {
                if (_controlButtons[action.name].hasOwnProperty("showTaptip"))
                {
                    _controlButtons[action.name].showTaptip = false;
                    // delete _controlButtons[action.name];   
                }
            }

            controlButtonStore.emitChange();

            break;

        case ACTION_TYPES.SHOW_TAPTIP:             
        
            _controlButtons[action.name] = { "showTaptip": true };

            //close other taptips    
            for (var key in _controlButtons)
            {
                if (key !== action.name)
                {
                    _controlButtons[key].showTaptip = false;
                }
            }
            
            controlButtonStore.emitChange();

            break;

        // case ACTION_TYPES.CLEAR_BUTTON:             

        //     if (!_clearButtons.hasOwnProperty(action.name))
        //     {
        //         _clearButtons[action.name] = "";
        //     }

        //     controlButtonStore.emitChange();

        //     break;
    } 

    
    
});



module.exports = controlButtonStore;

},{"../constants/action-types":37,"../dispatcher":38,"../lib/store":42,"../stores/authorization-store":46}],49:[function(require,module,exports){
'use strict';

var ACTION_TYPES = require('../constants/action-types');
var authorizationStore = require('../stores/authorization-store');
var dispatcher = require('../dispatcher');
var Store = require('../lib/store');

var devicesStore = new Store();

var _action = "get_scan_settings";
var _view = "Detect Devices";
var _device = null;

var _registryValues = [
    [
        {"key": "Point_Name", "value": "Heartbeat"},
        {"key": "Volttron_Point_Name", "value": "Heartbeat"},
        {"key": "Units", "value": "On/Off"},
        {"key": "Units_Details", "value": "On/Off"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": 0},
        {"key": "Type", "value": "boolean"},
        {"key": "Notes", "value": "Point for heartbeat toggle"}
    ],
    [
        {"key": "Point_Name", "value": "OutsideAirTemperature1"},
        {"key": "Volttron_Point_Name", "value": "OutsideAirTemperature1"},
        {"key": "Units", "value": "F"},
        {"key": "Units_Details", "value": "-100 to 300"},
        {"key": "Writable", "value": false},
        {"key": "Starting_Value", "value": 50},
        {"key": "Type", "value": "float"},
        {"key": "Notes", "value": "CO2 Reading 0.00-2000.0 ppm"}
    ],
    [
        {"key": "Point_Name", "value": "SampleWritableFloat1"},
        {"key": "Volttron_Point_Name", "value": "SampleWritableFloat1"},
        {"key": "Units", "value": "PPM"},
        {"key": "Units_Details", "value": "1000.00 (default)"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": 10},
        {"key": "Type", "value": "float"},
        {"key": "Notes", "value": "Setpoint to enable demand control ventilation"}
    ],
    [
        {"key": "Point_Name", "value": "SampleLong1"},
        {"key": "Volttron_Point_Name", "value": "SampleLong1"},
        {"key": "Units", "value": "Enumeration"},
        {"key": "Units_Details", "value": "1 through 13"},
        {"key": "Writable", "value": false},
        {"key": "Starting_Value", "value": 50},
        {"key": "Type", "value": "int"},
        {"key": "Notes", "value": "Status indicator of service switch"}
    ],
    [
        {"key": "Point_Name", "value": "SampleWritableShort1"},
        {"key": "Volttron_Point_Name", "value": "SampleWritableShort1"},
        {"key": "Units", "value": "%"},
        {"key": "Units_Details", "value": "0.00 to 100.00 (20 default)"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": 20},
        {"key": "Type", "value": "int"},
        {"key": "Notes", "value": "Minimum damper position during the standard mode"}
    ],
    [
        {"key": "Point_Name", "value": "SampleBool1"},
        {"key": "Volttron_Point_Name", "value": "SampleBool1"},
        {"key": "Units", "value": "On / Off"},
        {"key": "Units_Details", "value": "on/off"},
        {"key": "Writable", "value": false},
        {"key": "Starting_Value", "value": true},
        {"key": "Type", "value": "boolean"},
        {"key": "Notes", "value": "Status indidcator of cooling stage 1"}
    ],
    [
        {"key": "Point_Name", "value": "SampleWritableBool1"},
        {"key": "Volttron_Point_Name", "value": "SampleWritableBool1"},
        {"key": "Units", "value": "On / Off"},
        {"key": "Units_Details", "value": "on/off"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": true},
        {"key": "Type", "value": "boolean"},
        {"key": "Notes", "value": "Status indicator"}
    ],
    [
        {"key": "Point_Name", "value": "OutsideAirTemperature2"},
        {"key": "Volttron_Point_Name", "value": "OutsideAirTemperature2"},
        {"key": "Units", "value": "F"},
        {"key": "Units_Details", "value": "-100 to 300"},
        {"key": "Writable", "value": false},
        {"key": "Starting_Value", "value": 50},
        {"key": "Type", "value": "float"},
        {"key": "Notes", "value": "CO2 Reading 0.00-2000.0 ppm"}
    ],
    [
        {"key": "Point_Name", "value": "SampleWritableFloat2"},
        {"key": "Volttron_Point_Name", "value": "SampleWritableFloat2"},
        {"key": "Units", "value": "PPM"},
        {"key": "Units_Details", "value": "1000.00 (default)"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": 10},
        {"key": "Type", "value": "float"},
        {"key": "Notes", "value": "Setpoint to enable demand control ventilation"}
    ],
    [
        {"key": "Point_Name", "value": "SampleLong2"},
        {"key": "Volttron_Point_Name", "value": "SampleLong2"},
        {"key": "Units", "value": "Enumeration"},
        {"key": "Units_Details", "value": "1 through 13"},
        {"key": "Writable", "value": false},
        {"key": "Starting_Value", "value": 50},
        {"key": "Type", "value": "int"},
        {"key": "Notes", "value": "Status indicator of service switch"}
    ],
    [
        {"key": "Point_Name", "value": "SampleWritableShort2"},
        {"key": "Volttron_Point_Name", "value": "SampleWritableShort2"},
        {"key": "Units", "value": "%"},
        {"key": "Units_Details", "value": "0.00 to 100.00 (20 default)"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": 20},
        {"key": "Type", "value": "int"},
        {"key": "Notes", "value": "Minimum damper position during the standard mode"}
    ],
    [
        {"key": "Point_Name", "value": "SampleBool2"},
        {"key": "Volttron_Point_Name", "value": "SampleBool2"},
        {"key": "Units", "value": "On / Off"},
        {"key": "Units_Details", "value": "on/off"},
        {"key": "Writable", "value": false},
        {"key": "Starting_Value", "value": true},
        {"key": "Type", "value": "boolean"},
        {"key": "Notes", "value": "Status indidcator of cooling stage 1"}
    ],
    [
        {"key": "Point_Name", "value": "SampleWritableBool2"},
        {"key": "Volttron_Point_Name", "value": "SampleWritableBool2"},
        {"key": "Units", "value": "On / Off"},
        {"key": "Units_Details", "value": "on/off"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": true},
        {"key": "Type", "value": "boolean"},
        {"key": "Notes", "value": "Status indicator"}
    ],
    [
        {"key": "Point_Name", "value": "OutsideAirTemperature3"},
        {"key": "Volttron_Point_Name", "value": "OutsideAirTemperature3"},
        {"key": "Units", "value": "F"},
        {"key": "Units_Details", "value": "-100 to 300"},
        {"key": "Writable", "value": false},
        {"key": "Starting_Value", "value": 50},
        {"key": "Type", "value": "float"},
        {"key": "Notes", "value": "CO2 Reading 0.00-2000.0 ppm"}
    ],
    [
        {"key": "Point_Name", "value": "SampleWritableFloat3"},
        {"key": "Volttron_Point_Name", "value": "SampleWritableFloat3"},
        {"key": "Units", "value": "PPM"},
        {"key": "Units_Details", "value": "1000.00 (default)"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": 10},
        {"key": "Type", "value": "float"},
        {"key": "Notes", "value": "Setpoint to enable demand control ventilation"}
    ],
    [
        {"key": "Point_Name", "value": "SampleLong3"},
        {"key": "Volttron_Point_Name", "value": "SampleLong3"},
        {"key": "Units", "value": "Enumeration"},
        {"key": "Units_Details", "value": "1 through 13"},
        {"key": "Writable", "value": false},
        {"key": "Starting_Value", "value": 50},
        {"key": "Type", "value": "int"},
        {"key": "Notes", "value": "Status indicator of service switch"}
    ],
    [
        {"key": "Point_Name", "value": "SampleWritableShort3"},
        {"key": "Volttron_Point_Name", "value": "SampleWritableShort3"},
        {"key": "Units", "value": "%"},
        {"key": "Units_Details", "value": "0.00 to 100.00 (20 default)"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": 20},
        {"key": "Type", "value": "int"},
        {"key": "Notes", "value": "Minimum damper position during the standard mode"}
    ],
    [
        {"key": "Point_Name", "value": "SampleBool3"},
        {"key": "Volttron_Point_Name", "value": "SampleBool3"},
        {"key": "Units", "value": "On / Off"},
        {"key": "Units_Details", "value": "on/off"},
        {"key": "Writable", "value": false},
        {"key": "Starting_Value", "value": true},
        {"key": "Type", "value": "boolean"},
        {"key": "Notes", "value": "Status indidcator of cooling stage 1"}
    ],
    [
        {"key": "Point_Name", "value": "SampleWritableBool3"},
        {"key": "Volttron_Point_Name", "value": "SampleWritableBool3"},
        {"key": "Units", "value": "On / Off"},
        {"key": "Units_Details", "value": "on/off"},
        {"key": "Writable", "value": true},
        {"key": "Starting_Value", "value": true},
        {"key": "Type", "value": "boolean"},
        {"key": "Notes", "value": "Status indicator"}
    ]
];

devicesStore.getState = function () {
    return { action: _action, view: _view, device: _device };
};

devicesStore.getFilteredRegistryValues = function (device, filterStr) {

    return _registryValues.filter(function (item) {
        var pointName = item.find(function (pair) {
            return pair.key === "Point_Name";
        })

        return (pointName ? (pointName.value.trim().toUpperCase().indexOf(filterStr.trim().toUpperCase()) > -1) : false);
    });
}

devicesStore.getRegistryValues = function (device) {
    return _registryValues.slice();
    
};

devicesStore.dispatchToken = dispatcher.register(function (action) {
    dispatcher.waitFor([authorizationStore.dispatchToken]);

    switch (action.type) {
        case ACTION_TYPES.SCAN_FOR_DEVICES:
            _action = "start_scan";
            _view = "Detect Devices";
            _device = null;
            devicesStore.emitChange();
            break;
        case ACTION_TYPES.CANCEL_SCANNING:
            _action = "get_scan_settings";
            _view = "Detect Devices";
            _device = null;
            devicesStore.emitChange();
            break;
        case ACTION_TYPES.LIST_DETECTED_DEVICES:
            _action = "show_new_devices";
            _view = "Configure Devices";
            _device = null;
            devicesStore.emitChange();
            break;
        case ACTION_TYPES.CONFIGURE_DEVICE:
            _action = "configure_device";
            _view = "Configure Device";
            _device = action.device;
            devicesStore.emitChange();
            break;
        case ACTION_TYPES.CONFIGURE_REGISTRY:
            _action = "configure_registry";
            _view = "Registry Configuration";
            _device = action.device;
            devicesStore.emitChange();
            break;
    }
});

module.exports = devicesStore;


},{"../constants/action-types":37,"../dispatcher":38,"../lib/store":42,"../stores/authorization-store":46}],50:[function(require,module,exports){
'use strict';

var ACTION_TYPES = require('../constants/action-types');
var authorizationStore = require('./authorization-store');
var dispatcher = require('../dispatcher');
var Store = require('../lib/store');

var _lastError = null;

var loginFormStore = new Store();

loginFormStore.getLastError = function () {
    return _lastError;
};

loginFormStore.dispatchToken = dispatcher.register(function (action) {
    dispatcher.waitFor([authorizationStore.dispatchToken]);

    switch (action.type) {
        case ACTION_TYPES.RECEIVE_AUTHORIZATION:
            _lastError = null;
            loginFormStore.emitChange();
            break;

        case ACTION_TYPES.RECEIVE_UNAUTHORIZED:
            _lastError = action.error;
            loginFormStore.emitChange();
            break;
    }
});

module.exports = loginFormStore;


},{"../constants/action-types":37,"../dispatcher":38,"../lib/store":42,"./authorization-store":46}],51:[function(require,module,exports){
'use strict';

var ACTION_TYPES = require('../constants/action-types');
var dispatcher = require('../dispatcher');
var Store = require('../lib/store');

var _modalContent = null;

var modalStore = new Store();

modalStore.getModalContent = function () {
    return _modalContent;
};

modalStore.dispatchToken = dispatcher.register(function (action) {
    switch (action.type) {
        case ACTION_TYPES.OPEN_MODAL:
            _modalContent = action.content;
            modalStore.emitChange();
            break;

        case ACTION_TYPES.CLOSE_MODAL:
        case ACTION_TYPES.RECEIVE_UNAUTHORIZED:
            _modalContent = null;
            modalStore.emitChange();
            break;
    }
});

module.exports = modalStore;


},{"../constants/action-types":37,"../dispatcher":38,"../lib/store":42}],52:[function(require,module,exports){
'use strict';

var ACTION_TYPES = require('../constants/action-types');
var authorizationStore = require('./authorization-store');
var dispatcher = require('../dispatcher');
var Store = require('../lib/store');

var _lastRegisterError = null;
var _lastDeregisterError = null;

var platformRegistrationStore = new Store();

platformRegistrationStore.getLastRegisterError = function () {
    return _lastRegisterError;
};

platformRegistrationStore.getLastDeregisterError = function () {
    return _lastDeregisterError;
};

platformRegistrationStore.dispatchToken = dispatcher.register(function (action) {
    dispatcher.waitFor([authorizationStore.dispatchToken]);

    switch (action.type) {
        case ACTION_TYPES.REGISTER_PLATFORM_ERROR:
            _lastRegisterError = action.error;
            platformRegistrationStore.emitChange();
            break;

        case ACTION_TYPES.DEREGISTER_PLATFORM_ERROR:
            _lastDeregisterError = action.error;
            platformRegistrationStore.emitChange();
            break;

        case ACTION_TYPES.CLOSE_MODAL:
            _lastRegisterError = null;
            _lastDeregisterError = null;
            platformRegistrationStore.emitChange();
            break;
    }
});

module.exports = platformRegistrationStore;


},{"../constants/action-types":37,"../dispatcher":38,"../lib/store":42,"./authorization-store":46}],53:[function(require,module,exports){
'use strict';

var ACTION_TYPES = require('../constants/action-types');
var authorizationStore = require('../stores/authorization-store');
var dispatcher = require('../dispatcher');
var Store = require('../lib/store');

var _platforms = null;
var _lastErrors = {};

var platformsStore = new Store();

platformsStore.getPlatform = function (uuid) {
    var foundPlatform = null;

    if (_platforms) {
        _platforms.some(function (platform) {
            if (platform.uuid === uuid) {
                foundPlatform = platform;
                return true;
            }
        });
    }

    return foundPlatform;
};

platformsStore.getPlatforms = function () {
    return _platforms;
};

platformsStore.getLastError = function (uuid) {
    return _lastErrors[uuid] || null;
};

platformsStore.dispatchToken = dispatcher.register(function (action) {
    dispatcher.waitFor([authorizationStore.dispatchToken]);

    switch (action.type) {
        case ACTION_TYPES.CLEAR_AUTHORIZATION:
            _platforms = null;
            platformsStore.emitChange();
            break;

        case ACTION_TYPES.RECEIVE_PLATFORMS:
            _platforms = action.platforms;
            platformsStore.emitChange();
            break;

        case ACTION_TYPES.RECEIVE_PLATFORM:
            platformsStore.emitChange();
            break;

        case ACTION_TYPES.RECEIVE_PLATFORM_ERROR:
            _lastErrors[action.platform.uuid] = action.error;
            platformsStore.emitChange();
            break;

        case ACTION_TYPES.CLEAR_PLATFORM_ERROR:
            delete _lastErrors[action.platform.uuid];
            platformsStore.emitChange();
            break;
    }
});

module.exports = platformsStore;


},{"../constants/action-types":37,"../dispatcher":38,"../lib/store":42,"../stores/authorization-store":46}],54:[function(require,module,exports){
'use strict';

var ACTION_TYPES = require('../constants/action-types');
var authorizationStore = require('./authorization-store');
var dispatcher = require('../dispatcher');
var Store = require('../lib/store');

var topicData = {};

var topicDataStore = new Store();

topicDataStore.getTopicData = function (platform, topic) {
    if (topicData[platform.uuid] && topicData[platform.uuid][topic]) {
        return topicData[platform.uuid][topic];
    }

    return null;
};

topicDataStore.dispatchToken = dispatcher.register(function (action) {
    dispatcher.waitFor([authorizationStore.dispatchToken]);

    switch (action.type) {
        case ACTION_TYPES.RECEIVE_PLATFORM_TOPIC_DATA:
            topicData[action.platform.uuid] = topicData[action.platform.uuid] || {};
            topicData[action.platform.uuid][action.topic] = action.data;
            topicDataStore.emitChange();
            break;

        case ACTION_TYPES.CLEAR_AUTHORIZATION:
            topicData= {};
            topicDataStore.emitChange();
            break;
    }
});

module.exports = topicDataStore;


},{"../constants/action-types":37,"../dispatcher":38,"../lib/store":42,"./authorization-store":46}]},{},[1]);
