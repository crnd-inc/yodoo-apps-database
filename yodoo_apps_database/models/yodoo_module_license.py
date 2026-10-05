from odoo import models, fields, api, tools


class YodooModuleLicense(models.Model):
    _name = 'yodoo.module.license'
    _inherit = 'generic.mixin.namesearch.by.fields'
    _description = "Yodoo Module License"
    _order = 'code'
    _log_access = False

    _generic_namesearch_fields = ['name', 'code']

    name = fields.Char(index=True)
    code = fields.Char(required=True, index=True)

    _module_code_uniq = models.Constraint(
        'unique(code)',
        'License code must be unique!')

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for record in self:
            if record.name:
                record.display_name = "%s [%s]" % (
                    record.name, record.code)
            else:
                record.display_name = record.code

    @api.model
    @tools.ormcache('code')
    def _get_license(self, code):
        license_ = self.with_context(active_test=False).search(
            [('code', '=', code)], limit=1)
        if license_:
            return license_.id
        return False

    @api.model
    def get_or_create(self, code):
        license_id = self._get_license(code)
        if not license_id:
            license_id = self.create({
                'code': code,
            }).id
            self.env.registry.clear_cache()
        return license_id
