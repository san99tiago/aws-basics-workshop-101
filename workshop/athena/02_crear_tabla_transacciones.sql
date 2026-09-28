-- Athena: tabla EXTERNA sobre los CSV del prefijo entrada/ (los datos NO se copian, siguen en S3)
CREATE EXTERNAL TABLE IF NOT EXISTS workshop_aws_101_<tus_iniciales>.transacciones (
  id_transaccion string,
  cliente_id     string,
  nombre_cliente string,
  fecha          string,
  tipo           string,
  monto          bigint,
  moneda         string,
  ciudad         string,
  canal          string,
  estado         string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"', 'escapeChar' = '\\')
STORED AS TEXTFILE
LOCATION 's3://workshop-aws-101-<tus-iniciales>/entrada/'
TBLPROPERTIES ('skip.header.line.count' = '1');
