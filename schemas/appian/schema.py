from ensemble_compilation.graph_representation import SchemaGraph, Table


APPian_TABLE_SIZES = {
    "AddressView": 800000,
    "CategoryView": 9,
    "CreditCardView": 2039783,
    "CustomerView": 800000,
    "OrderItemView": 19280884,
    "OrderView": 4283993,
    "ProductView": 36,
    "TaxRecordView": 800000,
}


def gen_appian_schema(csv_path):
    schema = SchemaGraph()

    schema.add_table(
        Table(
            "AddressView",
            attributes=[
                "address_id",
                "address_street",
                "address_city",
                "address_state",
                "address_zip",
                "address_zipPrefix",
                "address_customerId",
                "address_valuation",
                "address_zone",
                "address_rating",
                "address_lastSupportSession",
                "address_occupancyDate",
                "address_supportTime",
            ],
            csv_file_location=csv_path.format("addressview"),
            table_size=APPian_TABLE_SIZES["AddressView"],
            primary_key=["address_id"],
        )
    )

    schema.add_table(
        Table(
            "CategoryView",
            attributes=[
                "category_name",
                "category_shortName",
                "category_perishable",
                "category_seasonal",
                "category_demandScore",
                "category_valuation",
                "category_warehouseSqft",
                "category_warehouseClosing",
                "category_regulationProbability",
                "category_auditDate",
                "category_auditDeadline",
            ],
            csv_file_location=csv_path.format("categoryview"),
            table_size=APPian_TABLE_SIZES["CategoryView"],
            primary_key=["category_name"],
        )
    )

    schema.add_table(
        Table(
            "CreditCardView",
            attributes=[
                "creditCard_number",
                "creditCard_holder",
                "creditCard_expirationDate",
                "creditCard_customerId",
                "creditCard_zip",
                "creditCard_cvv",
                "creditCard_lastChargeAmount",
                "creditCard_lastChargeTimestamp",
                "creditCard_lastChargeTime",
            ],
            csv_file_location=csv_path.format("creditcardview"),
            table_size=APPian_TABLE_SIZES["CreditCardView"],
            primary_key=["creditCard_number"],
        )
    )

    schema.add_table(
        Table(
            "CustomerView",
            attributes=[
                "customer_id",
                "customer_name",
                "customer_registrationDate",
                "customer_priority",
                "customer_age",
                "customer_onboardGroup",
                "customer_balance",
                "customer_lastLogin",
                "customer_alertTime",
                "customer_customerId",
            ],
            csv_file_location=csv_path.format("customerview"),
            table_size=APPian_TABLE_SIZES["CustomerView"],
            primary_key=["customer_id"],
        )
    )

    schema.add_table(
        Table(
            "OrderItemView",
            attributes=[
                "orderItem_id",
                "orderItem_supplierState",
                "orderItem_productId",
                "orderItem_quantity",
                "orderItem_sku",
                "orderItem_productGroup",
                "orderItem_weight",
                "orderItem_alertAt",
                "orderItem_discountExpiration",
                "orderItem_checkoutBy",
                "orderItem_orderId",
            ],
            csv_file_location=csv_path.format("orderitemview"),
            table_size=APPian_TABLE_SIZES["OrderItemView"],
            primary_key=["orderItem_id"],
        )
    )

    schema.add_table(
        Table(
            "OrderView",
            attributes=[
                "order_id",
                "order_destination",
                "order_placedOn",
                "order_isExpeditedShipped",
                "order_subShipments",
                "order_serverId",
                "order_slaProbability",
                "order_shipBy",
                "order_inspectionTime",
                "order_customerId",
                "order_creditCardNumber",
            ],
            csv_file_location=csv_path.format("orderview"),
            table_size=APPian_TABLE_SIZES["OrderView"],
            primary_key=["order_id"],
        )
    )

    schema.add_table(
        Table(
            "ProductView",
            attributes=[
                "product_id",
                "product_name",
                "product_price",
                "product_categoryName",
                "product_likes",
                "product_inventory",
                "product_backorderThreshold",
                "product_inventoryLastChecked",
                "product_inventoryLastOrderedOn",
                "product_inventoryAlertAt",
            ],
            csv_file_location=csv_path.format("productview"),
            table_size=APPian_TABLE_SIZES["ProductView"],
            primary_key=["product_id"],
        )
    )

    schema.add_table(
        Table(
            "TaxRecordView",
            attributes=[
                "taxRecord_id",
                "taxRecord_state",
                "taxRecord_value",
                "taxRecord_rate",
                "taxRecord_constructionDate",
                "taxRecord_bracket",
                "taxRecord_ein",
                "taxRecord_bracketThreshold",
                "taxRecord_lastPayment",
                "taxRecord_scheduledPaymentTime",
                "taxRecord_addressId",
            ],
            csv_file_location=csv_path.format("taxrecordview"),
            table_size=APPian_TABLE_SIZES["TaxRecordView"],
            primary_key=["taxRecord_id"],
        )
    )

    schema.add_relationship("AddressView", "address_customerId", "CustomerView", "customer_id")
    schema.add_relationship("TaxRecordView", "taxRecord_addressId", "AddressView", "address_id")
    schema.add_relationship("OrderView", "order_customerId", "CustomerView", "customer_id")
    schema.add_relationship("OrderView", "order_creditCardNumber", "CreditCardView", "creditCard_number")
    schema.add_relationship("OrderItemView", "orderItem_orderId", "OrderView", "order_id")
    schema.add_relationship("OrderItemView", "orderItem_productId", "ProductView", "product_id")
    schema.add_relationship("ProductView", "product_categoryName", "CategoryView", "category_name")

    return schema
