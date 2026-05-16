SELECT a.name AS actor_name, t.title AS movie_title, c.kind AS company_type, k.keyword AS movie_keyword, COUNT(mc.movie_id) AS movie_count
FROM aka_name a, cast_info ci, title t, movie_companies mc, company_type c, movie_keyword mk, keyword k
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mc.movie_id AND mc.company_type_id = c.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND a.name IS NOT NULL AND t.production_year >= 2000 AND c.kind LIKE 'Production%'
GROUP BY a.name, t.title, c.kind, k.keyword
ORDER BY movie_count DESC, actor_name ASC;

SELECT a.name AS actor_name, t.title AS movie_title, c.note AS role_note, t.production_year
FROM aka_name a, cast_info c, aka_title t
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND t.production_year >= 2000 AND t.production_year <= 2023
ORDER BY t.production_year DESC;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year, c.kind AS company_kind, k.keyword AS movie_keyword, pi.info AS person_info
FROM aka_name a, cast_info ci, title t, movie_companies mc, company_name cn, company_type c, movie_keyword mk, keyword k, person_info pi
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mc.movie_id AND mc.company_id = cn.id AND mc.company_type_id = c.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND a.person_id = pi.person_id AND t.production_year >= 2000 AND cn.country_code = 'USA' AND k.keyword LIKE '%action%'
GROUP BY a.name, t.title, t.production_year, c.kind, k.keyword, pi.info
ORDER BY t.production_year DESC, a.name;

SELECT a.name AS actor_name, t.title AS movie_title, c.kind AS company_type, k.keyword AS movie_keyword, p.info AS actor_info
FROM aka_name a, cast_info ci, title t, movie_companies mc, company_type c, movie_keyword mk, keyword k, person_info p
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mc.movie_id AND mc.company_type_id = c.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND a.person_id = p.person_id AND t.production_year >= 2000 AND a.name_pcode_cf IS NOT NULL AND k.keyword LIKE 'Action%'
ORDER BY t.production_year DESC, actor_name ASC;

SELECT t.title AS movie_title, a.name AS actor_name, c.kind AS company_type, k.keyword AS movie_keyword, COUNT(*) AS co_actor_count
FROM aka_title t, complete_cast cc, cast_info ci, aka_name a, movie_companies mc, company_type c, movie_keyword mk, keyword k
WHERE t.id = cc.movie_id AND cc.subject_id = ci.id AND ci.person_id = a.person_id AND t.id = mc.movie_id AND mc.company_type_id = c.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.production_year >= 2000 AND t.production_year <= 2020 AND a.name IS NOT NULL
GROUP BY t.title, a.name, c.kind, k.keyword
ORDER BY movie_title, actor_name;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year, c.note AS cast_note
FROM aka_name a, cast_info c, aka_title t
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND t.production_year >= 2000
ORDER BY t.production_year DESC, a.name;

SELECT a.name AS actor_name, t.title AS movie_title, ct.kind AS company_type, k.keyword AS movie_keyword, pi.info AS actor_info
FROM aka_name a, cast_info ci, title t, movie_companies mc, company_type ct, movie_keyword mk, keyword k, person_info pi
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mc.movie_id AND mc.company_type_id = ct.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND a.person_id = pi.person_id AND t.production_year > 2000 AND ct.kind = 'Distributor' AND k.keyword LIKE '%action%'
GROUP BY a.name, t.title, ct.kind, k.keyword, pi.info
ORDER BY a.name, t.title;

SELECT a.name AS aka_name, t.title AS movie_title, c.nr_order AS cast_order, p.info AS person_info, kom.name AS company_name, k.keyword AS movie_keyword, r.role AS person_role
FROM aka_name a, cast_info c, title t, role_type r, complete_cast cc, movie_companies mc, company_name kom, movie_keyword mk, keyword k, person_info p
WHERE a.person_id = c.person_id AND c.movie_id = t.id AND c.role_id = r.id AND cc.movie_id = t.id AND mc.movie_id = t.id AND mc.company_id = kom.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND a.person_id = p.person_id AND t.production_year > 2000 AND kom.country_code = 'USA'
ORDER BY t.production_year DESC, a.name ASC, c.nr_order ASC;

SELECT a.name AS actor_name, t.title AS movie_title, c.kind AS cast_type, ci.note AS casting_note, COUNT(mk.keyword_id) AS keyword_count
FROM aka_name a, cast_info ci, title t, movie_companies mc, company_name cn, movie_keyword mk, keyword k, comp_cast_type c
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND mc.movie_id = t.id AND mc.company_id = cn.id AND mk.movie_id = t.id AND mk.keyword_id = k.id AND ci.person_role_id = c.id AND t.production_year >= 2000 AND t.production_year <= 2023 AND cn.country_code = 'USA'
GROUP BY a.name, t.title, c.kind, ci.note
ORDER BY keyword_count DESC, a.name;

SELECT a.name AS actor_name, t.title AS movie_title, c.note AS role_note, t.production_year
FROM aka_name a, cast_info c, aka_title t
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND t.production_year IS NOT NULL
ORDER BY t.production_year DESC;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year, k.keyword AS movie_keyword, ct.kind AS company_type, r.role AS role_type
FROM aka_name a, cast_info ci, title t, movie_keyword mk, keyword k, movie_companies mc, company_type ct, company_name cn, complete_cast cc, role_type r
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.id = mc.movie_id AND mc.company_type_id = ct.id AND mc.company_id = cn.id AND t.id = cc.movie_id AND ci.role_id = r.id AND t.production_year >= 2000 AND t.production_year <= 2023 AND ci.nr_order = 1 AND a.name IS NOT NULL
GROUP BY a.name, t.title, t.production_year, k.keyword, ct.kind, r.role
ORDER BY t.production_year DESC, a.name ASC;

SELECT a.name AS actor_name, t.title AS movie_title, c.note AS role_note, co.name AS company_name, k.keyword AS movie_keyword, i.info AS movie_info
FROM aka_name a, cast_info c, title t, movie_companies mc, company_name co, movie_keyword mk, keyword k, movie_info mi, info_type i
WHERE a.person_id = c.person_id AND c.movie_id = t.id AND t.id = mc.movie_id AND mc.company_id = co.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.id = mi.movie_id AND mi.info_type_id = i.id AND t.production_year > 2000 AND co.country_code = 'USA' AND k.keyword LIKE '%action%'
ORDER BY t.production_year DESC, a.name;

