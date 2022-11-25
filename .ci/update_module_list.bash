#!/usr/bin/env bash

set -e;

SCRIPT=$(readlink -f "$0");
SCRIPT_NAME=$(basename "$SCRIPT");
SCRIPT_DIR=$(dirname "$SCRIPT");
WORKDIR=$(pwd);
PROJECT_DIR=$(readlink -f "$SCRIPT_DIR/..");

MODULES_PATH="$PROJECT_DIR/yodoo_apps_database/data/yodoo.module.csv";
MODULE_SERIES_PATH="$PROJECT_DIR/yodoo_apps_database/data/yodoo.module.serie.csv";


# Signature
#     update_list_for_serie <serie_major> <serie_minor> <modules_path> <module_series_path>
function update_list_for_serie {
    local serie_major="$1";
    local serie_minor="$2";
    local serie="$serie_major.$serie_minor";
    local modules_path="$3";
    local module_series_path="$4";
    local addons=( );

    if [ "$serie_major" -gt 10 ]; then
        # In case of odoo 11+ we have to use python3
        mapfile -t addons < <(docker run -v "$PROJECT_DIR/.ci:/yodoo_tools/" --rm "odoo:$serie" python3 /yodoo_tools/find_odoo_addons.py);
    else
        mapfile -t addons < <(docker run -v "$PROJECT_DIR/.ci:/yodoo_tools/" --rm "odoo:$serie" python /yodoo_tools/find_odoo_addons.py);
    fi

    for addon in "${addons[@]}"; do
        if [[ "$addon" == theme_* ]] && [[ "$addon" != "theme_default" ]] && [[ "$addon" != "theme_bootswatch" ]]; then
            # Skip themes except default ones, because they are not included in standard odoo,
            # but they are included in odoo docker images
            continue
        fi
        if [ -n "$addon" ]; then
            echo "\"odoo_community_module__${addon}\",\"${addon}\"" >> "$modules_path";
            echo "\"odoo_community_module__${addon}__yodoo_serie__${serie_major}_${serie_minor}\",\"odoo_community_module__${addon}\",\"yodoo_serie__${serie_major}_${serie_minor}\",\"True\"" >> "$module_series_path";
        fi
    done
}

# Start new files with csv header
echo "\"id\",\"system_name\"" > "$MODULES_PATH.tmp";
echo "\"id\",\"module_id:id\",\"serie_id:id\",\"is_odoo_community_addon\"" > "$MODULE_SERIES_PATH.tmp";

# Update module lists
update_list_for_serie 8 0 "$MODULES_PATH.tmp" "$MODULE_SERIES_PATH.tmp";
update_list_for_serie 9 0 "$MODULES_PATH.tmp" "$MODULE_SERIES_PATH.tmp";
update_list_for_serie 10 0 "$MODULES_PATH.tmp" "$MODULE_SERIES_PATH.tmp";
update_list_for_serie 11 0 "$MODULES_PATH.tmp" "$MODULE_SERIES_PATH.tmp";
update_list_for_serie 12 0 "$MODULES_PATH.tmp" "$MODULE_SERIES_PATH.tmp";
update_list_for_serie 13 0 "$MODULES_PATH.tmp" "$MODULE_SERIES_PATH.tmp";
update_list_for_serie 14 0 "$MODULES_PATH.tmp" "$MODULE_SERIES_PATH.tmp";
update_list_for_serie 15 0 "$MODULES_PATH.tmp" "$MODULE_SERIES_PATH.tmp";
update_list_for_serie 16 0 "$MODULES_PATH.tmp" "$MODULE_SERIES_PATH.tmp";

# Remove duplicates from files
cat "$MODULES_PATH.tmp" | sort -u > "$MODULES_PATH";
cat "$MODULE_SERIES_PATH.tmp" | uniq -u > "$MODULE_SERIES_PATH";

# Cleanup, remove temporary files
rm "$MODULES_PATH.tmp"
rm "$MODULE_SERIES_PATH.tmp"
