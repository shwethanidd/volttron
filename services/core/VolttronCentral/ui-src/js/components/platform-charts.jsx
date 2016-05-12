'use strict';

var React = require('react');
var Router = require('react-router');
var PlatformChart = require('./platform-chart');
// var Modal = require('./modal');
var modalActionCreators = require('../action-creators/modal-action-creators');
// var modalStore = require('../stores/modal-store');
var platformActionCreators = require('../action-creators/platform-action-creators');
var EditChartForm = require('./edit-chart-form');
var platformsStore = require('../stores/platforms-store');
var chartStore = require('../stores/platform-chart-store');
var statusIndicatorActionCreators = require('../action-creators/status-indicator-action-creators');
var platformManagerActionCreators = require('../action-creators/platform-manager-action-creators');

var PlatformCharts = React.createClass({
    getInitialState: function () {

        var vc = platformsStore.getVcInstance();

        var state = {
            platform: vc,
            chartData: chartStore.getData(),
            historianRunning: platformsStore.getHistorianRunning(vc),
            modalContent: null
        };

        return state;
    },
    componentWillMount: function () {
        
    },
    componentDidMount: function () {
        chartStore.addChangeListener(this._onChartStoreChange);
        platformsStore.addChangeListener(this._onPlatformStoreChange);
        // modalStore.addChangeListener(this._onModalStoreChange);

        if (!this.state.platform)
        {
            platformManagerActionCreators.loadPlatforms();
        }
    },
    componentWillUnmount: function () {
        chartStore.removeChangeListener(this._onChartStoreChange);
        platformsStore.removeChangeListener(this._onPlatformStoreChange);
        // modalStore.removeChangeListener(this._onModalStoreChange);
    },
    _onChartStoreChange: function () {
        this.setState({chartData: chartStore.getData()});
    },
    _onPlatformStoreChange: function () {

        var platform = this.state.platform;

        if (!platform)
        {
            platform = platformsStore.getVcInstance();

            if (platform)
            {
                this.setState({platform: platform});
            }
        }

        this.setState({historianRunning: platformsStore.getHistorianRunning(platform)});
    },
    // _onModalStoreChange: function () {
    //     var modalContent = modalStore.getModalContent();

    //     if (modalContent.hasOwnProperty("charts"))
    //     {
    //         this.setState({modalContent: modalContent.charts});
    //     }
    // },
    _onAddChartClick: function (platform) {

        if (this.state.historianRunning)
        {
            platformActionCreators.loadChartTopics(this.state.platform);

            modalActionCreators.openModal(<EditChartForm platform={this.state.platform}/>);            
        }
        else
        {
            var message = "Charts can't be added. The historian agent is unavailable."
            statusIndicatorActionCreators.openStatusIndicator("error", message);
        }
    },
    _onDeleteChartClick: function (platform, chart) {
        modalActionCreators.openModal(
            <ConfirmForm
                targetArea="charts"
                promptTitle="Delete chart"
                promptText={'Delete ' + chart.type + ' chart for ' + chart.topic + '?'}
                confirmText="Delete"
                onConfirm={platformActionCreators.deleteChart.bind(null, platform, chart)}>
            </ConfirmForm>
        );
    },
    render: function () {

        var chartData = this.state.chartData; 

        var platformCharts = [];

        for (var key in chartData)
        {
            if (chartData[key].data.length > 0)
            {
                var platformChart = <PlatformChart key={key} chart={chartData[key]} chartKey={key} hideControls={false}/>
                platformCharts.push(platformChart);
            }
        }

        if (platformCharts.length === 0)
        {
            var noCharts = <div>No charts have been loaded. Add charts by selecting points in the side panel.</div>
            platformCharts.push(noCharts);
        }

        // if (this.state.modalContent) {
        //     classes.push('platform-manager--modal-open');
        //     modal = (
        //         <Modal targetArea="charts" targetRef="view">{this.state.modalContent}</Modal>
        //     );
        // }
    
        return (
                <div>
                    <div className="view">
                        <div>
                            <button
                                className="button"
                                onClick={this._onAddChartClick.bind(null, this.state.platform)}
                            >
                                Add chart
                            </button>
                        </div>
                        <h2>Charts</h2>
                        {platformCharts}
                    </div>
                </div>
        );
    },
});

// function getChartsFromStores() {

//     return chartStore.getData();
// }

// function getHistorian()
// {
//     var platform = platformsStore.getHistorian();

//     var historian;

//     if (platform.agents)
//     {
//         historian = platform.agents.find(function (agent) {
     
//             return agent.name.indexOf("historian") > -1;
//         });        
//     }
 
//     return historian;
// } 

module.exports = PlatformCharts;
