"""
AWS Basics Workshop 101 - Lambda "procesar-transacciones"
----------------------------------------------------------
Se ejecuta cuando EventBridge detecta un archivo CSV nuevo en S3 (prefijo entrada/).

Flujo / Flow:
  1. Lee el CSV desde S3                      -> Reads the CSV from S3
  2. Guarda cada fila en DynamoDB (PK + SK)   -> Stores each row in DynamoDB (PK + SK)
  3. Calcula un resumen                       -> Builds a summary
  4. Envía el resumen por correo con SES      -> Emails the summary with SES

Variables de entorno / Environment variables:
  TABLE_NAME        Nombre de la tabla DynamoDB (ej: transacciones-<iniciales>)
  SENDER_EMAIL      Correo verificado en SES (remitente)
  DESTINATION_EMAIL Correo verificado en SES (destinatario)
"""
import csv
import io
import json
import os
import urllib.parse
from collections import defaultdict
from decimal import Decimal

import boto3

TABLE_NAME = os.environ["TABLE_NAME"]
SENDER_EMAIL = os.environ["SENDER_EMAIL"]
DESTINATION_EMAIL = os.environ["DESTINATION_EMAIL"]

s3 = boto3.client("s3")
ses = boto3.client("ses")
table = boto3.resource("dynamodb").Table(TABLE_NAME)


def extraer_bucket_y_key(event: dict) -> tuple[str, str]:
    """Soporta eventos de EventBridge (S3 Object Created) y el evento de prueba manual."""
    if "detail" in event:  # EventBridge -> S3 "Object Created"
        return event["detail"]["bucket"]["name"], urllib.parse.unquote_plus(event["detail"]["object"]["key"])
    return event["bucket"], event["key"]  # Evento de prueba: {"bucket": "...", "key": "entrada/archivo.csv"}


def leer_csv(bucket: str, key: str) -> list[dict]:
    respuesta = s3.get_object(Bucket=bucket, Key=key)
    contenido = respuesta["Body"].read().decode("utf-8-sig")  # utf-8-sig tolera el BOM de Excel
    return list(csv.DictReader(io.StringIO(contenido)))


def guardar_en_dynamodb(filas: list[dict], archivo: str) -> int:
    """PK = cliente_id  |  SK = fecha#id_transaccion  (permite consultar por cliente y ordenar por fecha)."""
    with table.batch_writer() as batch:
        for fila in filas:
            batch.put_item(
                Item={
                    "cliente_id": fila["cliente_id"],
                    "fecha_id": f'{fila["fecha"]}#{fila["id_transaccion"]}',
                    "id_transaccion": fila["id_transaccion"],
                    "nombre_cliente": fila["nombre_cliente"],
                    "fecha": fila["fecha"],
                    "tipo": fila["tipo"],
                    "monto": Decimal(fila["monto"]),
                    "moneda": fila["moneda"],
                    "ciudad": fila["ciudad"],
                    "canal": fila["canal"],
                    "estado": fila["estado"],
                    "archivo_origen": archivo,
                }
            )
    return len(filas)


def construir_resumen(filas: list[dict], archivo: str) -> str:
    total = sum(Decimal(f["monto"]) for f in filas if f["estado"] == "APROBADA")
    por_tipo = defaultdict(Decimal)
    por_estado = defaultdict(int)
    for f in filas:
        por_estado[f["estado"]] += 1
        if f["estado"] == "APROBADA":
            por_tipo[f["tipo"]] += Decimal(f["monto"])

    lineas = [
        f"Archivo procesado: {archivo}",
        f"Transacciones leídas: {len(filas)}",
        f"Total aprobado (COP): {total:,.0f}",
        "",
        "Por estado:",
        *[f"  - {estado}: {cantidad}" for estado, cantidad in sorted(por_estado.items())],
        "",
        "Monto aprobado por tipo:",
        *[f"  - {tipo}: {monto:,.0f}" for tipo, monto in sorted(por_tipo.items())],
        "",
        "Procesado automáticamente por AWS Lambda + EventBridge (AWS Basics Workshop 101).",
    ]
    return "\n".join(lineas)


def enviar_correo(asunto: str, cuerpo: str) -> str:
    respuesta = ses.send_email(
        Source=SENDER_EMAIL,
        Destination={"ToAddresses": [DESTINATION_EMAIL]},
        Message={
            "Subject": {"Data": asunto, "Charset": "UTF-8"},
            "Body": {"Text": {"Data": cuerpo, "Charset": "UTF-8"}},
        },
    )
    return respuesta["MessageId"]


def lambda_handler(event, context):
    print("Evento recibido:", json.dumps(event))
    bucket, key = extraer_bucket_y_key(event)

    if not key.lower().endswith(".csv"):
        print(f"Se ignora el objeto {key} porque no es un CSV")
        return {"status": "IGNORADO", "key": key}

    filas = leer_csv(bucket, key)
    guardadas = guardar_en_dynamodb(filas, key)
    resumen = construir_resumen(filas, key)
    print(resumen)

    message_id = enviar_correo(asunto=f"[Workshop AWS] Resumen de {key}", cuerpo=resumen)
    return {"status": "OK", "archivo": key, "transacciones": guardadas, "ses_message_id": message_id}
