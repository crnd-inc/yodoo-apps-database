import base64
import logging
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

RE_RELATIVE_IMG_SRC = re.compile(
    r'(src=["\'])(?!https?://|/|data:)([^"\']+)(["\'])')

GITLAB_RAW_URL = 'https://gitlab.crnd.pro'


class YodooGitSourceBranch(models.Model):
    _inherit = 'yodoo.git.source.branch'

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

            html = self._yodoo_apps_website_rewrite_img_urls_gitlab(
                html, project_path, branch_name, module_name)

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

    def _yodoo_apps_website_fetch_branch_descriptions_github(self, git):
        for mod in self.git_module_ids:
            module = mod.module_id
            module_name = mod.system_name
            branch_name = self.name
            owner = self.git_source_id.github_owner
            repo = self.git_source_id.github_repository
            try:
                html = self._yodoo_apps_website_gh_fetch_file(
                    git, branch_name,
                    '%s/static/description/index.html' % module_name)
            except Exception:
                continue

            html = self._yodoo_apps_website_rewrite_img_urls_github(
                html, owner, repo, branch_name, module_name)

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

    def _yodoo_apps_website_rewrite_img_urls_gitlab(
            self, html, project_path, branch, module_name):
        base_url = '%s/%s/-/raw/%s/%s/static/description/' % (
            GITLAB_RAW_URL, project_path, branch, module_name)
        return RE_RELATIVE_IMG_SRC.sub(
            r'\g<1>%s\2\3' % base_url.replace('\\', '\\\\'), html)

    def _yodoo_apps_website_rewrite_img_urls_github(
            self, html, owner, repo, branch, module_name):
        base_url = (
            'https://raw.githubusercontent.com/%s/%s/%s/'
            '%s/static/description/' % (owner, repo, branch, module_name))
        return RE_RELATIVE_IMG_SRC.sub(
            r'\g<1>%s\2\3' % base_url.replace('\\', '\\\\'), html)
