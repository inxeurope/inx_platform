DECLARE @ViewExists INT;
SET @ViewExists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.VIEWS 
    WHERE TABLE_NAME = '03_view_zaq'
);
IF @ViewExists = 0
BEGIN
    DECLARE @CreateViewSql NVARCHAR(MAX);
    SET @CreateViewSql = N'
        CREATE VIEW [03_view_zaq] AS
        /*
        This view pulls sales data from zaq
        joins the data with products and customers
        id a product or a customer dont exist, some fields will be NULL
        like _view_customer_id, brand_id, colorgroup_id
        */
        SELECT
            z.[id] as zaq_id,
            z.[billing_date],
            YEAR(z.[billing_date])*100 + MONTH(z.[billing_date]) as year_month,
            YEAR(z.[billing_date]) as [year],
            MONTH(z.[billing_date]) as [month_number],
            z.[material],
            z.[description],
            z.[sold_to],
            z.[name],
            z.[billing_doc],
            z.[invoice_qty],
            z.[UoM],
            z.[unit_price],
            z.[invoice_sales],
            z.[curr],
            z.[batch],
            z.[gm_perc],
            z.[prof],
            z.[ptrm],
            z.[curr_1],
            z.[cost],
            z.[can],
            z.[bill],
            z.[item],
            z.[tax_amount],
            z.[curr_2],
            z.[dv],
            z.[shpt],
            z.[sales_doc],
            z.[import_date],

            c.[id] as _view_customers_id,
            c.[number] as _view_customers_number,
            c.[name] as _view_customers_name,
            c.[currency],
            c.[active],
            c.[insurance],
            c.[insurance_value],
            c.[credit_limit],
            c.[vat],
            c.[email],
            c.[approved_by_old],
            c.[approved_on] as _view_customers_approved_on,
            c.[import_note],
            c.[import_status],
            c.[sqlapp_id],
            c.[approved_by_id] as _view_customers_approved_by_id,
            c.[country_id],
            c.[customer_type_id],
            c.[industry_id],
            c.[sales_employee_id],
            c.[is_new] as _view_customers_is_new,
            c.[phone],
            c.[customer_service_rep_id],
            c.[payment_term_id],
            c.[shipping_policy_id],
            c.[country_id_from_view],
            c.[country_iso_alpha2],
            c.[country_iso_alpha3],
            c.[country_name],
            c.[sales_manager],

            p.[id] as _view_products_id,
            p.[number] as _view_products_number,
            p.[name] as _view_products_name,
            p.[made_in_id],
            p.[made_in_name],
            p.[is_ink],
            p.[brand_id],
            p.[brand_name],
            p.[major_label_name],
            p.[nsf_division_id],
            p.[nsf_division_name],
            p.[division_id],
            p.[division_name],
            p.[ink_technology_id],
            p.[ink_technology_name],
            p.[market_segment_id],
            p.[market_segment_name],
            p.[material_group_id],
            p.[material_group_name],
            p.[color_id],
            p.[color_name],
            p.[colorgroup_id],
            p.[colorgroup_name],
            p.[product_line_id],
            p.[product_status_id],
            p.[approved_by_id] as _view_products_approved_by_id,
            p.[approved_on] as _view_products_approved_on,
            p.[is_new] as _view_products_is_new

        FROM inx_platform_app_zaqcodmi9_line z
        LEFT JOIN [02_view_products] p ON p.number = z.material
        LEFT JOIN [01_view_customers] c ON c.number = z.sold_to
        ';
    EXEC sp_executesql @CreateViewSql;
END




