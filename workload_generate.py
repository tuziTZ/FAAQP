import psycopg2
import random
import csv

def flights():
    query_num = 10000
    conn = psycopg2.connect(database="flights_test", user="postgres", password="postgres", host="127.0.0.1",
                            port="5432")
    cur = conn.cursor()
    attributes_c = ['origin', 'dest']
    attributes_i = ['dep_delay', 'taxi_out', 'taxi_in', 'arr_delay', 'air_time', 'distance']
    # attributes_c = ['origin']
    # attributes_i = ['arr_delay']

    aggerations = ['COUNT(*)', 'AVG(dep_delay)', 'AVG(taxi_out)', 'AVG(taxi_in)', 'AVG(distance)', 'AVG(arr_delay)']
    operates_f = [' >= ', ' > ']
    operates_s = [' <= ', ' < ']
    attributes_resluts = {}
    result_queries, none_queries = set(), set()
    queries = set()
    f = open('/home/qym/zhb/RSPN++/benchmarks/flights/sql/count_result_queries.sql', 'r')
    for q in f.readlines():
        if q != '\n':
            # temp_att = []
            # for att in attributes_i:
            #     if att not in q:
            #         temp_att.append(att)
            # aggre = random.choice(temp_att)
            # q = q.replace('COUNT(*)', 'AVG(' + aggre + ')')
            q = q.replace('\n','')
            # print(q.replace('\n',''))
            queries.add(q)

    # f = open('/home/qym/zhb/RSPN++/benchmarks/flights/sql/temp_none.sql', 'r')
    # for q in f.readlines():
    #     if q != '\n':
    #         none_queries.add(q)

    for att_c in attributes_c:
        query = 'select ' + att_c + ', count(*) from flights group by ' + att_c + ';'
        cur.execute(query)
        result = cur.fetchall()
        attributes_resluts[att_c] = result
    for att_i in attributes_i:
        query = 'select ' + att_i + ', count(*) from flights group by ' + att_i + ';'
        cur.execute(query)
        result = cur.fetchall()
        attributes_resluts[att_i] = result

    while True:
        c_pre_n = random.randint(0, 2)
        i_pre_n = random.randint(1, 2)
        c_pre = random.sample(attributes_c, c_pre_n)
        i_pre = random.sample(attributes_i, i_pre_n)
        # c_pre = attributes_c
        # i_pre = attributes_i
        query = 'SELECT COUNT(*) FROM flights WHERE '
        for pre in c_pre:
            condition = str(random.choice(attributes_resluts[pre])[0])
            if pre == 'year_date':
                query += pre + ' = ' + condition
            else:
                query += pre + ' = ' + "'" + condition + "'"
            if c_pre_n + i_pre_n > 1:
                query += ' and '
        for pre in i_pre:
            condition = random.sample(attributes_resluts[pre], 2)
            condition_f, condition_s = condition[0][0], condition[1][0]
            if condition_f > condition_s:
                temp = condition_f
                condition_f = condition_s
                condition_s = temp
            query += pre + random.choice(operates_f) + str(condition_f) + ' and ' + pre + random.choice(
                operates_s) + str(condition_s)
            if i_pre_n > 1:
                query += ' and '
        if query[-5:] == ' and ':
            query = query[:-5]
        query += ';'
        cur.execute(query)
        result = cur.fetchall()[0][0]
        if result and query not in queries:
            query += str(result) + '\n'
            if query not in result_queries:
                result_queries.add(query)
        # else:
        #     none_queries.add(query)
        if len(result_queries) >= query_num:
            break
        print(len(result_queries))
    conn.commit()
    conn.close()

    f = open('/home/qym/zhb/flights-benchmark/train_queries.sql', 'w')
    f.writelines(list(result_queries)[:query_num])
    f.close()


