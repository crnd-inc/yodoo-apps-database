"""
This script have to be ran in odoo container.
It will find all addons available in that odoo container
and print them as a list.

This script is used to automatically fill info about addons in yodoo apps
database
"""

import os
import sys
import pkg_resources

# Import odoo package
try:
    # Odoo 10.0+

    # this is required if there are addons installed via setuptools_odoo
    # Also, this needed to make odoo10 work, if running this script with
    # current working directory set to project root
    if sys.version_info.major == 2:
        pkg_resources.declare_namespace('odoo.addons')

    # import odoo itself
    import odoo
    import odoo.release  # to avoid 9.0 with odoo.py on path
except (ImportError, KeyError):
    try:
        # Odoo 9.0 and less versions
        import openerp as odoo
    except ImportError:
        raise

if odoo.release.version_info < (8,):
    raise ImportError(
        "Odoo version %s is not supported!" % odoo.release.version_info)


def is_odoo_addon(addon_path):
    if os.path.exists(os.path.join(addon_path, '__manifest__.py')):
        return True
    if os.path.exists(os.path.join(addon_path, '__openerp__.py')):
        return True
    return False


def find_addons_in_path(path):
    for root, dirs, files in os.walk(path):
        if is_odoo_addon(root):
            yield os.path.basename(root)


def find_addons():
    addons_paths = [
        a.strip()
        for a in odoo.tools.config.options.get('addons_path').split(',')
    ]
    addons_paths += os.path.abspath(
        os.path.join(
            os.path.dirname(odoo.__file__), 'addons')
    )

    for apath in addons_paths:
        for addon in find_addons_in_path(apath):
            yield addon


def main():
    print("\n".join(sorted(set(find_addons()))))


if __name__ == '__main__':
    main()
