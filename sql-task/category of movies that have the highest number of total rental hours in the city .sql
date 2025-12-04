WITH city_rentals AS (
    SELECT 
        ci.city,
        c.name AS category,
        SUM(EXTRACT(EPOCH FROM (r.return_date - r.rental_date)) / 3600) AS total_hours
    FROM rental r
    JOIN inventory i ON r.inventory_id = i.inventory_id
    JOIN film f ON i.film_id = f.film_id
    JOIN film_category fc ON f.film_id = fc.film_id
    JOIN category c ON fc.category_id = c.category_id
    JOIN customer cu ON r.customer_id = cu.customer_id
    JOIN address a ON cu.address_id = a.address_id
    JOIN city ci ON a.city_id = ci.city_id
    WHERE ci.city ILIKE 'a%' OR ci.city LIKE '%-%'
    GROUP BY ci.city, c.name
),
ranked AS (
    SELECT 
        city,
        category,
        total_hours,
        RANK() OVER (PARTITION BY city ORDER BY total_hours DESC) AS rnk
    FROM city_rentals
)
SELECT city, category, total_hours
FROM ranked
WHERE rnk = 1
ORDER BY city;
