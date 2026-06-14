# craftmine
Una recreacion de Minecraft a modo de proyecto final del curso CC3501 - Modelación y Computación Gráfica para Ingenieros de la FCFM, Universidad de Chile.

* Contiene codigo de https://github.com/asouris/CC3501

## Controles / KeyBindings
- ´W A S D´ - Mover al jugador. Con el mouse se mira al rededor
- ´M´ - Bloquear/Desbloquear el Mouse
- ´F3´ - Activa el Debug
- ´F5´ - Activa o Desactiva el Wireframe

## Ejecución
Seguir estos pasos para ejecutar la aplicación:
1. Descargar el repo, ya sea como .zip o clonandolo a su computador
2. En la carpeta donde se encuentre el repositorio, crear un entorno virtual (venv) de python. Para eso se debe tener instalado python 3.14 (o alguna version anterior que aun podria ser compatible con el programa!). Luego, en una consola de comandos, y estando en la carpeta padre de la carpeta del repositorio, ejecutar "python -m venv [nombre carpeta]".
- Por ejemplo, si la carpeta del repositorio se llama ´craftmine´ y está ubicada en la carpeta ´Downloads´, entonces abriendo la terminal/consola de comandos y estando seleccionada la carpeta ´Downloads´, ejecuta "python -m venv craftmine". Esto actualizará la carpeta craftmine para que incluya lo necesario del entorno virtual de python en la misma.
3. Activar el entorno virtual:
- Para Linux y Mac: dentro de craftmine debe existir la carpeta ´bin´, y dentro hay un script generado por python llamado ´activate´. Para activar el venv debe ejecutarse en la consola ´source [ruta a bin/activate]´. Por ejemplo, si aun está en la carpeta ´Downloads´ del ejemplo anterior, deberia ejecutar ´source craftmine/bin/activate´. Luego, aparecera "(craftmine)" en el inicio de la linea de comandos.
- Para Windows: dentro de craftmine debe existir la carpeta ´Scripts´, y dentro habra un script generado por python llamado ´Activate.ps1´. Para activar el venv es necesario estar utilizando Power Shell, y tener permisos de ejecucion de scripts (pruebe ejecutando ´Set-ExecutionPolicy AllSigned -Scope CurrentUser´ para dar permisos de ejecución). Luego, "abrir" el script indicando la ruta hacia el mismo. Por ejemplo, si ya se encontraba en la carpeta ´Downloads´, debe ejecutar ´craftmine\Scripts\Activate.ps1´. Luego, aparecera "(craftmine)" en el inicio de la linea de comandos.
4. Ahora hay que instalar las librerias requeridas. Para eso ejecute ´pip install numpy==2.3.5 pyglet pyopengl trimesh scipy networkx pillow´
5. Ejecutar el archivo ´app.py´. Para esto, debe ejecutar en su consola ´python app.py´.
