from odoo import models, fields, api, tools


class YodooModuleCategory(models.Model):
    _name = 'yodoo.module.category'
    _description = "Yodoo Module Category"
    _order = 'name'

    name = fields.Char(required=True, index=True)

    _sql_constraints = [
        ('module_name_uniq',
         'unique(name)',
         'Category name must be unique!'),
    ]

    @api.model
    @tools.ormcache('name')
    def _get_category(self, name):
        category = self.with_context(active_test=False).search(
            [('name', '=', name)], limit=1)
        if category:
            return category.id
        return False

    @api.model
    def get_or_create(self, name):
        category_id = self._get_category(name)
        if not category_id:
            category_id = self.create({
                'name': name,
            }).id
            self._get_category.clear_cache(self)
        return category_id