SELECT p.name AS person_name, t.title AS movie_title, c.kind AS company_type, k.keyword AS movie_keyword, COUNT(mc.id) AS company_count
FROM cast_info ci, aka_name p, complete_cast cc, movie_companies mc, company_type c, movie_keyword mk, keyword k, aka_title t
WHERE ci.person_id = p.person_id AND ci.movie_id = cc.movie_id AND cc.movie_id = mc.movie_id AND mc.company_type_id = c.id AND mc.movie_id = mk.movie_id AND mk.keyword_id = k.id AND ci.movie_id = t.movie_id AND t.production_year >= 1990 AND t.production_year <= 2020 AND c.kind LIKE 'Production%'
GROUP BY p.name, t.title, c.kind, k.keyword
ORDER BY company_count DESC, t.title ASC;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year, c.role_id, c.nr_order
FROM aka_name a, cast_info c, aka_title t
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND t.production_year >= 2000 AND t.production_year <= 2020
ORDER BY t.production_year DESC, a.name;

SELECT t.title AS movie_title, a.name AS actor_name, ct.kind AS company_type, k.keyword AS keyword, pi.info AS person_info
FROM title t, complete_cast cc, cast_info ci, aka_name a, movie_companies mc, company_name cn, company_type ct, movie_keyword mk, keyword k, person_info pi
WHERE t.id = cc.movie_id AND cc.subject_id = ci.person_id AND ci.person_id = a.person_id AND t.id = mc.movie_id AND mc.company_id = cn.id AND mc.company_type_id = ct.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND a.person_id = pi.person_id AND t.production_year >= 2000 AND t.production_year <= 2020 AND k.keyword LIKE '%action%'
GROUP BY t.title, a.name, ct.kind, k.keyword, pi.info
ORDER BY t.title, a.name;

SELECT t.title AS Movie_Title, a.name AS Actor_Name, r.role AS Role, c.note AS Cast_Note, co.name AS Company_Name, k.keyword AS Keyword, ti.info AS Movie_Info
FROM title t, cast_info c, aka_name a, role_type r, movie_companies mc, company_name co, movie_keyword mk, keyword k, movie_info mi, info_type ti
WHERE t.id = c.movie_id AND c.person_id = a.person_id AND c.role_id = r.id AND t.id = mc.movie_id AND mc.company_id = co.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.id = mi.movie_id AND mi.info_type_id = ti.id AND t.production_year >= 1990 AND t.production_year <= 2020 AND co.country_code = 'USA' AND k.keyword LIKE '%Action%'
ORDER BY t.production_year DESC, a.name ASC;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year, r.role AS role_name, c.kind AS company_type, n.gender AS actor_gender, COUNT(k.keyword) AS keyword_count
FROM aka_name a, cast_info ci, title t, role_type r, movie_companies mc, company_name cn, company_type c, movie_keyword mk, keyword k, name n
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND ci.role_id = r.id AND t.id = mc.movie_id AND mc.company_id = cn.id AND mc.company_type_id = c.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND a.person_id = n.imdb_id AND t.production_year >= 2000 AND c.kind LIKE '%Production%'
GROUP BY a.name, t.title, t.production_year, r.role, c.kind, n.gender
ORDER BY keyword_count DESC, t.production_year DESC;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year, c.role_id, c.nr_order
FROM cast_info c, aka_name a, aka_title t
WHERE c.person_id = a.person_id AND c.movie_id = t.movie_id AND t.production_year >= 2000
ORDER BY t.production_year DESC, a.name;

SELECT a.name AS actor_name, t.title AS movie_title, ct.kind AS company_type, t.production_year, k.keyword AS movie_keyword, pi.info AS person_info
FROM aka_name a, cast_info ci, title t, movie_companies mc, company_type ct, company_name cn, movie_keyword mk, keyword k, person_info pi
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mc.movie_id AND mc.company_type_id = ct.id AND mc.company_id = cn.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND a.person_id = pi.person_id AND a.name IS NOT NULL AND t.production_year > 2000 AND ct.kind = 'Distributor'
GROUP BY a.name, t.title, ct.kind, t.production_year, k.keyword, pi.info
ORDER BY t.production_year DESC, a.name;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year, c.kind AS company_type, k.keyword AS movie_keyword
FROM aka_name a, cast_info ci, aka_title t, movie_companies mc, company_type c, movie_keyword mk, keyword k
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mc.movie_id AND mc.company_type_id = c.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.production_year >= 2000 AND c.kind LIKE 'Production%'
ORDER BY t.production_year DESC, a.name ASC;

SELECT a.name AS actor_name, t.title AS movie_title, ct.kind AS company_type, m.production_year, k.keyword AS movie_keyword, COUNT(c.id) AS cast_count
FROM aka_name a, cast_info c, aka_title t, movie_companies mc, company_type ct, movie_keyword mk, keyword k, title m
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND t.id = mc.movie_id AND mc.company_type_id = ct.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.movie_id = m.id AND m.production_year >= 2000 AND m.production_year <= 2023 AND ct.kind = 'Production' AND k.keyword LIKE '%action%'
GROUP BY a.name, t.title, m.production_year, ct.kind, k.keyword
ORDER BY cast_count DESC, m.production_year DESC;

SELECT a.name AS actor_name, t.title AS movie_title, c.note AS role_description, t.production_year
FROM aka_name a, cast_info c, aka_title t
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND t.production_year >= 2000
ORDER BY t.production_year DESC, a.name;

SELECT a.name AS actor_name, t.title AS movie_title, ct.kind AS company_type, k.keyword AS movie_keyword, pm.info AS personal_info
FROM aka_name a, cast_info ci, aka_title t, movie_companies mc, company_type ct, movie_keyword mk, keyword k, complete_cast cc, person_info pm
WHERE a.person_id = ci.person_id AND ci.movie_id = t.movie_id AND t.id = mc.movie_id AND mc.company_type_id = ct.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.id = cc.movie_id AND cc.subject_id = pm.person_id AND t.production_year > 2000 AND a.name IS NOT NULL AND k.keyword IS NOT NULL
GROUP BY a.name, t.title, ct.kind, k.keyword, pm.info, t.production_year
ORDER BY t.production_year DESC, a.name;

SELECT t.title AS movie_title, a.name AS actor_name, r.role AS actor_role, mw.keyword AS movie_keyword, c.name AS company_name, ti.info AS movie_info
FROM title t, complete_cast cc, cast_info ci, aka_name a, role_type r, movie_keyword mk, keyword mw, movie_companies mc, company_name c, movie_info mi, info_type ti
WHERE t.id = cc.movie_id AND cc.subject_id = ci.person_id AND ci.person_id = a.person_id AND ci.role_id = r.id AND t.id = mk.movie_id AND mk.keyword_id = mw.id AND t.id = mc.movie_id AND mc.company_id = c.id AND t.id = mi.movie_id AND mi.info_type_id = ti.id AND t.production_year >= 2000 AND r.role LIKE 'actor%'
ORDER BY t.production_year DESC, a.name ASC;

