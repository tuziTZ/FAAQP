ALTER TABLE addressview ADD PRIMARY KEY (address_id);
ALTER TABLE categoryview ADD PRIMARY KEY (category_name);
ALTER TABLE creditcardview ADD PRIMARY KEY (creditcard_number);
ALTER TABLE customerview ADD PRIMARY KEY (customer_id);
ALTER TABLE orderitemview ADD PRIMARY KEY (orderitem_id);
ALTER TABLE orderview ADD PRIMARY KEY (order_id);
ALTER TABLE productview ADD PRIMARY KEY (product_id);
ALTER TABLE taxrecordview ADD PRIMARY KEY (taxrecord_id);

CREATE INDEX idx_addressview_customerid ON addressview (address_customerid);
CREATE INDEX idx_taxrecordview_addressid ON taxrecordview (taxrecord_addressid);
CREATE INDEX idx_orderview_customerid ON orderview (order_customerid);
CREATE INDEX idx_orderview_creditcardnumber ON orderview (order_creditcardnumber);
CREATE INDEX idx_orderitemview_orderid ON orderitemview (orderitem_orderid);
CREATE INDEX idx_orderitemview_productid ON orderitemview (orderitem_productid);
CREATE INDEX idx_productview_categoryname ON productview (product_categoryname);

ANALYZE;
