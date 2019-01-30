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

    @api.model
    @tools.ormcache('name')
    def get_or_create(self, name):
        if not RE_SERIE.match(name):
            raise exceptions.ValidationError(_(
                "Serie name ('%s') is not valid") % name)
        serie = self.with_context(active_test=True).search(
            [('name', '=', name)], limit=1)
        if not serie:
            serie = self.create({
                'name': name,
            })
        return serie.id
