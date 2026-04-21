import logging

from odoo import models

from ..tools.odoo_requirements import parse_odoo_requirements

_logger = logging.getLogger(__name__)

try:
    import gitlab as gitlab_lib
except (ImportError, IOError):
    gitlab_lib = None

try:
    import github as github_lib
except (ImportError, IOError):
    github_lib = None


class YodooGitSource(models.Model):
    _inherit = 'yodoo.git.source'

    # Restores the constant removed from BaseModel in Odoo 18; referenced
    # by generic.mixin.refresh.view._auto_refresh_view_on_field_changes_system.
    CONCURRENCY_CHECK_FIELD = '__last_update'

    def _action_sync_gitlab(self, branch_names=None):
        super()._action_sync_gitlab(branch_names=branch_names)
        if not self.gitlab_project_path:
            return
        self._yodoo_apps_website_fetch_descriptions_gitlab(branch_names)
        self._yodoo_apps_website_sync_odoo_requirements_gitlab()

    def _action_sync_github(self, branch_names=None):
        super()._action_sync_github(branch_names=branch_names)
        if not self.github_owner or not self.github_repository:
            return
        self._yodoo_apps_website_fetch_descriptions_github(branch_names)
        self._yodoo_apps_website_sync_odoo_requirements_github()

    def _yodoo_apps_website_fetch_descriptions_gitlab(self, branch_names=None):
        from odoo.addons.yodoo_apps_git_source.utils import GitlabWrapper
        try:
            git = GitlabWrapper(self.env)
            git.connect()
            git.open_repo(self.gitlab_project_id)
        except Exception:
            _logger.warning(
                'Cannot connect to GitLab for description fetch: %s',
                self.name)
            return

        for branch in self.git_branch_ids.filtered(
                lambda b: b.scan and b.is_standard):
            if branch_names and branch.name not in branch_names:
                continue
            branch._yodoo_apps_website_fetch_branch_descriptions_gitlab(
                git, self.gitlab_project_path)

    def _yodoo_apps_website_fetch_descriptions_github(self, branch_names=None):
        from odoo.addons.yodoo_apps_git_source.utils import GithubWrapper
        try:
            git = GithubWrapper(self.env)
            git.connect()
            git.open_repo(self.github_owner, self.github_repository)
        except Exception:
            _logger.warning(
                'Cannot connect to GitHub for description fetch: %s',
                self.name)
            return

        for branch in self.git_branch_ids.filtered(
                lambda b: b.scan and b.is_standard):
            if branch_names and branch.name not in branch_names:
                continue
            branch._yodoo_apps_website_fetch_branch_descriptions_github(
                git)

    def _yodoo_apps_website_sync_odoo_requirements_gitlab(self):
        from odoo.addons.yodoo_apps_git_source.utils import GitlabWrapper
        try:
            git = GitlabWrapper(self.env)
            git.connect()
            git.open_repo(self.gitlab_project_id)
        except Exception:
            return

        branch = self.git_branch_ids.filtered(
            lambda b: b.scan and b.is_standard)[:1]
        if not branch:
            return

        try:
            f = git.gl_project.files.get(
                ref=branch.name, file_path='odoo_requirements.txt')
            content = f.decode().decode('utf-8')
        except Exception:
            return

        requirements = parse_odoo_requirements(content)
        self._yodoo_apps_website_ensure_git_sources(
            requirements, git.connection)

    def _yodoo_apps_website_sync_odoo_requirements_github(self):
        from odoo.addons.yodoo_apps_git_source.utils import GithubWrapper
        try:
            git = GithubWrapper(self.env)
            git.connect()
            git.open_repo(self.github_owner, self.github_repository)
        except Exception:
            return

        branch = self.git_branch_ids.filtered(
            lambda b: b.scan and b.is_standard)[:1]
        if not branch:
            return

        try:
            file_content = git.gh_repo.get_contents(
                'odoo_requirements.txt', ref=branch.name)
            content = file_content.decoded_content.decode('utf-8')
        except Exception:
            return

        requirements = parse_odoo_requirements(content)
        self._yodoo_apps_website_ensure_git_sources(requirements)

    def _yodoo_apps_website_ensure_git_sources(
            self, requirements, gl_connection=None):
        GitSource = self.env['yodoo.git.source'].sudo()
        for req in requirements:
            try:
                if req['type'] == 'github':
                    self._yodoo_apps_website_ensure_github_source(
                        GitSource, req['owner'], req['repo'])
                elif req['type'] == 'gitlab' and gl_connection:
                    self._yodoo_apps_website_ensure_gitlab_source(
                        GitSource, gl_connection, req['path'])
            except Exception:
                _logger.warning(
                    'Cannot create git source for requirement: %s',
                    req, exc_info=True)

    def _yodoo_apps_website_ensure_github_source(
            self, GitSource, owner, repo):
        existing = GitSource.search([
            ('source_type', '=', 'github'),
            ('github_owner', '=', owner),
            ('github_repository', '=', repo),
        ], limit=1)
        if existing:
            return existing

        _logger.info(
            'Auto-creating GitHub git source: %s/%s', owner, repo)
        return GitSource.create({
            'name': '%s/%s' % (owner, repo),
            'source_type': 'github',
            'github_owner': owner,
            'github_repository': repo,
            'enable_sync': True,
        })

    def _yodoo_apps_website_ensure_gitlab_source(
            self, GitSource, gl_connection, path):
        existing = GitSource.search([
            ('source_type', '=', 'crnd'),
            ('gitlab_project_path', '=', path),
        ], limit=1)
        if existing:
            return existing

        try:
            project = gl_connection.projects.get(path)
        except Exception:
            _logger.warning(
                'GitLab project not found: %s', path)
            return

        existing_by_id = GitSource.search([
            ('source_type', '=', 'crnd'),
            ('gitlab_project_id', '=', project.id),
        ], limit=1)
        if existing_by_id:
            return existing_by_id

        _logger.info(
            'Auto-creating GitLab git source: %s (ID: %s)',
            path, project.id)
        return GitSource.create({
            'name': project.attributes.get('name', path),
            'source_type': 'crnd',
            'gitlab_project_id': project.id,
            'gitlab_project_path': project.path_with_namespace,
            'enable_sync': True,
        })
