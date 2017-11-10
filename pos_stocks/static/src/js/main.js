/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
odoo.define('pos_stock.pos_stock',function(require) {
	"use strict";
	var models = require('point_of_sale.models');
	var PosBaseWidget = require('point_of_sale.BaseWidget');
	var gui = require('point_of_sale.gui');
	var PopupWidget = require('point_of_sale.popups');
	var core = require('web.core');
	var Model = require('web.DataModel');
	var screens = require('point_of_sale.screens');
	var SuperNumpadState = models.NumpadState.prototype;
	var model_list = models.PosModel.prototype.models
	var _t = core._t;
	var _super_posmodel = models.PosModel.prototype;

	//--Fetching product model dictionary--
	models.load_fields('product.product',['qty_available','virtual_available','outgoing_qty','type']);
	var product_model = null;
	for(var i = 0,len = model_list.length;i<len;i++){
		if(model_list[i].model == "product.product"){
			product_model = model_list[i];
			break;
		}
	}
	
	//--Updating product model dictionary--
	var super_product_loaded = product_model.loaded;
	product_model.context= function(self){ return { pricelist: self.pricelist.id, display_default_code: false ,location: self.config.stock_location_id[0]}; },
	product_model.loaded = function(self,products){
		if(self.config.wk_hide_out_of_stock){
			var available_product = [];
			for(var i = 0,len = products.length; i<len; i++){
				switch(self.config.wk_stock_type){
					case'forecasted_qty':
						if(products[i].virtual_available>0||products[i].type == 'service')
							available_product.push(products[i]);
						break;
					case'virtual_qty':
						if((products[i].qty_available-products[i].outgoing_qty)>0||products[i].type == 'service')
							available_product.push(products[i]);
						break;
					default:
						if(products[i].qty_available>0||products[i].type == 'service')
							available_product.push(products[i]);
				}
			}
			products = available_product;
		}
		var results={}
		for(var i = 0,len=products.length;i<len;i++){
			switch(self.config.wk_stock_type){
				case'available_qty':
					results[products[i].id]=products[i].qty_available
					break;
				case'forecasted_qty':
					results[products[i].id]=products[i].virtual_available
					break;
				default:
					results[products[i].id]=products[i].qty_available-products[i].outgoing_qty
			}
		}
		self.set({'wk_product_qtys' : results});
		self.chrome.wk_change_qty_css();
		super_product_loaded.call(this,self,products);
	},
	
	models.PosModel = models.PosModel.extend({
		push_and_invoice_order: function(order) {
			var self = this;
			if (order != undefined) {
				if(!order.is_return_order){
                    var wk_order_line = order.get_orderlines();
                    for (var j = 0; j < wk_order_line.length; j++) {
                        self.get('wk_product_qtys')[wk_order_line[j].product.id] = self.get('wk_product_qtys')[wk_order_line[j].product.id] - wk_order_line[j].quantity;
                    }
                }else{
                    var wk_order_line = order.get_orderlines();
                    for (var j = 0; j < wk_order_line.length; j++) {
                        self.get('wk_product_qtys')[wk_order_line[j].product.id] = self.get('wk_product_qtys')[wk_order_line[j].product.id] + wk_order_line[j].quantity;
                    }
                }
			}
			var push = _super_posmodel.push_and_invoice_order.call(this, order);
			return push;
		},

		push_order: function(order) {
            var self = this;
            if (order != undefined) {
                if(!order.is_return_order){
                    var wk_order_line = order.get_orderlines();
                    for (var j = 0; j < wk_order_line.length; j++) {
						if(!wk_order_line[j].stock_location_id)
                        	self.get('wk_product_qtys')[wk_order_line[j].product.id] = self.get('wk_product_qtys')[wk_order_line[j].product.id] - wk_order_line[j].quantity;
                    }
                }else{
                    var wk_order_line = order.get_orderlines();
                    for (var j = 0; j < wk_order_line.length; j++) {
                        self.get('wk_product_qtys')[wk_order_line[j].product.id] = self.get('wk_product_qtys')[wk_order_line[j].product.id] + wk_order_line[j].quantity;
                    }
                }
            }
            var push = _super_posmodel.push_order.call(this, order);
            return push;
        },
	});

	PosBaseWidget.include({
		 set_stock_qtys: function(result){
            var self = this;
            if(!self.chrome.screens){
                $.unblockUI();
                return;
            }
            self.chrome.screens.products.product_categories_widget.reset_category();
            var all = $('.product');
            $.each(all, function(index, value){
                var product_id = $(value).data('product-id');
                var stock_qty = result[product_id];
                $(value).find('.qty-tag').html(stock_qty);
            });
            $.unblockUI();
        },
		get_information: function(wk_product_id) {
			self = this;
			if (self.pos.get('wk_product_qtys'))
				return self.pos.get('wk_product_qtys')[wk_product_id];
		},
		wk_change_qty_css: function() {
			self = this;
			var wk_order = self.pos.get('orders');
			var wk_p_qty = new Array();
			var wk_product_obj = self.pos.get('wk_product_qtys');
			if (wk_order) {
				for (var i in wk_product_obj)
					wk_p_qty[i] = self.pos.get('wk_product_qtys')[i];
				for (var i = 0; i < wk_order.length; i++) {
					if(!wk_order.models[i].is_return_order){
                        var wk_order_line = wk_order.models[i].get_orderlines();
                        for (var j = 0; j < wk_order_line.length; j++) {
                            if(!wk_order_line[j].stock_location_id) 
                                wk_p_qty[wk_order_line[j].product.id] = wk_p_qty[wk_order_line[j].product.id] - wk_order_line[j].quantity;                       
                            var qty = wk_p_qty[wk_order_line[j].product.id];
                            if (qty)
                                $("#qty-tag" + wk_order_line[j].product.id).html(qty);
                            else
                                $("#qty-tag" + wk_order_line[j].product.id).html('0');
                        }
                    }
				}
			}
		}
	});
	var OutOfStockMessagePopup = PopupWidget.extend({
		template: 'OutOfStockMessagePopup',
		show:function(options){
			var self = this;
			this.options = options || ''; 
			self._super(options);
		}
	});
	gui.define_popup({ name: 'out_of_stock', widget: OutOfStockMessagePopup });

	var _super_order = models.Order.prototype;
	models.Order = models.Order.extend({
		add_product: function(product, options) {
			var self = this;
			if(!self.pos.config.wk_continous_sale && self.pos.config.wk_display_stock && !self.pos.get_order().is_return_order) {
				if (parseInt($("#qty-tag" + product.id).html()) <= self.pos.config.wk_deny_val) 
					self.pos.gui.show_popup('out_of_stock',{
						'title':  _t("Warning !!!!"),
						'body': _t("("+product.display_name+")"+self.pos.config.wk_error_msg+"."),
						'product_id': product.id
					});
				else 
					_super_order.add_product.call(this, product, options);
			}else 
				_super_order.add_product.call(this, product, options);
			if (self.pos.config.wk_display_stock  && !self.is_return_order) {
				self.pos.chrome.wk_change_qty_css();
			}
		},
	});

	//---Product qty updated whenever product screen shown -----------
	screens.ProductScreenWidget.include({
        show: function(){
            var self = this;
            this._super();
            self.pos.chrome.set_stock_qtys(self.pos.get('wk_product_qtys'));
            self.pos.chrome.wk_change_qty_css();
        },
    });

	screens.NumpadWidget.include({
		start: function() {
			this.state.bind('change:mode', this.changedMode, this);
			this.changedMode();
			this.$el.find('.numpad-backspace').click(_.bind(this.clickDeleteLastChar, this));
			this.$el.find('.numpad-minus').click(_.bind(this.clickSwitchSign, this));
			this.$el.find('.number-char').click(_.bind(this.clickAppendNewChar, this));
			this.$el.find('.mode-button').click(_.bind(this.clickChangeMode, this));
			var self = this;
			this.$el.find('.numpad-backspace').on('update_buffer',function(){
				return self.state.delete_last_char_of_buffer();	  
			});
		}
	});

	models.NumpadState = models.NumpadState.extend({ 
		delete_last_char_of_buffer: function() {	
			if(this.get('buffer') === ""){
				if(this.get('mode') === 'quantity')
					this.trigger('set_value','remove');
				else
					this.trigger('set_value',this.get('buffer'));
			}else{
				var newBuffer = this.get('buffer').slice(0,-1) || "";
				this.set({ buffer: newBuffer });
				this.trigger('set_value',this.get('buffer'));
			}
		}
	});

	gui.Gui = gui.Gui.extend({
		show_screen: function(screen_name,params,refresh) {
			var self = this;
			self._super(screen_name,params,refresh);
			if (refresh) { 
				self.pos.chrome.wk_change_qty_css();
			}
		}
	});

	var _super_orderline = models.Orderline.prototype;
	models.Orderline = models.Orderline.extend({
		template: 'Orderline',
		initialize: function(attr,options){
			this.option = options;
			this.comment = 0.0
			if (options.product && !options.stock_location_id)
				this.comment=parseInt($("#qty-tag" + options.product.id).html());
			_super_orderline.initialize.call(this,attr,options);
		},

		set_quantity: function(quantity) {
			var self = this;
			if(!self.pos.config.wk_continous_sale && self.pos.config.wk_display_stock && isNaN(quantity)!=true && quantity!='' && parseFloat(self.comment)-parseFloat(quantity)<self.pos.config.wk_deny_val && self.comment !=0.0){
				self.pos.gui.show_popup('out_of_stock',{
					'title':  _t("Warning !!!!"),
					'body': _t("("+this.option.product.display_name+")"+self.pos.config.wk_error_msg+"."),
					'product_id': this.option.product.id
				});
			}else{
				var wk_avail_pro = 0;
				if (self.pos.get('selectedOrder')) {
					var wk_pro_order_line = (self.pos.get('selectedOrder')).get_selected_orderline();
					if (!self.pos.config.wk_continous_sale && self.pos.config.wk_display_stock && wk_pro_order_line) {
						var wk_current_qty = parseInt($("#qty-tag" + (wk_pro_order_line.product.id)).html());
						if (quantity == '' || quantity == 'remove')
							wk_avail_pro = wk_current_qty + wk_pro_order_line;
						else 
							wk_avail_pro = wk_current_qty + wk_pro_order_line - quantity;
						if (wk_avail_pro < self.pos.config.wk_deny_val && (!(quantity == '' || quantity == 'remove'))) {
							self.pos.gui.show_popup('out_of_stock',{
								'title':  _t("Warning !!!!"),
								'body': _t("("+wk_pro_order_line.product.display_name+")"+self.pos.config.wk_error_msg+"."),
								'product_id':wk_pro_order_line.product.id
							});
						}else 
							_super_orderline.set_quantity.call(this, quantity);
					}else
						_super_orderline.set_quantity.call(this, quantity);
					if(self.pos.config.wk_display_stock) 
						self.pos.chrome.wk_change_qty_css();
				}
				else
					_super_orderline.set_quantity.call(this, quantity);
			}
		},
	});
	return OutOfStockMessagePopup	
});