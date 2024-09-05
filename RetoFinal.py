import json
from flask import Flask, request, jsonify
import agentpy as ap
#from owlready2 import *

app = Flask(__name__)

# Definimos el modelo con agentes (Dron, Camara, PersonalSeguridad)
class Camara(ap.Agent):
    def detect_movement(self, agent_model, event_data):
        if event_data['detected_movement']:
            mensaje = {
                'performativa': 'alarma',
                'contenido': {
                    'evento': 'Ladrón detectado',
                    'ubicación': event_data['camara_position']
                }
            }
            agent_model.enviar_mensaje(mensaje, agent_model.dron)

class Dron(ap.Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.investigando = False
        self.mensaje_buzon = []
    
    def recibir_mensaje(self, mensaje):
        self.mensaje_buzon.append(mensaje)
    
    def investigar(self, model):
        for mensaje in self.mensaje_buzon:
            if mensaje['performativa'] == 'alarma':
                ubicacion = mensaje['contenido']['ubicación']
                print(f"{self}: Investigando {mensaje['contenido']['evento']} en {ubicacion}")
                self.investigando = True
                model.personal_seguridad.recibir_mensaje(mensaje)
        self.mensaje_buzon.clear()

class PersonalSeguridad(ap.Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alertado = False
        self.mensaje_buzon = []
    
    def recibir_mensaje(self, mensaje):
        self.mensaje_buzon.append(mensaje)
    
    def evaluar_amenaza(self):
        for mensaje in self.mensaje_buzon:
            if mensaje['performativa'] == 'alarma':
                print(f"{self}: Evaluando {mensaje['contenido']['evento']} en {mensaje['contenido']['ubicación']}")
                self.alertado = True
        self.mensaje_buzon.clear()

# Modelo de almacén
class AlmacenModel(ap.Model):
    def __init__(self):
        super().__init__()
        self.dron = Dron(self)
        self.personal_seguridad = PersonalSeguridad(self)
        self.camaras = ap.AgentList(self, 3, Camara)
        self.dron.position = [0, 0]

    def setup(self):
        for idx, camara in enumerate(self.camaras):
            camara.position = [0, idx * 10]
    
    def recibir_datos_json(self, datos_json):
        try:
            datos = json.loads(datos_json)
            self.dron.position = datos['drone_position']
            for idx, camara in enumerate(self.camaras):
                event_data = {
                    'camara_position': datos.get(f'camara_{idx}_position', [0, 0]),
                    'detected_movement': datos.get(f'camara_{idx}_detected_movement', False)
                }
                camara.detect_movement(self, event_data)
        except json.JSONDecodeError:
            print("Error al decodificar el JSON")

    def enviar_mensaje(self, mensaje, agente):
        agente.recibir_mensaje(mensaje)

    def generar_respuesta_json(self):
        estado_dron = {
            'investigando': self.dron.investigando,
            'dron_position': self.dron.position,
        }
        estado_seguridad = {
            'alertado': self.personal_seguridad.alertado
        }
        return json.dumps({
            'estado_dron': estado_dron,
            'estado_seguridad': estado_seguridad
        })

    def step(self):
        self.dron.investigar(self)
        self.personal_seguridad.evaluar_amenaza()

# Crear instancia del modelo
model = AlmacenModel()

# API para recibir datos de Unity
@app.route('/unity-to-python', methods=['POST'])
def unity_to_python():
    try:
        data = request.json
        print("Datos recibidos de Unity:", data)
        
        # Actualiza el estado del modelo
        model.recibir_datos_json(json.dumps(data))

        # Ejecuta un paso del modelo
        model.step()

        # Generar la respuesta en JSON
        response = model.generar_respuesta_json()
        print("Enviando respuesta a Unity:", response)
        
        return jsonify(json.loads(response))
    
    except Exception as e:
        print("Error occurred:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
