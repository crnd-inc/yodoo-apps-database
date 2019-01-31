from odoo import models, fields, api


class OdooModuleSerie(models.Model):
    _name = 'yodoo.module.serie'
    _description = "Odoo Module Serie"

    module_id = fields.Many2one(
        'yodoo.module', required=True, readonly=True, index=True,
        ondelete='cascade')
    serie_id = fields.Many2one(
        'yodoo.serie', required=True, readonly=True, index=True,
        ondelete='cascade')

    # Version
    version_ids = fields.One2many(
        'yodoo.module.version', 'module_serie_id', readonly=True)
    version_count = fields.Integer(
        compute='_compute_last_version',
        store=True, readonly=True)
    last_version_id = fields.Many2one(
        'yodoo.module.version', readonly=True, store=True,
        compute='_compute_last_version')

    _sql_constraints = [
        ('module_serie_uniq',
         'unique(module_id, serie_id)',
         'Module and serie must be unique!'),
    ]

    @api.depends('version_ids')
    def _compute_last_version(self):
        for record in self:
            last_version = self.env['yodoo.module.version'].search(
                [('module_serie_id', '=', record.id)], limit=1)
            if last_version:
                record.last_version_id = last_version
            else:
                record.last_version_id = False
            record.version_count = len(record.version_ids)

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            res += [(
                record.id,
                "%s [%s]" % (record.module_id.system_name,
                             record.serie_id.display_name),
            )]
        return res

    @api.model
    def get_or_create(self, module_id, serie_id):
        module_serie = self.with_context(active_test=False).search(
            [('module_id', '=', module_id),
             ('serie_id', '=', serie_id)], limit=1)
        if not module_serie:
            module_serie = self.create({
                'module_id': module_id,
                'serie_id': serie_id,
            })
        return module_serie

    @api.multi
    def action_show_versions(self):
        self.ensure_one()
        action = self.env.ref(
            'yodoo_apps_database.action_yodoo_module_version_view').read()[0]
        action.update({
            'domain': [('module_serie_id', '=', self.id)],
        })
        return action
