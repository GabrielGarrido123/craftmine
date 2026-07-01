==========================
INSTRUCCIONES DE EJECUCIÓN
==========================
La tarea contiene solo las librerias del curso (utils, shaders, grafica) y los assets de la tarea en si.
Esto significa que hay 2 alternativas para ejecutar la tarea:

1) Si la persona revisando esto tiene el repositorio de auxiliares en su computador (https://github.com/asouris/CC3501) y
ya instaló las librerias, entonces recomiendo que la carpeta donde se encuentra app.py, sea ubicada en la raiz del entorno
virtual que posiblemente ya tiene creado (quizas llamado venv, de acuerdo a Setup.md en el repositorio anteriormente mencionado).
Esto deberia ejecutar la tarea sin problema, y sin tener que pasar por el proceso de instalar las librerias desde 0.

2) Si en cambio se busca hacer una ejecucion en un computador cualquiera (o lo anterior no funcionó), seguir las instrucciones de abajo:

PASO 0 (general):
Este README lo debe encontrar en la carpeta que descomprimió. Lo mas probable es que entonces se llame "Tarea3GG".
Esto es importante, ya que las instrucciones siguientes asumen que la carpeta donde se encuentra la tarea se llama así.

PASO 1 (general):
Usando un explorador de archivos, abra en una terminal la carpeta. En el caso especifico de Windows asegurarse que la consola sea "PowerShell".
Para hacer lo anterior, haga clic derecho en algún espacio vacío de la ventana (con la carpeta abierta), y presione "Abrir en una terminal"
(o alguna opción similar en su sistema). De no encontrar esa opción, abra la terminal de la forma que se haga en su sistema, y
ejecute "cd [ruta a esta carpeta]".

PASO 2 (general):
Asegúrese de tener Python instalado. Esta tarea se realizó con python 3.14, aunque podría funcionar sin problema con versiones anteriores (como la 3.13).
Siga las instrucciones del sitio oficial de Python en caso de necesitar instalarlo. (https://www.python.org)

PASO 3 - Para WINDOWS:
Ahora, estando en Power Shell, ejecute primero "cd ..". Esto lo debería llevar a la carpeta donde sea que se encuentre "Tarea3GG" (por ejemplo en Descargas).

PASO 3 - Para LINUX y MAC:
Ahora, estando en su consola, ejecute primero "cd ..". Esto lo debería llevar a la carpeta donde sea que se encuentre "Tarea3GG" (por ejemplo en Descargas, o en el home).

PASO 4 (general):
Luego, ejecute "python -m venv Tarea3GG". Esto añadirá los archivos necesarios a la carpeta anteriormente mencionada.

Una vez realizado esto, vuelva a la carpeta, ejecutando "cd Tarea3GG"

PASO 5 - Para WINDOWS:
Ejecute "Set-ExecutionPolicy AllSigned -Scope CurrentUser". Si le pide confirmación, acepte.

Luego, ejecute "Scripts\Activate.ps1". De nuevo, si pide confirmación de ejecución, permita que se ejecute el script.

Ahora debería aparecer (Tarea3GG) al inicio de su línea de comandos.

PASO 5 - Para LINUX y MAC:
Ejecute "source bin/activate". Debería aparecer (Tarea3GG) al inicio de su línea de comandos.

PASO 6 (general):
Instalar las librerías necesarias usando pip: ejecute "pip install numpy==2.3.5 pyglet pyopengl trimesh scipy networkx pillow".
Espere a que termine la instalación.

Finalmente, ejecute "python app.py". Esto abrirá la tarea.

==========================================
	ASIGNACION DE TECLAS
==========================================
Principales
- wASD: Teclas para mover al personaje
- ESPACIO: Saltar
- T: Avanzar más rápido el tiempo

Extras
- F3: Activar el debug (ver FPS y posicion)
- F5: Activar el modo wireframe
- M: Desbloquear el movimiento del mouse (para que no este fijo en la ventana del juego)

==========================================
    PUNTAJES Y OTROS
==========================================
De la tabla de puntaje, quise implementar los siguientes puntos. Tambien añado alguna referencia a dónde pueden encontrar ese tema,
para quizas facilitar la revision de esta ensalada de texto llamada "codigo"...

*Skybox o entorno 3D (2pts)
- Empieza aproximadamente en la linea 389 y usa los shaders "sky" dentro de la carpeta 'game_shaders'. Luego aparecen mas lineas
en el update(dt) al final del codigo, aprox en la linea 554.

*Sistema de colisiones (2pts)
- Funcion player_colisions() en clase Player, linea 176 aprox.
Tambien en la funcion check_colisions(), aprox. en linea 340.
La colision de los cubos se añade en el generador de mundo, linea 409 aprox.

*Cinematica / Gravedad / Fisicas (2pts)
- Esta definido dentro de la clase Player, en la funcion player_update() (linea 103 aprox.)

Con esto estimo que la suma de puntos es 6pts.

Notar que de la tabla se hizo tambien "Manejo 3D de algun item anterior" y "Modelo de iluminacion Phong",
pero estos no eran los que buscaba implementar como tal.

Por ultimo, en esta tarea no hay absolutamente nada de inteligencia artificial. Solamente se uso conocimientos del curso y de auxiliares :)