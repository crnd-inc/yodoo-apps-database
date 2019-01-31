import re
from odoo import models, fields, api, tools, exceptions, _

RE_SERIE = re.compile(r"^(?P<serie_major>\d+)\.(?P<serie_minor>\d+)$")


class OdooSerie(models.Model):
    _name = 'yodoo.serie'
    _description = "Odoo Serie"
    _order = "major DESC, minor DESC"

    name = fields.Char(
        compute='_compute_name',
        inverse='_inverse_name',
        readonly=True, store=True, index=True)
    major = fields.Integer(readonly=True)
    minor = fields.Integer(readonly=True)
    color = fields.Integer()

    module_ids = fields.Many2many(
        comodel_name='yodoo.module',
        relation="yodoo_module_serie_rel",
        column1="serie_id", column2='module_id',
        readonly=True)
    module_count = fields.Integer(
        compute="_compute_module_count",
        readonly=True)

    _sql_constraints = [
        ('name_uniq',
         'unique(name)',
         'Serie name must be uniqe!')
    ]

    @api.depends('major', 'minor')
    def _compute_name(self):
        for record in self:
            record.name = "%d.%d" % (record.major, record.minor)

    def _inverse_name(self):
        for record in self:
            res = RE_SERIE.match(self.name)
            if res:
                record.update({
                    'major': res['serie_major'],
                    'minor': res['serie_minor'],
                })
            else:
                record.update({
                    'major': 0,
                    'monor': 0,
                })

    @api.depends('module_ids')
    def _compute_module_count(self):
        for record in self:
            record.module_count = len(record.module_ids)

    @api.model
    @tools.ormcache('name')
    def _get_serie(self, name):
        serie = self.with_context(active_test=True).search(
            [('name', '=', name)], limit=1)
        if serie:
            return serie.id
        return False

    @api.model
    @tools.ormcache('name')
    def get_or_create(self, name):
        if not RE_SERIE.match(name):
            raise exceptions.ValidationError(_(
                "Serie name ('%s') is not valid") % name)
        serie_id = self._get_serie(name)
        if not serie_id:
            serie_id = self.create({
                'name': name,
            }).id
            self._get_serie.clear_cache(self)
        return serie_id

    @api.multi
    def action_show_modules(self):
        self.ensure_one()
        action = self.env.ref(
            'yodoo_apps_database.action_yodoo_module_view').read()[0]
        action.update({
            'domain': [('serie_ids.id', '=', self.id)],
        })
        return action
