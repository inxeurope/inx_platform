SELECT
    c.*,
    cc.id as country_id_from_view,
    cc.iso3166_1_alpha_2 as country_iso_alpha2,
    cc.iso3166_1_alpha_3 as country_iso_alpha3,
    cc.official_name_en as country_name,
    u.first_name + ' ' + u.last_name as sales_manager
FROM inx_platform_app_customer c
LEFT JOIN inx_platform_app_countrycode cc ON cc.id = c.country_id
LEFT JOIN inx_platform_app_user u ON u.id = c.sales_employee_id