SELECT a.name AS actor_name, t.title AS movie_title, kt.kind AS cast_type, ci.note AS cast_note, co.name AS company_name, ci.nr_order AS actor_order, t.production_year, COUNT(k.keyword) AS keyword_count
FROM aka_name a, cast_info ci, aka_title t, movie_companies mc, company_name co, movie_keyword mk, keyword k, kind_type kt
WHERE a.person_id = ci.person_id AND ci.movie_id = t.movie_id AND t.id = mc.movie_id AND mc.company_id = co.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.kind_id = kt.id AND t.production_year >= 2000 AND kt.kind = 'feature'
GROUP BY a.name, t.title, kt.kind, ci.note, co.name, ci.nr_order, t.production_year
ORDER BY t.production_year DESC, actor_name;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year, c.note AS role_note
FROM aka_name a, cast_info c, aka_title t
WHERE a.person_id = c.person_id AND c.movie_id = t.id AND a.name IS NOT NULL
ORDER BY t.production_year DESC;

SELECT a.name AS actor_name, t.title AS movie_title, ct.kind AS company_type, k.keyword AS movie_keyword, r.role AS role_type, pi.info AS actor_info
FROM aka_name a, cast_info ci, title t, movie_companies mc, company_name cn, company_type ct, movie_keyword mk, keyword k, role_type r, person_info pi
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mc.movie_id AND mc.company_id = cn.id AND mc.company_type_id = ct.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND ci.role_id = r.id AND a.person_id = pi.person_id AND t.production_year >= 2000 AND a.name IS NOT NULL AND cn.country_code = 'USA'
GROUP BY a.name, t.title, ct.kind, k.keyword, r.role, pi.info, t.production_year
ORDER BY t.production_year DESC, a.name, movie_title;

SELECT ak.name AS aka_name, t.title AS movie_title, c.name AS company_name, r.role AS actor_role, p.info AS actor_info, k.keyword AS movie_keyword
FROM aka_name ak, cast_info ci, title t, movie_companies mc, company_name c, role_type r, person_info p, movie_keyword mk, keyword k
WHERE ak.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mc.movie_id AND mc.company_id = c.id AND ci.role_id = r.id AND ak.person_id = p.person_id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.production_year > 2000 AND ak.name IS NOT NULL AND c.country_code = 'USA'
ORDER BY t.production_year DESC, ak.name ASC;

SELECT a.name AS actor_name, t.title AS movie_title, c.kind AS company_type, r.role AS role, mi.info AS movie_info, k.keyword AS movie_keyword, COUNT(*) AS total_roles
FROM aka_name a, cast_info ci, title t, movie_companies mc, company_type c, complete_cast cc, person_info pi, role_type r, movie_info mi, movie_keyword mk, keyword k
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mc.movie_id AND mc.company_type_id = c.id AND t.id = cc.movie_id AND a.person_id = pi.person_id AND ci.role_id = r.id AND t.id = mi.movie_id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND a.name LIKE 'A%' AND t.production_year > 2000 AND c.kind = 'Production'
GROUP BY a.name, t.title, c.kind, r.role, mi.info, k.keyword
ORDER BY total_roles DESC, a.name ASC;

SELECT a.name AS actor_name, t.title AS movie_title, c.note AS role_note, t.production_year, c.nr_order
FROM aka_name a, cast_info c, aka_title t
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND a.name IS NOT NULL
ORDER BY t.production_year DESC, c.nr_order;

SELECT a.name AS actor_name, t.title AS movie_title, c.kind AS cast_type, t.production_year, k.keyword AS movie_keyword, p.info AS person_info
FROM aka_name a, cast_info ci, title t, comp_cast_type c, movie_keyword mk, keyword k, person_info p
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND ci.person_role_id = c.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND a.person_id = p.person_id AND t.production_year >= 2000 AND t.production_year <= 2023 AND k.keyword LIKE '%action%'
GROUP BY a.name, t.title, c.kind, t.production_year, k.keyword, p.info
ORDER BY t.production_year DESC, a.name ASC;

SELECT a.name AS alias_name, t.title AS movie_title, c.nr_order AS cast_order, co.name AS company_name, kt.keyword AS movie_keyword, p.info AS person_information
FROM aka_name a, cast_info c, title t, movie_companies mc, company_name co, movie_keyword mk, keyword kt, person_info p
WHERE a.person_id = c.person_id AND c.movie_id = t.id AND t.id = mc.movie_id AND mc.company_id = co.id AND t.id = mk.movie_id AND mk.keyword_id = kt.id AND a.person_id = p.person_id AND t.production_year > 2000 AND co.country_code = 'USA'
ORDER BY t.production_year DESC, a.name, c.nr_order;

SELECT a.name AS actor_name, t.title AS movie_title, c.kind AS cast_type, cc.name AS company_name, COUNT(k.keyword) AS keyword_count
FROM aka_name a, cast_info ci, title t, movie_companies mc, company_name cc, movie_keyword mk, keyword k, comp_cast_type c
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mc.movie_id AND mc.company_id = cc.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND ci.person_role_id = c.id AND t.production_year > 2000 AND cc.country_code = 'USA'
GROUP BY a.name, t.title, c.kind, cc.name
ORDER BY keyword_count DESC, a.name;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year, c.role_id, c.nr_order
FROM cast_info c, aka_name a, aka_title t
WHERE c.person_id = a.person_id AND c.movie_id = t.movie_id AND t.production_year >= 2000
ORDER BY t.production_year DESC, a.name ASC;

SELECT t.title AS movie_title, a.name AS actor_name, ct.kind AS company_type, pi.info AS person_info, ki.keyword AS movie_keyword
FROM title t, complete_cast cc, cast_info ci, aka_name a, movie_companies mc, company_type ct, company_name cn, person_info pi, movie_keyword mk, keyword ki
WHERE t.id = cc.movie_id AND cc.subject_id = ci.id AND ci.person_id = a.person_id AND t.id = mc.movie_id AND mc.company_type_id = ct.id AND mc.company_id = cn.id AND a.person_id = pi.person_id AND t.id = mk.movie_id AND mk.keyword_id = ki.id AND t.production_year >= 2000 AND t.production_year <= 2023 AND ct.kind LIKE '%Production%'
GROUP BY t.title, a.name, ct.kind, pi.info, ki.keyword
ORDER BY t.title, a.name;

