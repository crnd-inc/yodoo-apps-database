from odoo import models, fields, api, tools
from odoo.osv import expression


class YodooModuleLicense(models.Model):
    _name = 'yodoo.module.license'
    _description = "Yodoo Module License"
    _order = 'code'

    name = fields.Char(index=True)
    code = fields.Char(required=True, index=True)

    _sql_constraints = [
        ('module_code_uniq',
         'unique(code)',
         'License code must be unique!'),
    ]

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            if record.name:
                res += [(record.id, "%s [%s]" % (record.name, record.code))]
            else:
                res += [(record.id, record.code)]
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=10):
        if not args:
            args = []
        if name:
            domain = [
                [('name', operator, name)],
                [('code', operator, name)],
            ]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = expression.AND(domain)
            else:
                domain = expression.OR(domain)

            domain = expression.AND([domain, args])
            records = self.search(domain, limit=limit)
        else:
            records = self.search(args, limit=limit)

        return records.name_get()

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
            self._get_license.clear_cache(self)
        return license_id
