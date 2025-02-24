import os
import requests
import mimetypes
import json
from urllib import request
from flask import Flask, jsonify
from requests.auth import HTTPDigestAuth
from tago import Analysis

app = Flask(__name__)

# Configuración
host = "34.221.158.219"
devIndex = "F5487AA0-2485-4CFB-9304-835DCF118B43"
url_delete_face = f"http://{host}/ISAPI/Intelligent/FDLib/FDSearch/Delete?format=json&devIndex={devIndex}"
url_create_face = f"http://{host}/ISAPI/Intelligent/FDLib/FaceDataRecord?format=json&devIndex={devIndex}"
username = 'admin'
password = 'Inteliksa6969'


# Función para sincronizar usuarios con Hikvision
def sync_users():
    logs = []

    # Eliminar rostros existentes
    for usuario in usuarios_sap:
        employee_no = usuario.get("employeeNo")
        if not employee_no:
            continue

        delete_payload = {
            "FaceInfoDelCond": {
                "faceLibType": "blackFD",
                "EmployeeNoList": [{"employeeNo": employee_no}]
            }
        }

        try:
            response = requests.put(URL_DELETE_FACE, json=delete_payload, auth=HTTPDigestAuth(HIKVISION_USERNAME, HIKVISION_PASSWORD), timeout=10)
            if response.status_code == 200:
                logs.append(f"🗑️ Rostro eliminado para empleado {employee_no}")
            else:
                logs.append(f"⚠️ Error al eliminar rostro para {employee_no}: {response.text}")
        except requests.exceptions.RequestException as e:
            logs.append(f"⚠️ Error en la solicitud DELETE para {employee_no}: {e}")

    # Filtrar usuarios con faceURL
    usuarios_a_subir = [u for u in usuarios_sap if u.get("faceURL")]
    logs.append(f"Usuarios a subir: {len(usuarios_a_subir)}")

    # Subir imágenes a Hikvision
    for usuario in usuarios_a_subir:
        image_url = usuario.get("faceURL")
        employee_no = usuario.get("employeeNo")

        if not image_url:
            logs.append(f"Error: El empleado {employee_no} no tiene una URL de imagen válida.")
            continue

        temp_image_path = f"{employee_no}.jpg"
        logs.append(f"Descargando imagen para empleado {employee_no}: {image_url}")

        try:
            request.urlretrieve(image_url, temp_image_path)

            if not os.path.exists(temp_image_path) or os.path.getsize(temp_image_path) == 0:
                logs.append(f"Error: No se pudo descargar correctamente la imagen para {employee_no}.")
                continue

            with open(temp_image_path, "rb") as img_file:
                img_data = img_file.read()

            file_type = mimetypes.guess_type(temp_image_path)[0] or 'image/jpeg'

            face_info = {
                "FaceInfo": {
                    "employeeNo": employee_no,
                    "faceLibType": "blackFD"
                }
            }

            files = {'FaceDataRecord': ("face.jpg", img_data, file_type)}
            data = {'data': json.dumps(face_info)}

            response = requests.post(URL_CREATE_FACE, data=data, files=files, auth=HTTPDigestAuth(HIKVISION_USERNAME, HIKVISION_PASSWORD), timeout=10)
            if response.status_code == 200:
                logs.append(f"✅ Rostro agregado correctamente para {employee_no}")
            else:
                logs.append(f"❌ Error al agregar rostro para {employee_no}: {response.text}")

        except Exception as e:
            logs.append(f"⚠️ Error al procesar imagen para {employee_no}: {e}")

        finally:
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
                logs.append(f"🗑️ Archivo temporal eliminado: {temp_image_path}")

    context.log("Proceso completado.")
@app.route('/sync', methods=['POST'])
def sync():
    sync_users()
    return jsonify({"status": "success", "message": "Sincronización completada"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
# Análisis principal
def my_analysis(context, scope):
    context.log('Iniciando análisis...')
    context.log('Alcance del análisis:', scope)
    sync_users(context)


# Endpoint en Flask para iniciar la sincronización
@app.route('/sync-users', methods=['GET'])
def api_sync_users():
    logs = sync_users()
    return jsonify({"status": "OK", "logs": logs})

# Iniciar el servidor Flask
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