SELECT a.name AS actor_name, t.title AS movie_title, c.kind AS cast_kind, p.info AS actor_info, k.keyword AS movie_keyword
FROM aka_name a, cast_info ci, title t, movie_companies mc, company_name cn, complete_cast cc, person_info p, movie_keyword mk, keyword k, role_type r, comp_cast_type c
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mc.movie_id AND mc.company_id = cn.id AND t.id = cc.movie_id AND a.person_id = p.person_id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND ci.role_id = r.id AND r.id = c.id AND t.production_year > 2000 AND cn.country_code = 'USA'
ORDER BY t.production_year DESC, a.name;

SELECT t.title AS movie_title, a.name AS actor_name, ct.kind AS cast_type, c.name AS company_name, mi.info AS movie_info, COUNT(k.keyword) AS keyword_count
FROM title t, complete_cast cc, cast_info ci, aka_name a, movie_companies mc, company_name c, movie_info mi, movie_keyword mk, keyword k, comp_cast_type ct
WHERE t.id = cc.movie_id AND cc.subject_id = ci.id AND ci.person_id = a.person_id AND t.id = mc.movie_id AND mc.company_id = c.id AND t.id = mi.movie_id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND ci.person_role_id = ct.id AND t.production_year >= 2000 AND c.country_code = 'USA'
GROUP BY t.title, a.name, ct.kind, c.name, mi.info
ORDER BY keyword_count DESC, t.title;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year, c.note AS role_note
FROM cast_info c, aka_name a, aka_title t
WHERE c.person_id = a.person_id AND c.movie_id = t.movie_id AND t.production_year >= 2000 AND t.production_year <= 2020
ORDER BY t.production_year DESC, a.name;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year, ct.kind AS company_type, k.keyword AS movie_keyword
FROM aka_name a, cast_info ci, title t, movie_companies mc, company_name cn, company_type ct, movie_keyword mk, keyword k
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mc.movie_id AND mc.company_id = cn.id AND mc.company_type_id = ct.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND a.name LIKE '%Smith%' AND t.production_year >= 2000 AND t.production_year <= 2023
GROUP BY a.name, t.title, t.production_year, ct.kind, k.keyword
ORDER BY t.production_year DESC, a.name;

SELECT a.name AS actor_name, t.title AS movie_title, c.kind AS cast_type, co.name AS company_name, m.info AS movie_info, k.keyword AS movie_keyword
FROM aka_name a, cast_info ci, title t, comp_cast_type c, movie_companies mc, company_name co, movie_info m, movie_keyword mk, keyword k
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND ci.person_role_id = c.id AND t.id = mc.movie_id AND mc.company_id = co.id AND t.id = m.movie_id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.production_year >= 2000 AND t.production_year <= 2020 AND co.country_code = 'USA' AND c.kind = 'actor'
ORDER BY t.production_year DESC, a.name ASC;

SELECT a.name AS actor_name, t.title AS movie_title, c.kind AS cast_type, m.info AS movie_info, COUNT(k.keyword) AS keyword_count
FROM aka_name a, cast_info ci, title t, movie_companies mc, company_name cn, movie_info m, movie_keyword mk, keyword k, comp_cast_type c
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mc.movie_id AND mc.company_id = cn.id AND t.id = m.movie_id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND ci.person_role_id = c.id AND t.production_year >= 2000 AND cn.country_code = 'USA'
GROUP BY a.name, t.title, c.kind, m.info
ORDER BY keyword_count DESC, actor_name ASC;

SELECT a.name AS actor_name, t.title AS movie_title, c.note AS role_note, t.production_year
FROM aka_name a, cast_info c, aka_title t
WHERE a.person_id = c.person_id AND c.movie_id = t.id AND t.production_year >= 2000
ORDER BY t.production_year DESC, a.name;

SELECT t.title AS movie_title, a.name AS actor_name, r.role AS role, c.name AS company_name, t.production_year, k.keyword AS movie_keyword
FROM title t, complete_cast cc, cast_info ci, aka_name a, role_type r, movie_companies mc, company_name c, movie_keyword mk, keyword k
WHERE t.id = cc.movie_id AND cc.subject_id = ci.id AND ci.person_id = a.person_id AND ci.role_id = r.id AND t.id = mc.movie_id AND mc.company_id = c.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.production_year > 2000 AND c.country_code = 'USA'
GROUP BY t.title, a.name, r.role, c.name, t.production_year, k.keyword
ORDER BY t.production_year DESC, a.name, t.title;

SELECT t.title AS movie_title, a.name AS actor_name, c.name AS character_name, m.name AS company_name, k.keyword AS movie_keyword, pi.info AS actor_info
FROM title t, complete_cast cc, cast_info ci, aka_name a, char_name c, movie_companies mc, company_name m, movie_keyword mk, keyword k, person_info pi
WHERE t.id = cc.movie_id AND cc.subject_id = ci.id AND ci.person_id = a.person_id AND ci.role_id = c.id AND t.id = mc.movie_id AND mc.company_id = m.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND a.person_id = pi.person_id AND t.production_year >= 2000 AND t.production_year <= 2023
ORDER BY t.production_year DESC, a.name;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year, c.kind AS company_type, COUNT(mc.movie_id) AS number_of_movies
FROM aka_name a, cast_info ci, aka_title t, movie_companies mc, company_type c
WHERE a.person_id = ci.person_id AND ci.movie_id = t.movie_id AND t.id = mc.movie_id AND mc.company_type_id = c.id
GROUP BY a.name, t.title, t.production_year, c.kind
ORDER BY number_of_movies DESC;

SELECT a.name AS actor_name, t.title AS movie_title, c.note AS character_role, t.production_year
FROM aka_name a, cast_info c, aka_title t
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND t.production_year > 2000
ORDER BY t.production_year DESC;

SELECT a.name AS actor_name, t.title AS movie_title, ct.kind AS company_type, mc.note AS company_note, mi.info AS movie_info
FROM aka_name a, cast_info ci, title t, movie_companies mc, company_type ct, movie_info mi, info_type it
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mc.movie_id AND mc.company_type_id = ct.id AND t.id = mi.movie_id AND mi.info_type_id = it.id AND it.info = 'budget' AND t.production_year >= 2000 AND t.production_year <= 2023
GROUP BY a.name, t.title, ct.kind, mc.note, mi.info, t.production_year
ORDER BY t.production_year DESC, actor_name;

SELECT a.name AS actor_name, t.title AS movie_title, c.kind AS company_type, k.keyword AS movie_keyword, pi.info AS person_info
FROM aka_name a, cast_info ci, aka_title t, movie_companies mc, company_type c, movie_keyword mk, keyword k, complete_cast cc, person_info pi
WHERE a.person_id = ci.person_id AND ci.movie_id = t.movie_id AND mc.movie_id = t.id AND mc.company_type_id = c.id AND mk.movie_id = t.id AND mk.keyword_id = k.id AND cc.movie_id = t.id AND pi.person_id = a.person_id AND t.production_year > 2000 AND c.kind LIKE 'Distribution%'
ORDER BY t.production_year DESC, a.name;

