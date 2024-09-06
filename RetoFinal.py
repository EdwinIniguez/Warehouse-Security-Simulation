import json
from flask import Flask, request, jsonify
import agentpy as ap

app = Flask(__name__)

# Agente Camara
class Camara(ap.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.precision = 0.9  # Probabilidad de detección correcta
        self.falsas_alarmas = 0
        self.position = [0, 0]  # Posición inicial de la cámara

    def setup(self, *args, **kwargs):
        # Configuración inicial, si es necesario
        print(f"{self}: Configuración inicial completada.")

    def step(self):
        # Comportamiento de la cámara en cada paso
        print(f"{self}: Ejecutando paso de simulación.")
        # Aquí puedes llamar a tus métodos como detect_movement() si corresponde

    def detect_movement(self, agent_model, event_data):
        if event_data['detected_movement']:
            if self.model.np_random.random() < self.precision:  # Detección correcta
                mensaje = {
                    'performativa': 'alarma',
                    'contenido': {
                        'evento': 'Ladrón detectado',
                        'ubicación': event_data['camara_position']
                    }
                }
                agent_model.enviar_mensaje(mensaje, agent_model.dron)
            else:
                self.falsas_alarmas += 1
                print(f"{self}: Falsa alarma, total: {self.falsas_alarmas}")


# Agente Dron
class Dron(ap.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.investigando = False
        self.mensaje_buzon = []
        self.bateria = 100  # Batería del dron
        self.position = [0, 0, 0]  # Posición inicial del dron

    def setup(self, *args, **kwargs):
        print(f"{self}: Configuración inicial completada.")

    def step(self):
        # Comportamiento del dron en cada paso
        print(f"{self}: Ejecutando paso de simulación.")
        self.investigar(self.model)

    def recibir_mensaje(self, mensaje):
        self.mensaje_buzon.append(mensaje)

    def investigar(self, model):
        if self.bateria <= 0:
            print(f"{self}: No puede investigar, batería agotada.")
            return
        for mensaje in self.mensaje_buzon:
            if mensaje['performativa'] == 'alarma':
                ubicacion = mensaje['contenido']['ubicación']
                print(f"{self}: Investigando {mensaje['contenido']['evento']} en {ubicacion}")
                self.investigando = True
                model.personal_seguridad.recibir_mensaje(mensaje)
                self.bateria -= 10  # Gastar batería por cada investigación
        self.mensaje_buzon.clear()


# Agente Personal de Seguridad
class PersonalSeguridad(ap.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.alertado = False
        self.mensaje_buzon = []
        self.falsas_alarmas = 0

    def setup(self, *args, **kwargs):
        print(f"{self}: Configuración inicial completada.")

    def step(self):
        # Comportamiento del personal de seguridad en cada paso
        print(f"{self}: Ejecutando paso de simulación.")
        self.evaluar_amenaza()
        

    def recibir_mensaje(self, mensaje):
        self.mensaje_buzon.append(mensaje)

    def evaluar_amenaza(self):
        for mensaje in self.mensaje_buzon:
            if mensaje['performativa'] == 'alarma':
                print(f"{self}: Evaluando {mensaje['contenido']['evento']} en {mensaje['contenido']['ubicación']}")
                if self.model.np_random.random() < 0.8:  # 80% probabilidad de ser amenaza real
                    print(f"{self}: Amenaza real detectada.")
                    self.alertado = True
                else:
                    self.falsas_alarmas += 1
                    print(f"{self}: Falsa alarma detectada. Total: {self.falsas_alarmas}")
        self.mensaje_buzon.clear()


# Modelo de almacén
class AlmacenModel(ap.Model):
    def __init__(self):
        super().__init__()
        self.dron = None
        self.personal_seguridad = None
        self.camaras = None

    def setup(self):
        # Inicialización de los agentes
        self.dron = Dron(self)
        self.personal_seguridad = PersonalSeguridad(self)
        self.camaras = ap.AgentList(self, 5, Camara)

        # Ejecutar el setup de todos los agentes
        self.dron.setup()
        self.personal_seguridad.setup()
        for camara in self.camaras:
            camara.setup()

    def step(self):
        # Ejecutar el step de todos los agentes
        self.dron.step()
        self.personal_seguridad.step()
        for camara in self.camaras:
            camara.step()

    def recibir_datos_json(self, datos_json):
        try:
            datos = json.loads(datos_json)
            if 'drone_position' not in datos:
                raise ValueError("Falta la posición del dron en los datos JSON.")
            self.dron.position = datos['drone_position']
            for idx, camara in enumerate(self.camaras):
                event_data = {
                    'camara_position': datos.get(f'camara_{idx}_position', [0, 0]),
                    'detected_movement': datos.get(f'camara_{idx}_detected_movement', False)
                }
                camara.detect_movement(self, event_data)
        except json.JSONDecodeError:
            print("Error al decodificar el JSON.")
        except ValueError as e:
            print(f"Error en los datos recibidos: {e}")

    def enviar_mensaje(self, mensaje, agente):
        agente.recibir_mensaje(mensaje)

    def generar_respuesta_json(self):
        estado_dron = {
            'investigando': self.dron.investigando,
            'bateria': self.dron.bateria,
            'dron_position': self.dron.position,
        }
        estado_seguridad = {
            'alertado': self.personal_seguridad.alertado,
            'falsas_alarmas': self.personal_seguridad.falsas_alarmas
        }

        return json.dumps({
            'estado_dron': estado_dron,
            'estado_seguridad': estado_seguridad
        })


# Instanciar el modelo
model = AlmacenModel()

# API Flask para recibir datos y responder a Unity
@app.route('/unity-to-python', methods=['POST'])
def unity_to_python():
    try:
        data = request.json
        if not data:
            raise ValueError("No se recibieron datos del JSON.")
        print("Datos recibidos de Unity:", data)

        # Actualiza el estado del modelo
        model.recibir_datos_json(json.dumps(data))

        # Ejecuta un paso del modelo
        model.step()

        # Generar la respuesta en JSON
        response = model.generar_respuesta_json()
        print("Enviando respuesta a Unity:", response)

        return jsonify(json.loads(response))

    except json.JSONDecodeError:
        print("Error al decodificar el JSON.")
    except ValueError as e:
        print(f"Error en los datos recibidos: {e}")
        print("Error occurred:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
