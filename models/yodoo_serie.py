from odoo import models, fields, api


class YodooSerie(models.Model):
    _inherit = 'yodoo.serie'

    product_attribute_value_id = fields.Many2one(
        'product.attribute.value', readonly=True)

    @api.model
    def _generate_product_attribute(self, name):
        AttrValue = self.env['product.attribute.value']
        attribute = self.env.ref(
            'yodoo_apps_sale.product_attribute_odoo_serie')
        attribute_value = AttrValue.search([
            ('name', '=', name),
            ('attribute_id', '=', attribute.id),
        ], limit=1)

        if not attribute_value:
            attribute_value = AttrValue.create({
                'attribute_id': attribute.id,
                'name': name,
            })
        return attribute_value

    @api.model
    def create(self, vals):
        name = vals.get('name', False)
        attribute_value = self._generate_product_attribute(name)
        vals = dict(
            vals,
            product_attribute_value_id=attribute_value.id)

        return super(YodooSerie, self).create(vals)