SELECT a.name AS actor_name, m.title AS movie_title, m.production_year, c.role_id, COUNT(*) AS total_roles
FROM aka_name a, cast_info c, aka_title m, movie_companies mc, company_name cn
WHERE a.person_id = c.person_id AND c.movie_id = m.movie_id AND m.id = mc.movie_id AND mc.company_id = cn.id
GROUP BY a.name, m.title, m.production_year, c.role_id
ORDER BY total_roles DESC;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year, c.note AS cast_note
FROM aka_name a, cast_info c, aka_title t
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND t.production_year >= 2000
ORDER BY t.production_year DESC, a.name;

SELECT t.title, ak.name AS aka_name, c.nr_order, c.note AS role_note, ct.kind AS company_type, p.info AS person_info
FROM title t, movie_companies mc, company_name cn, company_type ct, complete_cast cc, cast_info c, aka_name ak, person_info p
WHERE t.id = mc.movie_id AND mc.company_id = cn.id AND mc.company_type_id = ct.id AND t.id = cc.movie_id AND cc.subject_id = c.id AND c.person_id = ak.person_id AND ak.person_id = p.person_id AND t.production_year >= 2000
GROUP BY t.title, ak.name, c.nr_order, c.note, ct.kind, p.info
ORDER BY t.title, c.nr_order;

SELECT a.name AS actor_name, t.title AS movie_title, c.kind AS cast_type, co.name AS company_name, m.info AS movie_info, k.keyword AS movie_keyword
FROM aka_name a, cast_info ci, title t, movie_companies mc, company_name co, movie_info m, info_type it, movie_keyword mk, keyword k, comp_cast_type c
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mc.movie_id AND mc.company_id = co.id AND t.id = m.movie_id AND m.info_type_id = it.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND ci.person_role_id = c.id AND t.production_year >= 2000 AND co.country_code = 'USA' AND it.info = 'Plot'
ORDER BY a.name, t.production_year DESC;

SELECT t.title, a.name AS actor_name, t.production_year, COUNT(c.id) AS total_cast_members
FROM title t, movie_companies mc, company_name cn, cast_info c, aka_name a
WHERE t.id = mc.movie_id AND mc.company_id = cn.id AND t.id = c.movie_id AND c.person_id = a.person_id AND t.production_year >= 2000
GROUP BY t.title, a.name, t.production_year
ORDER BY t.production_year DESC, total_cast_members DESC;

SELECT a.name AS aka_name, t.title AS movie_title, c.note AS cast_note
FROM aka_name a, cast_info c, aka_title t
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND a.name LIKE '%Smith%' AND t.production_year > 2000
ORDER BY t.production_year DESC;

SELECT t.title AS movie_title, a.name AS actor_name, ct.kind AS company_type, m.info AS movie_info
FROM title t, complete_cast cc, cast_info ci, aka_name a, movie_companies mc, company_type ct, movie_info m, info_type it, keyword k, kind_type kt
WHERE t.id = cc.movie_id AND cc.subject_id = ci.id AND ci.person_id = a.person_id AND t.id = mc.movie_id AND mc.company_type_id = ct.id AND t.id = m.movie_id AND m.info_type_id = it.id AND t.id = k.id AND t.kind_id = kt.id AND t.production_year >= 2000
GROUP BY t.title, a.name, ct.kind, m.info, t.production_year
ORDER BY t.production_year DESC, a.name;

SELECT a.id AS aka_id, a.name AS aka_name, t.title AS movie_title, c.name AS company_name, p.info AS person_info, k.keyword AS movie_keyword, r.role AS role_type
FROM aka_name a, cast_info ci, title t, movie_companies mc, company_name c, person_info p, movie_keyword mk, keyword k, role_type r
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mc.movie_id AND mc.company_id = c.id AND a.person_id = p.person_id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND ci.role_id = r.id AND t.production_year >= 2000 AND t.production_year <= 2020 AND c.country_code = 'USA' AND k.keyword IS NOT NULL
ORDER BY t.production_year DESC, a.name ASC;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year, c.role_id AS character_role, ct.kind AS company_type, COUNT(*) AS total_roles
FROM aka_name a, cast_info c, aka_title t, movie_companies mc, company_type ct
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND t.id = mc.movie_id AND mc.company_type_id = ct.id
GROUP BY a.name, t.title, t.production_year, c.role_id, ct.kind
ORDER BY total_roles DESC;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year
FROM aka_name a, cast_info c, aka_title t
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND t.production_year > 2000
ORDER BY t.production_year DESC;

SELECT t.title, a.name AS actor_name, ky.kind AS role_type, t.production_year, k.keyword
FROM title t, movie_companies mc, company_name cn, complete_cast cc, cast_info ci, aka_name a, role_type r, movie_keyword mk, keyword k, kind_type ky
WHERE t.id = mc.movie_id AND mc.company_id = cn.id AND t.id = cc.movie_id AND cc.subject_id = ci.id AND ci.person_id = a.person_id AND ci.role_id = r.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.kind_id = ky.id AND t.production_year >= 2000
GROUP BY t.title, a.name, ky.kind, t.production_year, k.keyword
ORDER BY t.production_year DESC, a.name;

SELECT a.name AS aka_name, t.title AS movie_title, c.nr_order, p.info AS person_information, k.keyword AS movie_keyword, co.name AS company_name, ct.kind AS company_type, r.role AS role_description
FROM aka_name a, cast_info c, title t, person_info p, movie_keyword mk, keyword k, movie_companies mc, company_name co, company_type ct, role_type r
WHERE a.person_id = c.person_id AND c.movie_id = t.id AND a.person_id = p.person_id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.id = mc.movie_id AND mc.company_id = co.id AND mc.company_type_id = ct.id AND c.role_id = r.id AND t.production_year > 2000 AND ct.kind = 'Distributor'
ORDER BY t.production_year DESC, a.name ASC;

SELECT ak.name AS aka_name, at.title AS movie_title, ct.kind AS company_type, COUNT(ci.id) AS cast_count
FROM aka_name ak, cast_info ci, aka_title at, movie_companies mc, company_type ct
WHERE ak.person_id = ci.person_id AND ci.movie_id = at.movie_id AND at.id = mc.movie_id AND mc.company_type_id = ct.id
GROUP BY ak.name, at.title, ct.kind
ORDER BY cast_count DESC;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year
FROM aka_name a, cast_info c, aka_title t
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND t.production_year > 2000
ORDER BY t.production_year DESC;

