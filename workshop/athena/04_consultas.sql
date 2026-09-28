-- 1) Ver las primeras filas
SELECT * FROM workshop_aws_101_<tus_iniciales>.transacciones LIMIT 10;

-- 2) Total aprobado por tipo de transacción
SELECT tipo, COUNT(*) AS cantidad, SUM(monto) AS total_cop
FROM workshop_aws_101_<tus_iniciales>.transacciones
WHERE estado = 'APROBADA'
GROUP BY tipo
ORDER BY total_cop DESC;

-- 3) Top 5 clientes por monto aprobado
SELECT cliente_id, nombre_cliente, SUM(monto) AS total_cop
FROM workshop_aws_101_<tus_iniciales>.transacciones
WHERE estado = 'APROBADA'
GROUP BY cliente_id, nombre_cliente
ORDER BY total_cop DESC
LIMIT 5;

-- 4) JOIN con la tabla de clientes: gasto por segmento
SELECT c.segmento, COUNT(t.id_transaccion) AS transacciones, SUM(t.monto) AS total_cop
FROM workshop_aws_101_<tus_iniciales>.transacciones t
JOIN workshop_aws_101_<tus_iniciales>.clientes c ON t.cliente_id = c.cliente_id
WHERE t.estado = 'APROBADA'
GROUP BY c.segmento
ORDER BY total_cop DESC;

-- 5) Transacciones rechazadas o pendientes (revisión operativa)
SELECT fecha, id_transaccion, nombre_cliente, tipo, monto, estado
FROM workshop_aws_101_<tus_iniciales>.transacciones
WHERE estado <> 'APROBADA'
ORDER BY fecha;
