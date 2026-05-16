DROP TABLE IF EXISTS orderitemview;
DROP TABLE IF EXISTS orderview;
DROP TABLE IF EXISTS taxrecordview;
DROP TABLE IF EXISTS addressview;
DROP TABLE IF EXISTS productview;
DROP TABLE IF EXISTS categoryview;
DROP TABLE IF EXISTS creditcardview;
DROP TABLE IF EXISTS customerview;

CREATE TABLE addressview (
    address_id BIGINT,
    address_street VARCHAR,
    address_city VARCHAR,
    address_state VARCHAR,
    address_zip BIGINT,
    address_zipprefix BIGINT,
    address_customerid BIGINT,
    address_valuation BIGINT,
    address_zone BIGINT,
    address_rating DOUBLE PRECISION,
    address_lastsupportsession BIGINT,
    address_occupancydate BIGINT,
    address_supporttime BIGINT
);

CREATE TABLE categoryview (
    category_name BIGINT,
    category_shortname VARCHAR,
    category_perishable SMALLINT,
    category_seasonal SMALLINT,
    category_demandscore BIGINT,
    category_valuation BIGINT,
    category_warehousesqft BIGINT,
    category_warehouseclosing BIGINT,
    category_regulationprobability DOUBLE PRECISION,
    category_auditdate BIGINT,
    category_auditdeadline BIGINT
);

CREATE TABLE creditcardview (
    creditcard_number BIGINT,
    creditcard_holder VARCHAR,
    creditcard_expirationdate BIGINT,
    creditcard_customerid BIGINT,
    creditcard_zip BIGINT,
    creditcard_cvv BIGINT,
    creditcard_lastchargeamount DOUBLE PRECISION,
    creditcard_lastchargetimestamp BIGINT,
    creditcard_lastchargetime BIGINT
);

CREATE TABLE customerview (
    customer_id BIGINT,
    customer_name VARCHAR,
    customer_registrationdate BIGINT,
    customer_priority BIGINT,
    customer_age BIGINT,
    customer_onboardgroup BIGINT,
    customer_balance DOUBLE PRECISION,
    customer_lastlogin BIGINT,
    customer_alerttime BIGINT,
    customer_customerid BIGINT
);

CREATE TABLE orderitemview (
    orderitem_id BIGINT,
    orderitem_supplierstate VARCHAR,
    orderitem_productid BIGINT,
    orderitem_quantity BIGINT,
    orderitem_sku BIGINT,
    orderitem_productgroup BIGINT,
    orderitem_weight DOUBLE PRECISION,
    orderitem_alertat BIGINT,
    orderitem_discountexpiration BIGINT,
    orderitem_checkoutby BIGINT,
    orderitem_orderid BIGINT
);

CREATE TABLE orderview (
    order_id BIGINT,
    order_destination VARCHAR,
    order_placedon BIGINT,
    order_isexpeditedshipped SMALLINT,
    order_subshipments BIGINT,
    order_serverid BIGINT,
    order_slaprobability DOUBLE PRECISION,
    order_shipby BIGINT,
    order_inspectiontime BIGINT,
    order_customerid BIGINT,
    order_creditcardnumber BIGINT
);

CREATE TABLE productview (
    product_id BIGINT,
    product_name VARCHAR,
    product_price DOUBLE PRECISION,
    product_categoryname BIGINT,
    product_likes BIGINT,
    product_inventory BIGINT,
    product_backorderthreshold BIGINT,
    product_inventorylastchecked BIGINT,
    product_inventorylastorderedon BIGINT,
    product_inventoryalertat BIGINT
);

CREATE TABLE taxrecordview (
    taxrecord_id BIGINT,
    taxrecord_state VARCHAR,
    taxrecord_value DOUBLE PRECISION,
    taxrecord_rate DOUBLE PRECISION,
    taxrecord_constructiondate BIGINT,
    taxrecord_bracket BIGINT,
    taxrecord_ein BIGINT,
    taxrecord_bracketthreshold BIGINT,
    taxrecord_lastpayment BIGINT,
    taxrecord_scheduledpaymenttime BIGINT,
    taxrecord_addressid BIGINT
);
