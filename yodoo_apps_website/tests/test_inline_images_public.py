from odoo.tests.common import TransactionCase

PNG_B64 = (
    b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwAD'
    b'hgGAWjR9awAAAABJRU5ErkJggg==')


class TestInlineImagesPublic(TransactionCase):
    """ Images inlined into yodoo_apps_website_description_html are
        shown to anonymous visitors of the modules catalog, so the
        attachments must be public; otherwise /web/image returns a
        placeholder because portal/public users have no ACL on
        ir.attachment.
    """

    def setUp(self):
        super().setUp()
        self.source = self.env['yodoo.git.source'].create({
            'name': 'Test Source Public Images',
        })
        self.branch = self.env['yodoo.git.source.branch'].create({
            'name': '18.0',
            'git_source_id': self.source.id,
            'yodoo_serie_id': self.env.ref(
                'yodoo_apps_database.yodoo_serie__18_0').id,
        })
        self.module = self.env['yodoo.module'].create({
            'name': 'Test Module Public Images',
            'system_name': 'test_module_public_images',
        })

    def test_inlined_image_attachment_is_public(self):
        html = '<p><img src="static/description/shot.png"/></p>'
        result = self.branch._yodoo_apps_website_inline_images(
            self.module, 'test_module_public_images', html,
            lambda path: PNG_B64)
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'yodoo.module'),
            ('res_id', '=', self.module.id),
            ('kw_is_html2attachment_image', '=', True),
        ])
        self.assertEqual(len(attachment), 1)
        self.assertTrue(attachment.public)
        self.assertIn('/web/image/%s' % attachment.id, result)
