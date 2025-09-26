# AI Fitness Assistant (Flask)

Este proyecto es una aplicación web desarrollada en Flask para corrección de postura y registro de ejercicios físicos usando visión por computadora.

## Características
- Registro e inicio de sesión de usuarios
- Corrección de postura en tiempo real para diferentes ejercicios (curl de bíceps, sentadillas, push-ups)
- Historial de ejercicios y errores
- Exportación de historial a Excel
- Visualización de curva de aprendizaje

## Requisitos
- Python 3.11+
- MySQL Server (o SQLite para pruebas)
- pip

### Dependencias Python
- Flask
- Flask-WTF
- Flask-Bcrypt
- Flask-SQLAlchemy
- pandas
- openpyxl
- matplotlib
- mediapipe
- opencv-python

Puedes instalar todas las dependencias con:

```bash
pip install Flask Flask-WTF Flask-Bcrypt Flask-SQLAlchemy pandas openpyxl matplotlib mediapipe opencv-python
```

## Configuración
1. Clona este repositorio y entra a la carpeta `backend`:
   ```bash
   git clone <URL_DEL_REPO>
   cd backend
   ```
2. Configura la base de datos en `app.py`:
   - Por defecto usa MySQL:  
     `app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:admin@localhost/fitter'`
   - Puedes cambiarlo a SQLite para pruebas:
     ```python
     app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitter.db'
     ```
3. Crea la base de datos y las tablas:
   ```bash
   python app.py
   ```
   El servidor creará las tablas automáticamente al iniciar.

## Ejecución
Desde la carpeta `backend` ejecuta:

```bash
python app.py
```

Abre tu navegador en [http://localhost:5000](http://localhost:5000)

## Notas
- Para usar la corrección de postura necesitas una cámara web conectada.
- El sistema está pensado para uso local y pruebas. Si lo despliegas en producción, asegúrate de proteger las credenciales y usar HTTPS.

## Estructura de carpetas
```
backend/
  app.py
  models.py
  forms.py
  PoseModule.py
  pose_left.py
  pose_right.py
  pose_pushup.py
  pose_squat.py
  templates/
  static/
  instance/
```

## Créditos
Desarrollado por Jymon y colaboradores. Basado en Flask, OpenCV y MediaPipe.
