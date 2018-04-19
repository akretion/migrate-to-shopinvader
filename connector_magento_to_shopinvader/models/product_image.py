# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class StorageImage(models.Model):
    _inherit = 'storage.image'

    magento_file = fields.Char()


class ProductImage(models.Model):
    _inherit = 'product.image'

    template_binding_id = fields.Many2one(
        'magento.product.template')
    product_binding_id = fields.Many2one(
        'magento.product.product')
