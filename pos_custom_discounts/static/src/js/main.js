/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
odoo.define('pos_custom_discounts.pos_custom_discounts', function (require) {
"use strict";
	var models = require('point_of_sale.models');
	var core = require('web.core');
	var gui = require('point_of_sale.gui');
	var pos_model = require('point_of_sale.models');
	var core = require('web.core');
	var _t = core._t;
	var screens = require('point_of_sale.screens');
	var popup_widget = require('point_of_sale.popups');
	var SuperOrder = models.Order;
	var SuperOrderline = pos_model.Orderline;
	var QWeb = core.qweb;
	models.load_models([{
		model:'pos.custom.discount',
		field: [],
		domain:function(self){
			return [['id','in',self.config.discount_ids]];
		},
		loaded: function(self,result) {
			self.all_discounts = result;
		}

	}],{
			'before': 'pos.category'
		}
	);
	pos_model.Orderline = pos_model.Orderline.extend({			
		initialize: function(attr,options){
			this.custom_discount_reason='';
			SuperOrderline.prototype.initialize.call(this,attr,options);
		},
		export_for_printing: function(){
			var dict = SuperOrderline.prototype.export_for_printing.call(this);
			dict.custom_discount_reason = this.custom_discount_reason;
			return dict;
		},
		get_custom_discount_reason: function(){
			var self = this;		
			return self.custom_discount_reason;
		},
		export_as_JSON: function() {
			var self = this;
			var loaded=SuperOrderline.prototype.export_as_JSON.call(this);
			loaded.custom_discount_reason=self.get_custom_discount_reason();  
			return loaded;
		}
	});
	
	var WkCustomDiscountPopup = popup_widget.extend({
		template: 'WkCustomDiscountPopup',
		
		show: function(){
			var self=this;
			this._super();
			var order = this.pos.get_order();
			$('.custom_cancel').on('click',function(){
				self.gui.close_popup();
				self.gui.current_screen.order_widget.numpad_state.reset();
			});
			$('#discount').on('click',function(){
				$('#error_div').hide();
			})

			$('.current_product').on('click',function(){
				if (($('#discount').val())>100 || $('#discount').val()<=0){
					$('#error_div').show();
					$('#customize_error').html('<i class="fa fa-exclamation-triangle" aria-hidden="true"></i > Discount percent must be between 0 and 100.')
				}
				else if ($("#reason").val() == ''){
					$('#error_div').show();
					$('#customize_error').html('<i class="fa fa-exclamation-triangle" aria-hidden="true"></i >   Please enter the reason for discount')
				}
				else{
					var wk_customize_discount = parseFloat($('#discount').val())
					var reason =($("#reason").val());
					order.get_selected_orderline().set_discount(wk_customize_discount);	
					self.pos.get_order().get_selected_orderline().custom_discount_reason=reason;
					$('ul.orderlines li.selected div#custom_discount_reason').text(reason);
					self.gui.close_popup();
					self.gui.current_screen.order_widget.numpad_state.reset();	
				}				
				
			});
			$('.whole_order').on('click',function(){
				var orderline_ids = order.get_orderlines();
				if (($('#discount').val())>100 || $('#discount').val()<=0){
					$('#error_div').show();
					$('#customize_error').html('<i class="fa fa-exclamation-triangle" aria-hidden="true"></i > Discount percent must be between 0 and 100.')
				}
				else if ($("#reason").val() == ''){
					$('#error_div').show();
					$('#customize_error').html('<i class="fa fa-exclamation-triangle" aria-hidden="true"></i >   Please enter the reason for discount')
				}
				else{
					var wk_customize_discount = parseFloat($('#discount').val());
					var reason =($("#reason").val());
					for(var i=0; i< orderline_ids.length; i++){
							orderline_ids[i].set_discount(wk_customize_discount);
							orderline_ids[i].custom_discount_reason=reason;
						}
					$('ul.orderlines li div#custom_discount_reason').text(reason);
					self.gui.close_popup();
					self.gui.current_screen.order_widget.numpad_state.reset();	
					
				}				
				
			});
		}

	});
	gui.define_popup({ name: 'custom_discount', widget: WkCustomDiscountPopup });

	var WkDiscountPopup = popup_widget.extend({
		template: 'WkDiscountPopup',
		wk_ask_password: function(password) {
			var self = this;
			var ret = new $.Deferred();
			if (password) {
				this.gui.show_popup('password',{
					'title': _t('Password ?'),
					confirm: function(pw) {
						if (pw !== password) {
							self.gui.show_popup('webkul_error_popup',{
								'title':_t('Password Incorrect !!!'),
								'body':_('Entered Password Is Incorrect ')
							});
						} else {
							ret.resolve();
						}
					},
					cancel: function() {
						self.gui.current_screen.order_widget.numpad_state.reset();	
					}
				});
			} else {
				ret.resolve();
			}
			return ret;
		},

		show: function() {
			var self = this;
			this._super();
			var discount_id = null;
			var wk_discount_list = self.pos.all_discounts;
			var wk_discount_percentage=0;
			var order = this.pos.get_order();
			var discount_price=0;
			var wk_discount = null;
			var currentOrder = self.pos.get('selectedOrder');
			$(".button.apply").removeClass('oe_hidden');
			$(".button.apply_complete_order").removeClass('oe_hidden');
			$("#discount_error").hide();
			if(!wk_discount_list.length){
				$(".button.apply_complete_order").addClass('oe_hidden');
				$(".button.apply").addClass('oe_hidden');
			}
			$(".wk_product_discount").on("click",function(e){
				$("#discount_error").hide();
				$(".wk_product_discount").css('background','white');
				var discount_id=parseInt($(this).attr('id'));
				$(this).css('background','#6EC89B');
				for(var i=0; i<wk_discount_list.length; i++ ){
					if( wk_discount_list[i].id == discount_id){
						wk_discount = wk_discount_list[i] ;
						wk_discount_percentage = self.format_currency_no_symbol(wk_discount.discount_percent);
					}
				}

			});
			$(".button.apply").on('click',function(){
				if(wk_discount_percentage != 0){
					order.get_selected_orderline().set_discount(wk_discount_percentage);
					order.get_selected_orderline().custom_discount_reason='';
					$('ul.orderlines li.selected div#custom_discount_reason').text('');
					self.gui.close_popup();
					self.gui.current_screen.order_widget.numpad_state.reset();	
				}
				else{
					 
		   			$(".wk_product_discount").css("background-color","burlywood");
					setTimeout(function(){
						$(".wk_product_discount").css("background-color","");
					},100);
					setTimeout(function(){
						$(".wk_product_discount").css("background-color","burlywood");
					},200);
					setTimeout(function(){
						$(".wk_product_discount").css("background-color","");
					},300);
					setTimeout(function(){
						$(".wk_product_discount").css("background-color","burlywood");
					},400);
					setTimeout(function(){
						$(".wk_product_discount").css("background-color","");
					},500);
					return;
				}
			});
			$(".button.apply_complete_order").on('click',function(){
				if(wk_discount_percentage != 0){
					var orderline_ids = order.get_orderlines();
					for(var i=0; i< orderline_ids.length; i++){
							orderline_ids[i].set_discount(wk_discount_percentage);
							orderline_ids.custom_discount_reason='';
						}
					$('ul.orderlines li div#custom_discount_reason').text('');
					self.gui.close_popup();
					self.gui.current_screen.order_widget.numpad_state.reset();	
				}
				else{
					 
		   			$(".wk_product_discount").css("background-color","burlywood");
					setTimeout(function(){
						$(".wk_product_discount").css("background-color","");
					},100);
					setTimeout(function(){
						$(".wk_product_discount").css("background-color","burlywood");
					},200);
					setTimeout(function(){
						$(".wk_product_discount").css("background-color","");
					},300);
					setTimeout(function(){
						$(".wk_product_discount").css("background-color","burlywood");
					},400);
					setTimeout(function(){
						$(".wk_product_discount").css("background-color","");
					},500);
					return;
				}
			});
			$(".button.cancel").on('click',function(){
				self.gui.close_popup();
				self.gui.current_screen.order_widget.numpad_state.reset();	
			});
			$(".button.customize").on("click",function(){
				var user = self.pos.get_cashier();
				if(self.pos.config.allow_security_pin && user.pos_security_pin){
					var user = self.pos.get_cashier();
					self.wk_ask_password(user.pos_security_pin).then(function(){
						self.gui.show_popup('custom_discount', {
								'title': _t("Customize Discount"),
							});

					});

				}
				else{
					self.gui.show_popup('custom_discount', {
					'title': _t("Customize Discount")
					});
				}

			});
			
		}
	});
	gui.define_popup({ name: 'wk_customer_discount', widget: WkDiscountPopup });
	var WebkulErrorPopup = popup_widget.extend({
		template:'WebkulErrorPopup',
		events: {
				'click #password_ok_button':  'click_password_ok_button',
			},
			click_password_ok_button: function(){
				var self = this;
				this.gui.close_popup();
				self.gui.current_screen.order_widget.numpad_state.reset();
			},
	});
	gui.define_popup({name:'webkul_error_popup', widget: WebkulErrorPopup});


	screens.NumpadWidget.include({

		changedMode: function() {
			var self = this;
			var mode = this.state.get('mode');
			if(mode == 'discount' && self.pos.get_order().get_selected_orderline()){
				if(self.pos.config.discount_ids.length ||self.pos.config.allow_custom_discount){
					self.gui.show_popup('wk_customer_discount', {
					'title': _t("Discount List"),
					});
				}
				else{
					self.gui.show_popup('webkul_error_popup',{
						'title':_t('No Discount Is Available'),
						'body':_t('No discount is available for current POS. Please add discount from configuration')
					});
				}	
			}
			else if(mode == 'discount'){
				self.gui.show_popup('webkul_error_popup',{
					'title':_t('No Selected Orderline'),
					'body':_t('No order line is Selected. Please add or select an Orderline')
				});
			}
			self._super();
		},
	});
});