SELECT t.title AS movie_title, a.name AS actor_name, r.role AS actor_role, ct.kind AS company_kind, t.production_year, k.keyword AS movie_keyword
FROM title t, complete_cast cc, cast_info ci, aka_name a, role_type r, movie_companies mc, company_name cn, company_type ct, movie_keyword mk, keyword k
WHERE t.id = cc.movie_id AND cc.subject_id = ci.id AND ci.person_id = a.person_id AND ci.role_id = r.id AND t.id = mc.movie_id AND mc.company_id = cn.id AND mc.company_type_id = ct.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.production_year >= 2000 AND t.production_year <= 2023
GROUP BY t.title, a.name, r.role, ct.kind, t.production_year, k.keyword
ORDER BY t.title, a.name;

SELECT t.title AS movie_title, a.name AS actor_name, ci.nr_order AS character_order, comp.name AS company_name, kt.keyword AS movie_keyword, ti.info AS movie_info, r.role AS role_type
FROM aka_title t, complete_cast cc, cast_info ci, aka_name a, movie_companies mc, company_name comp, movie_keyword mk, keyword kt, movie_info mi, info_type ti, role_type r
WHERE t.id = cc.movie_id AND cc.subject_id = ci.id AND ci.person_id = a.person_id AND t.id = mc.movie_id AND mc.company_id = comp.id AND t.id = mk.movie_id AND mk.keyword_id = kt.id AND t.id = mi.movie_id AND mi.info_type_id = ti.id AND ci.role_id = r.id AND t.production_year >= 2000 AND t.production_year <= 2023 AND comp.country_code = 'USA'
ORDER BY t.production_year DESC, a.name ASC;

SELECT t.title AS movie_title, a.name AS actor_name, ct.kind AS company_type, COUNT(*) AS total_cast
FROM title t, movie_companies mc, company_type ct, complete_cast cc, cast_info ci, aka_name a
WHERE t.id = mc.movie_id AND mc.company_type_id = ct.id AND t.id = cc.movie_id AND cc.subject_id = ci.person_id AND ci.person_id = a.person_id
GROUP BY t.title, a.name, ct.kind
ORDER BY total_cast DESC;

SELECT a.name AS actor_name, t.title AS movie_title, c.nr_order AS role_order
FROM cast_info c, aka_name a, aka_title t
WHERE c.person_id = a.person_id AND c.movie_id = t.movie_id AND t.production_year = 2021
ORDER BY c.nr_order;

SELECT t.title AS movie_title, n.name AS actor_name, a.name AS aka_name, k.keyword AS movie_keyword, co.name AS company_name, rt.role AS role_type, ti.info AS movie_info
FROM title t, complete_cast cc, cast_info ci, aka_name a, name n, movie_keyword mk, keyword k, movie_companies mc, company_name co, role_type rt, movie_info mi, info_type ti
WHERE t.id = cc.movie_id AND cc.subject_id = ci.id AND ci.person_id = a.person_id AND a.person_id = n.imdb_id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.id = mc.movie_id AND mc.company_id = co.id AND ci.role_id = rt.id AND t.id = mi.movie_id AND mi.info_type_id = ti.id AND t.production_year >= 2000
GROUP BY t.title, n.name, a.name, k.keyword, co.name, rt.role, ti.info, t.production_year
ORDER BY t.production_year DESC, t.title;

SELECT a.name AS actor_name, t.title AS movie_title, c.role_id AS actor_role, m.info AS movie_info, k.keyword AS movie_keyword, comp.name AS company_name, ct.kind AS company_type
FROM aka_name a, cast_info c, aka_title t, movie_info m, movie_keyword mk, keyword k, movie_companies mc, company_name comp, company_type ct
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND t.id = m.movie_id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.id = mc.movie_id AND mc.company_id = comp.id AND mc.company_type_id = ct.id AND t.production_year > 2000 AND ct.kind = 'Distributor'
ORDER BY t.production_year DESC, a.name;

SELECT t.title AS movie_title, a.name AS actor_name, ci.nr_order AS actor_order, ct.kind AS company_type, COUNT(mk.keyword_id) AS keyword_count
FROM title t, complete_cast cc, cast_info ci, aka_name a, movie_companies mc, company_type ct, movie_keyword mk
WHERE t.id = cc.movie_id AND ci.id = cc.subject_id AND a.person_id = ci.person_id AND mc.movie_id = t.id AND ct.id = mc.company_type_id AND mk.movie_id = t.id
GROUP BY t.title, a.name, ci.nr_order, ct.kind
ORDER BY t.title, actor_order;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year
FROM aka_name a, cast_info c, aka_title t
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND t.production_year >= 2000
ORDER BY t.production_year DESC;

SELECT t.title AS movie_title, a.name AS actor_name, ct.kind AS company_kind, k.keyword AS movie_keyword, p.info AS person_info
FROM title t, aka_title at, cast_info ci, aka_name a, movie_companies mc, company_type ct, keyword k, person_info p
WHERE t.id = at.movie_id AND at.id = ci.movie_id AND ci.person_id = a.person_id AND t.id = mc.movie_id AND mc.company_type_id = ct.id AND k.id = mc.movie_id AND a.id = p.person_id AND t.production_year >= 2000
GROUP BY t.title, a.name, ct.kind, k.keyword, p.info, t.production_year
ORDER BY t.production_year DESC, a.name;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year, c.kind AS cast_type, k.keyword AS movie_keyword, cn.name AS company_name
FROM aka_name a, cast_info ci, title t, movie_keyword mk, keyword k, movie_companies mc, company_name cn, comp_cast_type c
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.id = mc.movie_id AND mc.company_id = cn.id AND ci.person_role_id = c.id AND t.production_year >= 2000 AND t.production_year <= 2023 AND k.keyword LIKE '%action%'
ORDER BY t.production_year DESC, a.name ASC;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year
FROM aka_name a, cast_info c, aka_title t
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND t.production_year >= 2000
ORDER BY t.production_year DESC;

SELECT t.title AS movie_title, a.name AS person_name, r.role AS role_name, ct.kind AS company_type, y.keyword AS movie_keyword
FROM title t, complete_cast cc, cast_info ci, aka_name a, role_type r, movie_companies mc, company_type ct, company_name cn, movie_keyword mk, keyword y
WHERE t.id = cc.movie_id AND cc.subject_id = ci.person_id AND ci.person_id = a.person_id AND ci.role_id = r.id AND t.id = mc.movie_id AND mc.company_type_id = ct.id AND mc.company_id = cn.id AND t.id = mk.movie_id AND mk.keyword_id = y.id
GROUP BY t.title, a.name, r.role, ct.kind, y.keyword
ORDER BY t.title, a.name;