def flights_predicates():
    query_num = 1000
    conn = psycopg2.connect(database="flights_test", user="postgres", password="postgres", host="127.0.0.1",
                            port="5432")
    cur = conn.cursor()
    sql = 'SELECT distance, arr_delay, origin, dest, dep_delay, COUNT(*) FROM flights GROUP BY origin, dest, dep_delay, arr_delay, distance;'
    origin_l, dest_l, dep_delay_l, arr_delay_l, distance_l = set(), set(), set(), set(), set()
    pre_l5, pre_l4, pre_l3, pre_l2, pre_l1 = [], [], [], [], []
    cur.execute(sql)
    result = cur.fetchall()
    for item in result:
        pre = item[0:5]
        res = item[5]
        # if res < 30:
        #     continue
        if pre[0] in distance_l or pre[1] in arr_delay_l or pre[2] in origin_l or pre[3] in dest_l or pre[4] in dep_delay_l:
            continue
        else:
            print(query_num, res)
            query_num  -= 1
            distance_l.add(pre[0])
            arr_delay_l.add(pre[1])
            origin_l.add(pre[2])
            dest_l.add(pre[3])
            dep_delay_l.add(pre[4])
            if pre[0] < 1000:
                pre5 = "SELECT COUNT(*) FROM flights WHERE distance >= " + str(pre[0]) + " and " + "arr_delay = " + str(
                    pre[1]) + " and " + "origin = '" + str(pre[2]) + "' and " + "dest = '" + str(
                    pre[3]) + "' and " + "dep_delay = " + str(pre[4]) + ";\n"
                pre4 = "SELECT COUNT(*) FROM flights WHERE distance >= " + str(pre[0]) + " and " + "arr_delay = " + str(
                    pre[1]) + " and " + "origin = '" + str(pre[2]) + "' and " + "dest = '" + str(pre[3]) + "';\n"
                pre3 = "SELECT COUNT(*) FROM flights WHERE distance >= " + str(pre[0]) + " and " + "arr_delay = " + str(
                    pre[1]) + " and " + "origin = '" + str(pre[2]) + "';\n"
                pre2 = "SELECT COUNT(*) FROM flights WHERE distance >= " + str(pre[0]) + " and " + "arr_delay = " + str(
                    pre[1]) + ";\n"
                pre1 = "SELECT COUNT(*) FROM flights WHERE distance >= " + str(pre[0]) + ";\n"
            else:
                pre5 = "SELECT COUNT(*) FROM flights WHERE distance <= " + str(pre[0]) + " and " + "arr_delay = " + str(
                    pre[1]) + " and " + "origin = '" + str(pre[2]) + "' and " + "dest = '" + str(
                    pre[3]) + "' and " + "dep_delay = " + str(pre[4]) + ";\n"
                pre4 = "SELECT COUNT(*) FROM flights WHERE distance <= " + str(pre[0]) + " and " + "arr_delay = " + str(
                    pre[1]) + " and " + "origin = '" + str(pre[2]) + "' and " + "dest = '" + str(pre[3]) + "';\n"
                pre3 = "SELECT COUNT(*) FROM flights WHERE distance <= " + str(pre[0]) + " and " + "arr_delay = " + str(
                    pre[1]) + " and " + "origin = '" + str(pre[2]) + "';\n"
                pre2 = "SELECT COUNT(*) FROM flights WHERE distance <= " + str(pre[0]) + " and " + "arr_delay = " + str(
                    pre[1]) + ";\n"
                pre1 = "SELECT COUNT(*) FROM flights WHERE distance <= " + str(pre[0]) + ";\n"
            pre_l5.append(pre5)
            pre_l4.append(pre4)
            pre_l3.append(pre3)
            pre_l2.append(pre2)
            pre_l1.append(pre1)
        if query_num <= 0:
            break
    conn.commit()
    conn.close()

    f = open('/home/qym/zhb/RSPN++/benchmarks/flights/sql/pre5.sql', 'w')
    f.writelines(pre_l5)
    f.close()
    f = open('/home/qym/zhb/RSPN++/benchmarks/flights/sql/pre4.sql', 'w')
    f.writelines(pre_l4)
    f.close()
    f = open('/home/qym/zhb/RSPN++/benchmarks/flights/sql/pre3.sql', 'w')
    f.writelines(pre_l3)
    f.close()
    f = open('/home/qym/zhb/RSPN++/benchmarks/flights/sql/pre2.sql', 'w')
    f.writelines(pre_l2)
    f.close()
    f = open('/home/qym/zhb/RSPN++/benchmarks/flights/sql/pre1.sql', 'w')
    f.writelines(pre_l1)
    f.close()


