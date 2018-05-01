# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import base64
from openerp import api, fields, models
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class BindingDataMixin(models.AbstractModel):
    _name = 'binding.data.mixin'

    data = fields.Serialized()

    def fields_get(self):
        res = super(BindingDataMixin, self).fields_get()
        res['data']['translate'] = True
        return res

    def write(self, vals):
        if 'data' in vals:
            self.ensure_one()
            lang = self._context.get('lang', 'en_US')
            data = self.data
            data[lang] = vals['data']
            vals['data'] = data
        return super(BindingDataMixin, self).write(vals)

    def create(self, vals):
        if 'data' in vals:
            lang = self._context.get('lang', 'en_US')
            vals['data'] = {lang: vals['data']}
        return super(BindingDataMixin, self).write(vals)


class MagentoProductProduct(models.Model):
    _inherit = ['magento.product.product', 'binding.data.mixin']
    _name = 'magento.product.product'


class MagentoProductTemplate(models.Model):
    _inherit = ['magento.product.template', 'binding.data.mixin']
    _name = 'magento.product.template'


class MagentoProductCategory(models.Model):
    _inherit = ['magento.product.category', 'binding.data.mixin']
    _name = 'magento.product.category'


class ProductImportMapper(Component):
    _inherit = 'magento.product.product.import.mapper'

    @mapping
    def data(self, record):
        return {'data': record}


class ProductCategoryImportMapper(Component):
    _inherit = 'magento.product.category.import.mapper'

    @mapping
    def data(self, record):
        return {'data': record}


class CatalogImageImporter(Component):
    _inherit = 'magento.product.image.importer'

    def _get_or_create_image(self, image_data):
        binary = self._get_binary_image(image_data)
        image = self.env['storage.image'].search([
            ('magento_file', '=', image_data['file'])])
        if image:
            return image
        else:
            if image_data['label']:
                filename, extension = os.path.splitext(image_data['file'])
                name = image_data['label'] + extension
            else:
                name = image_data['file'][5:]
            return self.env['storage.image'].create({
                'name': name,
                'data': base64.b64encode(binary),
                'magento_file': image_data['file'],
                })

    def run(self, external_id, binding):
        self.external_id = external_id
        if binding._name == 'magento.product.template':
            img_vals = {
                'product_tmpl_id': binding.odoo_id.id,
                'template_binding_id': binding.id,
                }
        else:
            img_vals = {
                'product_tmpl_id': binding.product_tmpl_id.id,
                'product_binding_id': binding.id,
                }
        images = self._get_images()
        for image_data in self._sort_images(images):
            image = self._get_or_create_image(image_data)
            product_image = self.env['product.image'].search([
                ('product_tmpl_id', '=', img_vals['product_tmpl_id']),
                ('image_id', '=', image.id),
                ])
            if not product_image:
                vals = img_vals.copy()
                vals['image_id'] = image.id
                self.env['product.image'].create(vals)