SELECT t.title, a.name AS actor_name, cct.kind AS cast_type, mn.name AS company_name, mi.info AS movie_info, kw.keyword AS movie_keyword
FROM title t, movie_companies mc, company_name mn, complete_cast cc, cast_info ci, aka_name a, role_type rt, comp_cast_type cct, movie_info mi, movie_keyword mk, keyword kw
WHERE t.id = mc.movie_id AND mc.company_id = mn.id AND t.id = cc.movie_id AND cc.subject_id = ci.id AND ci.person_id = a.person_id AND ci.role_id = rt.id AND ci.person_role_id = cct.id AND t.id = mi.movie_id AND t.id = mk.movie_id AND mk.keyword_id = kw.id AND t.production_year >= 2000 AND mn.country_code = 'USA'
ORDER BY t.production_year DESC, a.name;

SELECT a.name AS actor_name, t.title AS movie_title, c.nr_order AS actor_order
FROM cast_info c, aka_name a, aka_title t
WHERE c.person_id = a.person_id AND c.movie_id = t.movie_id AND t.production_year = 2020
ORDER BY c.nr_order;

SELECT t.title, n.name AS actor_name, a.name AS alias_name, ct.kind AS company_type, k.keyword AS keyword
FROM title t, movie_companies mc, company_name cn, company_type ct, complete_cast cc, aka_name a, cast_info ci, name n, movie_keyword mk, keyword k
WHERE t.id = mc.movie_id AND mc.company_id = cn.id AND mc.company_type_id = ct.id AND t.id = cc.movie_id AND cc.subject_id = a.person_id AND a.person_id = ci.person_id AND t.id = ci.movie_id AND a.person_id = n.imdb_id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.production_year >= 2000
GROUP BY t.title, n.name, a.name, ct.kind, k.keyword
ORDER BY t.title, n.name;

SELECT t.title AS movie_title, ak.name AS actor_name, ct.kind AS company_type, ci.note AS casting_note, mi.info AS movie_info, k.keyword AS movie_keyword, pi.info AS person_info
FROM title t, complete_cast cc, cast_info ci, aka_name ak, movie_companies mc, company_name cn, company_type ct, movie_info mi, movie_keyword mk, keyword k, person_info pi
WHERE t.id = cc.movie_id AND cc.id = ci.id AND ci.person_id = ak.person_id AND t.id = mc.movie_id AND mc.company_id = cn.id AND mc.company_type_id = ct.id AND t.id = mi.movie_id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND ak.person_id = pi.person_id AND t.production_year >= 2000 AND t.production_year <= 2023 AND ci.nr_order < 5 AND ct.kind LIKE 'Production%'
ORDER BY t.production_year DESC, ak.name;

SELECT a.name, t.title, c.note
FROM aka_name a, cast_info c, aka_title t
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND t.production_year > 2000
ORDER BY t.production_year DESC;

SELECT t.title AS movie_title, a.name AS actor_name, c.kind AS cast_type, t.production_year, k.keyword AS movie_keyword
FROM title t, aka_title at, cast_info ci, aka_name a, comp_cast_type c, movie_keyword mk, keyword k, movie_companies mc, company_name cn
WHERE t.id = at.movie_id AND at.id = ci.movie_id AND ci.person_id = a.person_id AND ci.person_role_id = c.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.id = mc.movie_id AND mc.company_id = cn.id AND t.production_year >= 2000
GROUP BY t.title, a.name, c.kind, t.production_year, k.keyword
ORDER BY t.production_year DESC, a.name;

SELECT p.name AS actor_name, m.title AS movie_title, m.production_year, c.role_id, k.keyword
FROM aka_name p, cast_info c, title m, movie_keyword mk, keyword k
WHERE p.person_id = c.person_id AND c.movie_id = m.id AND m.id = mk.movie_id AND mk.keyword_id = k.id AND m.production_year >= 2000 AND m.production_year <= 2023 AND k.keyword LIKE '%action%'
ORDER BY m.production_year DESC, actor_name;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year, c.note AS role_note
FROM cast_info c, aka_name a, aka_title t
WHERE c.person_id = a.person_id AND c.movie_id = t.movie_id AND t.production_year >= 2000
ORDER BY t.production_year DESC;

SELECT a.name AS aka_name, t.title AS movie_title, p.info AS person_info, ct.kind AS comp_type, k.keyword AS movie_keyword, r.role AS role_name
FROM aka_name a, cast_info ci, title t, movie_keyword mk, keyword k, movie_companies mc, company_type ct, company_name cn, person_info p, role_type r
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.id = mc.movie_id AND mc.company_type_id = ct.id AND mc.company_id = cn.id AND a.person_id = p.person_id AND ci.role_id = r.id AND t.production_year = 2023
GROUP BY a.name, t.title, p.info, ct.kind, k.keyword, r.role
ORDER BY t.title, a.name;

SELECT a.name AS actor_name, m.title AS movie_title, c.role_id AS role_id, k.keyword AS movie_keyword, ci.kind AS company_type, ti.info AS movie_info
FROM aka_name a, cast_info c, aka_title m, movie_keyword mk, keyword k, movie_companies mc, company_type ci, movie_info mi, info_type ti
WHERE a.person_id = c.person_id AND c.movie_id = m.movie_id AND m.id = mk.movie_id AND mk.keyword_id = k.id AND mc.movie_id = m.id AND mc.company_type_id = ci.id AND mi.movie_id = m.id AND mi.info_type_id = ti.id AND m.production_year >= 2000 AND c.nr_order < 5 AND k.keyword LIKE '%action%'
ORDER BY a.name, m.title;

SELECT a.name AS actor_name, t.title AS movie_title, c.note AS role_note, t.production_year
FROM aka_name a, cast_info c, aka_title t
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND t.production_year > 2000
ORDER BY a.name, t.production_year;

SELECT t.title AS movie_title, a.name AS actor_name, r.role AS role_type, c.note AS cast_note, t.production_year, k.keyword AS movie_keyword
FROM title t, movie_keyword mk, keyword k, complete_cast cc, cast_info c, aka_name a, role_type r, aka_title at
WHERE t.id = mk.movie_id AND mk.keyword_id = k.id AND t.id = cc.movie_id AND cc.subject_id = c.person_id AND c.person_id = a.person_id AND c.role_id = r.id AND t.id = at.movie_id AND t.production_year > 2000
GROUP BY t.title, a.name, r.role, c.note, t.production_year, k.keyword
ORDER BY t.production_year DESC, a.name;

SELECT a.name AS actor_name, t.title AS movie_title, c.kind AS cast_type, p.info AS person_info, k.keyword AS movie_keyword
FROM aka_name a, cast_info ci, title t, comp_cast_type c, person_info p, movie_keyword mk, keyword k
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND ci.person_role_id = c.id AND a.person_id = p.person_id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.production_year >= 2000 AND t.production_year <= 2023 AND k.keyword LIKE '%drama%'
ORDER BY t.production_year DESC, a.name ASC;

