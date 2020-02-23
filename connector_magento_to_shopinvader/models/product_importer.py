# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import base64
from openerp import api, fields, models
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
import logging
_logger = logging.getLogger(__name__)


class BindingDataMixin(models.AbstractModel):
    _name = 'binding.data.mixin'

    updated = fields.Boolean()
    data = fields.Serialized()

    def _synchronize_magento_record(self, backend_id):
        backend = self.env['magento.backend'].browse(backend_id)
        with backend.work_on(self._name) as work:
            adapter = work.component(usage='backend.adapter')
            records = self.search([
                ('backend_id', '=', backend_id),
                ('updated', '=', False),
            ])
            total = len(records)
            missing_ids = []
            for idx, record in enumerate(records):
                if idx % 10 == 0:
                    _logger.info('progress {} / {}'.format(idx, total))
                try:
                    data = {}
                    for storeview in backend.mapped(
                            'website_ids.store_ids.storeview_ids'):
                        data[storeview.code] = adapter.read(
                            record.external_id,
                            storeview_id=storeview.external_id)
                except Exception as e:
                    missing_ids.append(record.id)
                record.write({'updated': True, 'data': data})
                self._cr.commit()
        return missing_ids


class MagentoProductProduct(models.Model):
    _inherit = ['magento.product.product', 'binding.data.mixin']
    _name = 'magento.product.product'


class MagentoProductTemplate(models.Model):
    _inherit = ['magento.product.template', 'binding.data.mixin']
    _name = 'magento.product.template'


class MagentoProductCategory(models.Model):
    _inherit = ['magento.product.category', 'binding.data.mixin']
    _name = 'magento.product.category'


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
            product_image = self.env['product.image.relation'].search([
                ('product_tmpl_id', '=', img_vals['product_tmpl_id']),
                ('image_id', '=', image.id),
                ])
            if not product_image:
                vals = img_vals.copy()
                vals['image_id'] = image.id
                self.env['product.image.relation'].create(vals)
