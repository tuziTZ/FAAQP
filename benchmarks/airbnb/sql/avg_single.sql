SELECT AVG(l_minimum_nights) FROM listings WHERE l_minimum_nights >= 1 AND l_minimum_nights <= 30;
SELECT AVG(l_number_of_reviews) FROM listings WHERE l_room_type = 'Entire home/apt' AND l_number_of_reviews >= 0 AND l_number_of_reviews <= 500;
SELECT AVG(l_reviews_per_month) FROM listings WHERE l_room_type = 'Private room' AND l_reviews_per_month >= 0 AND l_reviews_per_month <= 20;
SELECT AVG(l_minimum_nights) FROM listings WHERE l_minimum_nights >= 1 AND l_minimum_nights <= 30;
SELECT AVG(l_minimum_nights) FROM listings WHERE l_room_type = 'Private room' AND l_minimum_nights >= 1 AND l_minimum_nights <= 30;
SELECT AVG(c_minimum_nights) FROM calendar, listings, reviews WHERE c_listing_id = l_id AND r_listing_id = l_id AND c_available = 't' AND c_minimum_nights >= 1 AND c_minimum_nights <= 30;
SELECT AVG(c_minimum_nights) FROM calendar, listings, reviews WHERE c_listing_id = l_id AND r_listing_id = l_id AND c_available = 'f' AND c_minimum_nights >= 1 AND c_minimum_nights <= 30;
SELECT AVG(c_maximum_nights) FROM calendar, listings, reviews WHERE c_listing_id = l_id AND r_listing_id = l_id AND c_maximum_nights >= 30 AND c_maximum_nights <= 365;
SELECT AVG(l_availability_365) FROM calendar, listings, reviews WHERE c_listing_id = l_id AND r_listing_id = l_id AND l_room_type = 'Entire home/apt' AND l_availability_365 >= 0 AND l_availability_365 <= 365;