SELECT a.name AS aka_name, t.title AS movie_title, c.note AS cast_note
FROM aka_name a, cast_info c, aka_title t
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND t.production_year = 2021;

SELECT t.title AS movie_title, a.name AS actor_name, ct.kind AS cast_type, t.production_year, k.keyword AS movie_keyword
FROM title t, aka_title at, complete_cast cc, cast_info ci, aka_name a, comp_cast_type ct, movie_keyword mk, keyword k
WHERE t.id = at.movie_id AND t.id = cc.movie_id AND ci.movie_id = t.id AND ci.person_id = a.person_id AND ci.person_role_id = ct.id AND t.id = mk.movie_id AND mk.keyword_id = k.id
GROUP BY t.title, a.name, ct.kind, t.production_year, k.keyword
ORDER BY t.production_year DESC, t.title ASC;

SELECT ak.name AS aka_name, t.title AS movie_title, t.production_year, c.kind AS cast_type, co.name AS company_name, p.info AS person_info, k.keyword AS movie_keyword
FROM aka_name ak, cast_info ci, title t, comp_cast_type c, movie_companies mc, company_name co, person_info p, movie_keyword mk, keyword k
WHERE ak.person_id = ci.person_id AND ci.movie_id = t.id AND ci.person_role_id = c.id AND mc.movie_id = t.id AND mc.company_id = co.id AND p.person_id = ak.person_id AND mk.movie_id = t.id AND mk.keyword_id = k.id AND t.production_year >= 2000 AND co.country_code = 'US' AND k.keyword LIKE '%action%'
ORDER BY t.production_year DESC, ak.name;

SELECT a.name AS actor_name, t.title AS movie_title, c.nr_order AS role_order
FROM cast_info c, aka_name a, aka_title t
WHERE c.person_id = a.person_id AND c.movie_id = t.movie_id AND t.production_year = 2020
ORDER BY c.nr_order;

SELECT t.title, a.name AS actor_name, c.kind AS role_description, tc.production_year, kc.keyword AS movie_keyword
FROM title t, movie_companies mc, company_name cn, movie_keyword mk, keyword kc, complete_cast cc, cast_info ci, aka_name a, comp_cast_type c, title tc
WHERE t.id = mc.movie_id AND mc.company_id = cn.id AND t.id = mk.movie_id AND mk.keyword_id = kc.id AND t.id = cc.movie_id AND cc.subject_id = ci.person_id AND ci.person_id = a.person_id AND ci.role_id = c.id AND t.id = tc.id AND tc.production_year > 2000
GROUP BY t.title, a.name, c.kind, tc.production_year, kc.keyword
ORDER BY tc.production_year DESC, actor_name;

SELECT a.name AS actor_name, t.title AS movie_title, c.kind AS company_type, k.keyword AS movie_keyword, p.info AS person_info
FROM aka_name a, cast_info ci, title t, movie_companies mc, company_type c, movie_keyword mk, keyword k, person_info p
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mc.movie_id AND mc.company_type_id = c.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND a.person_id = p.person_id AND t.production_year >= 2000 AND c.kind = 'Production'
ORDER BY actor_name, movie_title;

SELECT a.name AS actor_name, m.title AS movie_title, c.nr_order AS role_order
FROM aka_name a, cast_info c, aka_title m
WHERE a.person_id = c.person_id AND c.movie_id = m.movie_id AND m.production_year >= 2000
ORDER BY m.production_year DESC;

SELECT t.title, a.name AS actor_name, ct.kind AS company_type, k.keyword AS movie_keyword, pi.info AS person_info
FROM title t, movie_companies mc, company_name cn, company_type ct, movie_keyword mk, keyword k, complete_cast cc, cast_info ci, aka_name a, person_info pi
WHERE t.id = mc.movie_id AND mc.company_id = cn.id AND mc.company_type_id = ct.id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.id = cc.movie_id AND cc.subject_id = ci.id AND ci.person_id = a.person_id AND a.person_id = pi.person_id AND t.production_year >= 2000
GROUP BY t.title, a.name, ct.kind, k.keyword, pi.info
ORDER BY t.title, a.name;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year, rt.role AS role, c.name AS company_name, kt.keyword AS movie_keyword
FROM aka_name a, cast_info ci, title t, role_type rt, movie_companies mc, company_name c, movie_keyword mk, keyword kt
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND ci.role_id = rt.id AND t.id = mc.movie_id AND mc.company_id = c.id AND t.id = mk.movie_id AND mk.keyword_id = kt.id AND t.production_year >= 2000 AND t.production_year <= 2023 AND c.country_code = 'USA'
ORDER BY t.production_year DESC, a.name;

SELECT t.title AS movie_title, a.name AS actor_name, ci.nr_order AS cast_order
FROM title t, cast_info ci, aka_name a
WHERE t.id = ci.movie_id AND ci.person_id = a.person_id AND t.production_year > 2000
ORDER BY t.title, ci.nr_order;

SELECT a.id AS aka_id, a.name AS aka_name, t.id AS title_id, t.title AS movie_title, c.id AS cast_id, n.name AS actor_name, ct.kind AS company_type
FROM aka_name a, cast_info c, title t, movie_companies mc, company_type ct, company_name cn, name n
WHERE a.person_id = c.person_id AND c.movie_id = t.id AND t.id = mc.movie_id AND mc.company_type_id = ct.id AND mc.company_id = cn.id AND c.person_id = n.imdb_id AND t.production_year >= 2000
GROUP BY a.id, a.name, t.id, t.title, c.id, n.name, ct.kind
ORDER BY t.production_year DESC, a.name;

SELECT a.name AS actor_name, t.title AS movie_title, t.production_year, c.kind AS company_type, m.info AS movie_info, k.keyword AS movie_keyword
FROM aka_name a, cast_info ci, title t, movie_companies mc, company_name cn, company_type c, movie_info m, movie_keyword mk, keyword k
WHERE a.person_id = ci.person_id AND ci.movie_id = t.id AND t.id = mc.movie_id AND mc.company_id = cn.id AND mc.company_type_id = c.id AND t.id = m.movie_id AND t.id = mk.movie_id AND mk.keyword_id = k.id AND t.production_year >= 2000 AND t.production_year <= 2020 AND k.keyword LIKE 'Action%'
ORDER BY t.production_year DESC, a.name;

SELECT a.name AS aka_name, t.title AS movie_title, c.note AS cast_note
FROM aka_name a, cast_info c, aka_title t
WHERE a.person_id = c.person_id AND c.movie_id = t.movie_id AND t.production_year = 2020;

