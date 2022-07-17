from odoo.addons.generic_mixin.tools.migration_utils import ensure_version


@ensure_version('0.4.0')
def migrate(cr, installed_version):
    cr.execute("""
        INSERT INTO ir_model_data
            (module, name, model, res_id, noupdate)
        SELECT 'yodoo_apps_database',
               format('yodoo_serie__%s_%s', ys.major, ys.minor),
               'yodoo.serie',
               ys.id,
               True
        FROM yodoo_serie AS ys
    """)
