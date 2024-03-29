from odoo import models, fields, api, tools


class YodooModuleCategory(models.Model):
    _name = 'yodoo.module.category'
    _description = "Yodoo Module Category"
    _order = 'name'

    name = fields.Char(required=True, index=True)
    module_ids = fields.One2many(
        'yodoo.module', 'category_id', readonly=True)
    module_count = fields.Integer(
        compute='_compute_module_count', readonly=True)

    _sql_constraints = [
        ('module_name_uniq',
         'unique(name)',
         'Category name must be unique!'),
    ]

    @api.depends('module_ids')
    def _compute_module_count(self):
        for record in self:
            record.module_count = len(record.module_ids)

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

    def action_show_modules(self):
        self.ensure_one()
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'yodoo_apps_database.action_yodoo_module_view',
            domain=[('category_id', '=', self.id)])
