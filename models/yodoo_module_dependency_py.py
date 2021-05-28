from odoo import models, fields, api, tools


class YodooModuleDependencyPython(models.Model):
    _name = 'yodoo.module.dependency.python'
    _inherit = 'generic.mixin.namesearch.by.fields'
    _description = "Yodoo Module Python Dependency"
    _order = 'name'
    _log_access = False

    _generic_namesearch_fields = ['name', 'pypi_package']

    name = fields.Char(index=True, required=True, readonly=True)
    pypi_package = fields.Char(index=True)

    active = fields.Boolean(default=True, index=True)

    def name_get(self):
        res = []
        for record in self:
            if record.pypi_package:
                res += [
                    (record.id, "%s [%s]" % (record.name, record.pypi_package))
                ]
            else:
                res += [(record.id, record.name)]
        return res

    @api.model
    @tools.ormcache('name')
    def _get_python_dependency(self, name):
        dependency = self.with_context(active_test=False).search(
            [('name', '=', name)], limit=1)
        if dependency:
            return dependency.id
        return False

    @api.model
    def get_or_create(self, name):
        dependency_id = self._get_python_dependency(name)
        if not dependency_id:
            dependency_id = self.create({
                'name': name,
            }).id
            self._get_python_dependency.clear_cache(self)
        return dependency_id
