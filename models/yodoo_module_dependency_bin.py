from odoo import models, fields, api, tools


class YodooModuleDependencyBinary(models.Model):
    _name = 'yodoo.module.dependency.binary'
    _inherit = 'generic.mixin.namesearch.by.fields'
    _description = "Yodoo Module Binary Dependency"
    _order = 'name'
    _log_access = False

    _generic_namesearch_fields = ['name', 'apt_package']

    name = fields.Char(index=True, required=True, readonly=True)
    apt_package = fields.Char(index=True)

    module_ids = fields.Many2manyView(
        comodel_name='yodoo.module',
        relation='yodoo_module_dependency_binary_rel_view',
        column1='dependency_id',
        column2='module_id',
        string="Yodoo Modules",
        readonly=True)
    module_count = fields.Integer(
        compute='_compute_module_count', readonly=True)

    active = fields.Boolean(default=True, index=True)

    @api.depends('module_ids')
    def _compute_module_count(self):
        for record in self:
            record.module_count = len(record.module_ids)

    def name_get(self):
        res = []
        for record in self:
            if record.apt_package:
                res += [
                    (record.id, "%s [%s]" % (record.name, record.apt_package))
                ]
            else:
                res += [(record.id, record.name)]
        return res

    @api.model
    @tools.ormcache('name')
    def _get_bin_dependency(self, name):
        dependency = self.with_context(active_test=False).search(
            [('name', '=', name)], limit=1)
        if dependency:
            return dependency.id
        return False

    @api.model
    def get_or_create(self, name):
        dependency_id = self._get_bin_dependency(name)
        if not dependency_id:
            dependency_id = self.create({
                'name': name,
            }).id
            self._get_bin_dependency.clear_cache(self)
        return dependency_id

    def action_show_modules(self):
        self.ensure_one()
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'yodoo_apps_database.action_yodoo_module_view',
            domain=[('dependency_bin_ids.id', '=', self.id)])
