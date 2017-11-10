# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "POS Custom Discount",
  "summary"              :  "This module allows the seller to apply discount on single product as well as complete order in pos session.",
  "category"             :  "Point of sale",
  "version"              :  "1.3",
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-POS-Custom-Discount.html",
  "description"          :  """http://webkul.com/blog/odoo-pos-custom-discount/""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=pos_custom_discounts&version=10.0",
  "depends"              :  ['point_of_sale'],
  "data"                 :  [
                             'views/pos_custom_discounts_view.xml',
                             'views/template.xml',
                             'security/ir.model.access.csv',
                            ],
  "demo"                 :  ['data/pos_custom_discount_demo.xml'],
  "qweb"                 :  ['static/src/xml/pos_custom_discounts.xml'],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  49,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
}