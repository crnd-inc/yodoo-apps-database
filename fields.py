from odoo.fields import Many2many


class Many2manyView(Many2many):
    """ This field have to be used when m2m relation is view
        and thus we do not need to create relation table.
    """

    def update_db(self, model, columns):
        # Do nothing. View have to be created elsewhere
        return True
