'use strict';

var React = require('react');

var ComboBox = React.createClass({
    mixins: [
        require('react-onclickoutside')
    ],
	getInitialState: function () {

        var preppedItems = prepItems(this.props.itemskey, this.props.itemsvalue, this.props.itemslabel, this.props.items);

        var state = {
            selectedItem: "",
            inputValue: "",
            hideMenu: true,
            preppedItems: preppedItems,
            itemsList: preppedItems
        };

        this.forceHide = false;

        return state;
    },
    componentDidUpdate: function () {
        if (this.forceHide)
        {
            React.findDOMNode(this.refs.comboInput).blur();
            this.forceHide = false;
        }
    },
    handleClickOutside: function () {
        if (!this.state.hideMenu)
        {
            this.setState({hideMenu: true});
        }
    },
    _onClick: function (e) {
        this.setState({selectedItem: e.target.dataset.topicLabel});
        this.setState({hideMenu: true});
        this.setState({inputValue: e.target.dataset.topicLabel});
    },
    _onFocus: function () {
        this.setState({hideMenu: false});
    },
    _onKeyup: function (e) {
        if (e.keyCode === 13)
        {
            this.forceHide = true;
            this.setState({hideMenu: true});
        }
    },
    _onChange: function (e) {

        var inputValue = e.target.value;

        var itemsList = filterItems(inputValue, this.state.preppedItems);

        this.setState({itemsList: itemsList});

        this.setState({inputValue: inputValue}); 
                
    },

	render: function () {
		
        var menuStyle = {
            display: (this.state.hideMenu ? 'none' : 'block')
        };

        var items = this.state.itemsList.map(function (item, index) {
            return (
                <div className="combobox-item">
                    <div 
                        onClick={this._onClick}
                        data-topic-label={item.label}
                        data-topic-value={item.value}
                        data-topic-key={item.key}>{item.label}</div>
                </div>
            )
        }, this);

		return (
		
        	<div className="combobox-control">
                <input 
                    type="text" 
                    onFocus={this._onFocus} 
                    onChange={this._onChange}
                    onKeyUp={this._onKeyup}
                    ref="comboInput"
                    value={this.state.inputValue}></input>

                <div className="combobox-menu" style={menuStyle}>                    
				    {items}
                </div>
			</div>
		);
	},
});

function prepItems(itemsKey, itemsValue, itemsLabel, itemsList)
{
    var props = {
        itemsKey: itemsKey,
        itemsValue: itemsValue,
        itemsLabel: itemsLabel
    };

    var list = itemsList.map(function (item, index) {

        var preppedItem = {
            key: (this.itemsKey ? item[this.itemsKey] : index),
            value: (this.itemsValue ? item[this.itemsValue] : item),
            label: (this.itemsLabel ? item[this.itemsLabel] : item)
        };

        return preppedItem;
    }, props);

    return JSON.parse(JSON.stringify(list));
}

function filterItems(filterTerm, itemsList)
{
    var listCopy = JSON.parse(JSON.stringify(itemsList));

    var filteredItems = listCopy;

    if (filterTerm)
    {
        filteredItems = [];

        listCopy.forEach(function (item) {
            if (item.label.toUpperCase().indexOf(filterTerm.toUpperCase()) > -1)
            {
                filteredItems.push(item);
            }
        });
    }

    return filteredItems;
}


module.exports = ComboBox;
