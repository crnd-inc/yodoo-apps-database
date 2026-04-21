import base64
import logging
import posixpath
import re

from odoo import models

_logger = logging.getLogger(__name__)

try:
    import gitlab as gitlab_lib
except (ImportError, IOError):
    gitlab_lib = None

try:
    import github as github_lib
except (ImportError, IOError):
    github_lib = None

RE_IMG_SRC = re.compile(
    r'<img\b[^>]*?\bsrc=["\']([^"\']+)["\']', re.IGNORECASE)

IMAGE_TASK_XMLID = (
    'yodoo_apps_website.kw_html_image2attachment_task_module_description')


class YodooGitSourceBranch(models.Model):
    _inherit = 'yodoo.git.source.branch'

    # Restores BaseModel.CONCURRENCY_CHECK_FIELD removed in Odoo 18;
    # referenced by generic.mixin.refresh.view on every write.
    CONCURRENCY_CHECK_FIELD = '__last_update'

    def _yodoo_apps_website_enqueue_image_task(self, module):
        task = self.env.ref(IMAGE_TASK_XMLID, raise_if_not_found=False)
        if not task:
            return
        Line = self.env['kw.html_image2attachment.task.line'].sudo()
        existing = Line.search([
            ('task_id', '=', task.id),
            ('res_id', '=', module.id),
            ('state', 'in', ('new', 'error')),
        ], limit=1)
        if existing:
            existing.write({'state': 'new', 'result': False})
        else:
            Line.create({'task_id': task.id, 'res_id': module.id})

    def _yodoo_apps_website_resolve_repo_path(self, src, module_name):
        if src.startswith(('http://', 'https://', 'data:', '/')):
            return None
        base = '%s/static/description' % module_name
        return posixpath.normpath(posixpath.join(base, src))

    def _yodoo_apps_website_create_image_attachment(
            self, module, filename, data_b64):
        return self.env['ir.attachment'].sudo().create({
            'name': filename,
            'type': 'binary',
            'datas': data_b64,
            'res_model': module._name,
            'res_id': module.id,
            'kw_is_html2attachment_image': True,
        })

    def _yodoo_apps_website_inline_images(
            self, module, module_name, html, fetch_binary):
        if not html:
            return html
        replacements = {}
        for src in set(RE_IMG_SRC.findall(html)):
            if src in replacements:
                continue
            repo_path = self._yodoo_apps_website_resolve_repo_path(
                src, module_name)
            if not repo_path:
                continue
            data_b64 = fetch_binary(repo_path)
            if not data_b64:
                continue
            filename = posixpath.basename(repo_path) or 'image.png'
            attachment = self._yodoo_apps_website_create_image_attachment(
                module, filename, data_b64)
            replacements[src] = '/web/image/%s' % attachment.id
        for src, local_url in replacements.items():
            html = re.sub(
                r'(src=["\'])%s(["\'])' % re.escape(src),
                r'\g<1>%s\g<2>' % local_url,
                html,
            )
        return html

    def _yodoo_apps_website_fetch_branch_descriptions_gitlab(
            self, git, project_path):
        for mod in self.git_module_ids:
            module = mod.module_id
            module_name = mod.system_name
            branch_name = self.name
            try:
                html = self._yodoo_apps_website_gl_fetch_file(
                    git, branch_name,
                    '%s/static/description/index.html' % module_name)
            except Exception:
                continue

            html = self._yodoo_apps_website_inline_images(
                module.sudo(), module_name, html,
                lambda p: self._yodoo_apps_website_gl_fetch_binary(
                    git, branch_name, p))

            vals = {
                'yodoo_apps_website_description_html': html,
            }

            icon_data = self._yodoo_apps_website_gl_fetch_binary(
                git, branch_name,
                '%s/static/description/icon.png' % module_name)
            if icon_data:
                vals['yodoo_apps_website_icon'] = icon_data

            cover_data = self._yodoo_apps_website_gl_fetch_binary(
                git, branch_name,
                '%s/static/description/cover.png' % module_name)
            if cover_data:
                vals['yodoo_apps_website_cover'] = cover_data

            module.sudo().write(vals)
            self._yodoo_apps_website_enqueue_image_task(module)

    def _yodoo_apps_website_fetch_branch_descriptions_github(self, git):
        for mod in self.git_module_ids:
            module = mod.module_id
            module_name = mod.system_name
            branch_name = self.name
            try:
                html = self._yodoo_apps_website_gh_fetch_file(
                    git, branch_name,
                    '%s/static/description/index.html' % module_name)
            except Exception:
                continue

            html = self._yodoo_apps_website_inline_images(
                module.sudo(), module_name, html,
                lambda p: self._yodoo_apps_website_gh_fetch_binary(
                    git, branch_name, p))

            vals = {
                'yodoo_apps_website_description_html': html,
            }

            icon_data = self._yodoo_apps_website_gh_fetch_binary(
                git, branch_name,
                '%s/static/description/icon.png' % module_name)
            if icon_data:
                vals['yodoo_apps_website_icon'] = icon_data

            cover_data = self._yodoo_apps_website_gh_fetch_binary(
                git, branch_name,
                '%s/static/description/cover.png' % module_name)
            if cover_data:
                vals['yodoo_apps_website_cover'] = cover_data

            module.sudo().write(vals)
            self._yodoo_apps_website_enqueue_image_task(module)

    def _yodoo_apps_website_gl_fetch_file(self, git, branch, path):
        f = git.gl_project.files.get(ref=branch, file_path=path)
        return f.decode().decode('utf-8')

    def _yodoo_apps_website_gl_fetch_binary(self, git, branch, path):
        try:
            f = git.gl_project.files.get(ref=branch, file_path=path)
            return base64.b64encode(base64.b64decode(f.content))
        except Exception:
            return False

    def _yodoo_apps_website_gh_fetch_file(self, git, branch, path):
        content = git.gh_repo.get_contents(path, ref=branch)
        return content.decoded_content.decode('utf-8')

    def _yodoo_apps_website_gh_fetch_binary(self, git, branch, path):
        try:
            content = git.gh_repo.get_contents(path, ref=branch)
            return base64.b64encode(content.decoded_content)
        except Exception:
            return False