def dom1000(table_name_list):
    conn = psycopg2.connect(database="sdata", user="postgres", password="postgres", host="127.0.0.1", port="5432")
    cur = conn.cursor()
    attributes=['col0', 'col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8', 'col9']
    for table in table_name_list:
        query_num = 1000
        query_list = []
        while query_num:
            query = 'select count(*) from ' + table + ' WHERE '
            for col in attributes:
                if random.random() < 0.5:
                    l = random.randint(0, 999)
                    r = random.randint(0, 999)
                    if l > r:
                        temp = l
                        l = r
                        r = temp
                    query += col + ' >= ' + str(l) + ' and ' + col + ' <= ' + str(r) + ' and '
            if query[-5:] == ' and ':
                query = query[:-5]
                cur.execute(query)
                result = cur.fetchall()[0][0]
                query += ';\n'
                if query not in query_list and result:
                    query_list.append(query)
                    query_num -= 1
                    print(table, query_num)

        f = open('/home/qym/zhb/sdata/sql/' + table + '.sql', 'w')
        f.writelines(query_list)
        f.close()
    # while query_num > 90:
    #     condition_1 = 'col0 >= ' + str(random.randint(0, 999))
    #     condition_2 = 'col1 = ' + str(random.randint(0, 999))
    #     tf = True
    #     for table_name in table_name_list:
    #         query = 'select count(*) from ' + table_name + ' WHERE ' + condition_1 + ' and ' + condition_2 + ';'
    #         # print(query)
    #         cur.execute(query)
    #         query += '\n'
    #         result = cur.fetchall()[0][0]
    #         if not result or query in query_list or result > 1000:
    #             # print(result)
    #             tf = False
    #             break
    #     if tf:
    #         query_list.append(query)
    #         query_num -= 1
    #         print(query_num, result)
    # while query_num:
    #     value = str(random.randint(0, 999))
    #     condition_1 = 'col0 = ' + value
    #     condition_2 = 'col1 = ' + value
    #     tf = True
    #     for table_name in table_name_list:
    #         query = 'select count(*) from ' + table_name + ' WHERE ' + condition_1 + ' and ' + condition_2 + ';'
    #         cur.execute(query)
    #         result = cur.fetchall()[0][0]
    #         query += '\n'
    #         if not result or query in query_list:
    #             tf = False
    #             break
    #     if tf:
    #         query_list.append(query)
    #         query_num -= 1
    #         print(query_num)
    # conn.commit()
    # conn.close()

    # for i in range(len(table_name_list)):
    #     temp_query_list = []
    #     for query in query_list:
    #         temp_query_list.append(query.replace('c00s10', table_name_list[i]))
    #     f = open('/home/qym/zhb/sdata/sql/' + table_name_list[i] + '.sql', 'w')
    #     f.writelines(temp_query_list)
    #     f.close()


def dom1000_sel(table_name_list, sel1 = 100, sel2 = 200):
    conn = psycopg2.connect(database="dom1000", user="postgres", password="postgres", host="127.0.0.1", port="5432")
    cur = conn.cursor()
    eq_list = [' >= ', ' <= ', ' = ', ' = ']
    for table_name in table_name_list:
        print(table_name)
        query_list = []
        query_num = 1000
        while query_num > 50:
            value = str(random.randint(0, 999))
            condition_1 = 'col0' + random.choice(eq_list) + str(random.randint(0, 999))
            condition_2 = 'col1' + random.choice(eq_list) + str(random.randint(0, 999))

            query = 'select count(*) from ' + table_name + ' WHERE ' + condition_1 + ' and ' + condition_2 + ';'
            cur.execute(query)
            query += '\n'
            result = cur.fetchall()[0][0]
            if result and query not in query_list:
                query_list.append(query)
                query_num -= 1
                print(query_num)
        while query_num:
            condition_1 = 'col0 = ' + str(random.randint(0, 50))
            condition_2 = 'col1 = ' + str(random.randint(0, 50))

            query = 'select count(*) from ' + table_name + ' WHERE ' + condition_1 + ' and ' + condition_2 + ';'
            cur.execute(query)
            query += '\n'
            result = cur.fetchall()[0][0]
            if result and query not in query_list:
                query_list.append(query)
                query_num -= 1
                print(query_num)
            # value = str(i)
            # i += 1
            # condition_1 = 'col0 >= ' + value
            # condition_2 = 'col1 >= ' + value
            # query = 'select count(*) from ' + table_name + ' WHERE ' + condition_1 + ' and ' + condition_2 + ';'
            # cur.execute(query)
            # query += '\n'
            # result = cur.fetchall()[0][0]
            # print(query, result)
            # if not result or query in query_list or result < sel1 or result > sel2:
            #     continue
            # else:
            #     query_list.append(query)
            #     query_num -= 1
            #     print(query_num)
        f = open('/home/qym/zhb/dom1000/sql/' + table_name + '.sql', 'w')
        f.writelines(query_list)
        f.close()
    conn.commit()
    conn.close()


