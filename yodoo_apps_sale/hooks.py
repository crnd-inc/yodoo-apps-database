def _post_init_hook(env):
    Serie = env['yodoo.serie']
    for serie in Serie.with_context(active_test=False).search([]):
        serie.product_attribute_value_id = Serie._generate_product_attribute(
            serie.name)
