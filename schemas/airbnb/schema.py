from ensemble_compilation.graph_representation import SchemaGraph, Table


def gen_airbnb_schema(csv_path):
    schema = SchemaGraph()

    schema.add_table(Table('calendar',
                           attributes=['c_listing_id', 'c_date', 'c_available', 'c_price', 'c_adjusted_price',
                                       'c_minimum_nights', 'c_maximum_nights', 'c_id'],
                           csv_file_location=csv_path.format('calendar_summary_pk'),
                           table_size=8627065, primary_key=['c_id'], sample_rate=1))

    schema.add_table(
        Table('listings',
              attributes=['l_id', 'l_host_id', 'l_latitude', 'l_longitude', 'l_room_type', 'l_price',
                          'l_minimum_nights', 'l_number_of_reviews', 'l_last_review', 'l_reviews_per_month',
                          'l_calculated_host_listings_count', 'l_availability_365', 'l_number_of_reviews_ltm'],
              csv_file_location=csv_path.format('listings_summary'),
              table_size=17230, primary_key=["l_id"]))

    schema.add_table(
        Table('reviews',
              attributes=['r_listing_id', 'r_id', 'r_date', 'r_reviewer_id'],
              csv_file_location=csv_path.format('reviews_summary'),
              table_size=333706, primary_key=["r_id"]))

    # relationships
    schema.add_relationship('calendar', 'c_listing_id', 'listings', 'l_id')
    # schema.add_relationship('calendar', 'c_listing_id', 'reviews', 'r_listing_id')
    schema.add_relationship('reviews', 'r_listing_id', 'listings', 'l_id')

    return schema