def airbnb():
    conn = psycopg2.connect(database="airbnb", user="postgres", password="postgres", host="127.0.0.1", port="5432")
    cur = conn.cursor()
    attributes_c = ['c_available', 'l_room_type']
    attributes_i = ['c_price', 'c_adjusted_price', 'c_minimum_nights', 'c_maximum_nights', 'l_reviews_per_month',
             'l_calculated_host_listings_count', 'l_availability_365', 'l_number_of_reviews_ltm', 'l_number_of_reviews']
    operates_f = [' >= ', ' = ']
    operates_s = [' <= ', ' = ']
    attributes_resluts = {}

    query = 'select c_available, count(*) from calendar group by c_available;'
    cur.execute(query)
    result = cur.fetchall()
    attributes_resluts['c_available'] = result

    query = 'select l_room_type, count(*) from listings group by l_room_type;'
    cur.execute(query)
    result = cur.fetchall()
    attributes_resluts['l_room_type'] = result

    for att_i in attributes_i:
        if 'c_' in att_i:
            query = 'select ' + att_i + ', count(*) from calendar group by ' + att_i + ';'
        else:
            query = 'select ' + att_i + ', count(*) from listings group by ' + att_i + ';'
        cur.execute(query)
        result = cur.fetchall()
        attributes_resluts[att_i] = result
    query_num = 1000
    result_queries = []
    while query_num:
        sql = 'SELECT COUNT(*) FROM calendar, listings, reviews WHERE c_listing_id = l_id and r_listing_id = l_id'

        # c_pre = random.choice(attributes_c)
        c_pre = attributes_c
        for pre in c_pre:
            condition = str(random.choice(attributes_resluts[pre])[0])
            sql += ' and ' +pre + ' = ' + "'" + condition + "'"
        # condition = str(random.choice(attributes_resluts[c_pre])[0])
        # sql += ' and ' + c_pre + ' = ' + "'" + condition + "'"

        # if random.randint(0, 10) < 5:
        #     i_pre = random.sample(attributes_i, 2)
        # else:
        i_pre = random.sample(attributes_i, 1)
        for pre in i_pre:
            condition = random.sample(attributes_resluts[pre], 2)
            condition_f, condition_s = condition[0][0], condition[1][0]
            if condition_f > condition_s:
                temp = condition_f
                condition_f = condition_s
                condition_s = temp
            if random.choice(operates_f) == ' = ':
                sql += ' and ' + pre + ' = ' + str(condition_f)
            else:
                sql += ' and ' + pre + ' >= ' + str(condition_f) + ' and ' + pre + ' <= ' + str(condition_s)

        cur.execute(sql)
        sql += '\n'
        result = cur.fetchall()[0][0]
        if result and sql not in result_queries:
            result_queries.append(sql)
            query_num -= 1
            print(len(result_queries), sql, result)

    conn.commit()
    conn.close()
    f = open('/home/qym/zhb/airbnb/sql/join_DBEst.sql', 'w')
    f.writelines(result_queries)
    f.close()


def flights_different_size():
    file_1 = '/home/qym/zhb/flights-benchmark/shuf_different_size/shuf_transport.csv'
    file_2 = '/home/qym/zhb/flights-benchmark/shuf_different_size/flights_origin.csv'
    file_3 = '/home/qym/zhb/flights-benchmark/shuf_different_size/flights_size_20m.csv'
    num = 20000000
    with open(file_2, 'r') as f:
        r_1 = csv.reader(f, delimiter=',')
        i = 0
        data_list = []
        for row in r_1:
            if i == 0:
                i += 1
                continue
            data_list.append(row)
            i += 1
            if i % 1000000 == 0:
                print(i)
    with open(file_1, 'r') as f:
        r_1 = csv.reader(f, delimiter=',')
        i = 0
        for row in r_1:
            if i == 0:
                i += 1
                continue
            data_list.append(row)
            i += 1
            if i % 1000000 == 0:
                print(i)
            if len(data_list) >= num:
                break
    with open(file_3, 'w') as f:
        r_3 = csv.writer(f, delimiter=',')
        r_3.writerows(data_list)

# table_name_list = ['s10c00', 's10c01', 's10c02', 's10c03', 's10c04', 's10c05', 's10c06', 's10c07', 's10c08', 's10c09'
#                     , 's10c10', 'c10s00', 'c10s02', 'c10s04', 'c10s05', 'c10s06', 'c10s08', 'c10s10', 'c10s12', 'c10s14'
#                     , 'c10s15', 'c10s16', 'c10s18', 'c10s20']
# table_name_list = ['s10c00', 's10c02', 's10c04', 's10c06', 's10c08', 's10c10', 'c10s15', 'c10s20', 'c10s00', 'c10s05']
# table_name_list = ['c04s15']
# table_name_list = ['c00s10', 'c02s10', 'c04s10', 'c06s10', 'c08s10', 'c10s10', 'c04s00', 'c04s05', 'c04s15', 'c04s20']
# table_name_list = ['c04s05', 'c04s15', 'c04s20']
# dom1000(table_name_list)
# flights_predicates()
airbnb()
# flights_different_size()