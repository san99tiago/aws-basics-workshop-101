-- Athena: tabla EXTERNA de clientes (prefijo referencia/clientes/)
CREATE EXTERNAL TABLE IF NOT EXISTS workshop_aws_101_<tus_iniciales>.clientes (
  cliente_id        string,
  nombre            string,
  ciudad            string,
  segmento          string,
  fecha_vinculacion string,
  correo            string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"', 'escapeChar' = '\\')
STORED AS TEXTFILE
LOCATION 's3://workshop-aws-101-<tus-iniciales>/referencia/clientes/'
TBLPROPERTIES ('skip.header.line.count' = '1');
