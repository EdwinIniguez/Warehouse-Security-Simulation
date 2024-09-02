from flask import Flask, request, jsonify
import agentpy as ap

# Inicialización de la API
app = Flask(__name__)

# Definición de la Clase Camara-----------------------------------------------------------------------------
class Camara(ap.Agent):
    def setup(self):
        self.detected_movement = False

    def detect_movement(self, environment):
        # Simulación de la detección de movimiento
        self.detected_movement = self.model.random.choice([True, False]) #Aqui entra la vision computacional para definir si se encontro una amenaza o no
        if self.detected_movement:
            self.model.dron.notify_suspicion(self)

# Definición de la Clase Dron-----------------------------------------------------------------------------
class Dron(ap.Agent):
    def setup(self):
        self.suspicion_detected = False
        self.investigating = False

    def notify_suspicion(self, camara):
        print(f'Dron: Movimiento sospechoso detectado por {camara}.')
        self.suspicion_detected = True

    def investigate(self):
        if self.suspicion_detected and not self.investigating:
            print('Dron: Investigando la zona sospechosa...')
            self.investigating = True
            self.suspicion_detected = False
            if self.model.random.choice([True, False]): #Aqui entra la vision computacional para definir si se encontro una amenaza o no
                print('Dron: Se encontró algo sospechoso.')
                self.model.security_personnel.notify_threat(self)
            else:
                print('Dron: No se encontró nada sospechoso.')
            self.investigating = False

# Definición de la Clase PersonalSeguridad-----------------------------------------------------------------------------
class PersonalSeguridad(ap.Agent):
    def setup(self):
        self.alerted = False

    def notify_threat(self, dron):
        print('Personal de Seguridad: Recibido informe del dron sobre posible amenaza.')
        self.alerted = True

    def evaluate_threat(self):
        if self.alerted:
            print('Personal de Seguridad: Evaluando la amenaza...')
            if self.model.random.choice([True, False]): #Aqui entra la vision computacional para definir si se encontro una amenaza o no
                print('Personal de Seguridad: ¡Alerta general activada!')
            else:
                print('Personal de Seguridad: Falsa alarma. No hay amenaza.')
            self.alerted = False

# Definición del Modelo de Almacén-----------------------------------------------------------------------------
class AlmacenModel(ap.Model):
    def setup(self):
        # Crear agentes
        self.dron = Dron(self)
        self.camaras = ap.AgentList(self, 3, Camara)
        self.security_personnel = PersonalSeguridad(self)
    
    def step(self):
        # Las cámaras buscan movimiento
        for camara in self.camaras:
            camara.detect_movement(self)
        
        # El dron investiga si se detectó algo
        self.dron.investigate()
        
        # El personal de seguridad evalúa si se ha detectado una amenaza
        self.security_personnel.evaluate_threat()

# Inicializa el modelo-----------------------------------------------------------------------------
parameters = {'steps': 1}  # Solo un paso por llamada para sincronización con Unity
model = AlmacenModel(parameters)


# Rutas de la API-----------------------------------------------------------------------------

# Aquí se asume que las clases de los agentes y el modelo ya están definidas

@app.route('/unity-to-python', methods=['POST'])
def unity_to_python():
    try:
        data = request.json
        print("Datos recibidos de Unity:", data)

        # Aquí puedes actualizar el estado del modelo con la información de Unity si es necesario

        model.step()  # Ejecuta un paso del modelo

        # Envía la respuesta del modelo a Unity
        response = {
            "drone_status": "Investigating" if model.dron.investigating else "Idle",
            "security_alert": "True" if model.security_personnel.alerted else "False"
        }
        
        print("Enviando respuesta a Unity:", response)
        return jsonify(response)
    
    except ValueError as ve:
        print("ValueError occurred:", str(ve))
    except KeyError as ke:
        print("KeyError occurred:", str(ke))
    except IndexError as ie:
        print("IndexError occurred:", str(ie))
    except Exception as e:
        print("An error occurred:", str(e))
        print("Ocurrió un error:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
