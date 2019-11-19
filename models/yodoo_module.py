from odoo import models, fields, api


class YodooModule(models.Model):
    _inherit = 'yodoo.module'

    product_template_id = fields.Many2one(
        'product.template', 'Product Template', readonly=True)
    product_template_attr_line_serie_id = fields.Many2one(
        'product.template.attribute.line', readonly=True)

    def _create_or_update_product_template(self):
        self.ensure_one()

        company = self.env.user.company_id
        date = self._context.get('date') or fields.Date.today()
        uom = self.env.ref('uom.product_uom_unit')
        serie_attribute = self.env.ref(
            'yodoo_apps_sale.product_attribute_odoo_serie')

        # Prepare data for mapping serie - variant
        module_serie_by_attr_value_map = {}
        serie_attribute_values = self.env['product.attribute.value'].browse()
        for module_serie in self.module_serie_ids:
            serie_attr_val = module_serie.serie_id.product_attribute_value_id
            module_serie_by_attr_value_map[serie_attr_val] = module_serie
            serie_attribute_values += serie_attr_val

        # Convert price to company price
        price = self.currency_id._convert(
            self.price, company.currency_id, company, date)

        # Update or create product
        if self.product_template_id:
            self.product_template_id.write({
                'list_price': price,
                'standard_price': price,
                'default_code': self.system_name,
            })
            self.product_template_attr_line_serie_id.write({
                'value_ids': [(6, 0, serie_attribute_values.ids)],
            })
        else:
            self.product_template_id = self.env['product.template'].create({
                'name': self.name,
                'list_price': price,
                'standard_price': price,
                'type': 'service',
                'default_code': self.system_name,
                'uom_id': uom.id,
                'uom_po_id': uom.id,
                'categ_id': company.yodoo_default_product_category_id.id,
                'attribute_line_ids': [(0, 0, {
                    'attribute_id': serie_attribute.id,
                    'value_ids': [(6, 0, serie_attribute_values.ids)],
                })],
            })
            self.product_template_attr_line_serie_id = (
                self.product_template_id.attribute_line_ids.filtered(
                    lambda r: r.attribute_id == serie_attribute))

        # Map product variant to module serie
        for product_variant in self.product_template_id.product_variant_ids:
            serie_attr_val = product_variant.attribute_value_ids.filtered(
                lambda r: r.attribute_id == serie_attribute)
            if len(serie_attr_val) != 1:
                # Strange variat that has no serie or has multiple series
                continue
            module_serie = module_serie_by_attr_value_map[serie_attr_val]
            module_serie.product_variant_id = product_variant
            product_variant.write({
                'default_code': '%s_%s' % (
                    self.system_name, module_serie.serie_id.name),
            })

    def action_create_or_update_product(self):
        for record in self:
            record._create_or_update_product_template()
