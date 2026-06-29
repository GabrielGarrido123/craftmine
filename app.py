#Librerias externas
from pyglet.graphics.shader import Shader, ShaderProgram
from pyglet.window import Window, key
from pyglet.gl import *
from pyglet.app import run
from pyglet import math
from pyglet import clock
from pyglet import text

import numpy as np #recordar que en general usamos numpy 2.3.5
import trimesh as tm

#Librerias Oficiales de Python
import sys, os
import math as mathPY

#Codigos del curso CC3501
from utils.helpers import init_pipeline, mesh_from_file, init_axis
from utils.camera import FreeCamera
from utils.scene_graph import SceneGraph
from utils.drawables import Texture, Model, DirectionalLight, Material
from utils import shapes
from utils import colliders

DEFAULT_MATERIAL = Material(specular=[0.4,0.4,0.4])


BLOCKS_UV = {
    "air": [],
    "grass": [(27, 20), (27, 20), (27, 20), (27, 20), (28, 18), (23, 23)],
    "cobblestone": [(2,16),(2,16),(2,16),(2,16),(2,16),(2,16)]
}

class Controller(Window):
    #hereda caracteristicas de pyglet.window.Window
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args,**kwargs)

        self.time = 0

        self.wireframe = False
        self.mouseLocked = True
        self.debug = False

        self.skyColor = np.array([0.2,0.55,0.85])
        self.WORLD_SIZE = 2

class Player(FreeCamera):
    #clase del jugador. El jugador sera básicamente una camara, asi que\
    #hereda caracteristicas de utils.camera.FreeCamera
    def __init__(self, position=np.zeros(3), camera_type="perspective", direction=np.zeros(3), speed=4):
        super().__init__(position, camera_type)
        self.direction = direction
        self.speed = speed
        self.velocity = np.zeros(3)

        #gestiona cómo se mueve el jugador: "survival", "creative" y "spectator"
        self.gamemode = "survival"
        self.flystate = 0
        self.is_W_Pressed = False
        self.is_S_Pressed = False
        self.is_A_Pressed = False
        self.is_D_Pressed = False
        self.is_SPACE_Pressed = False
        
        #notar que p_pos es la posicion del jugador, es decir la bounding box.
        self.p_pos = np.array(position, dtype=float)
        self.collider = colliders.AABB("player", [-0.4, 0.0, -0.4], [0.4, 1.8, 0.4])
        self.collider.set_position(self.p_pos)

        #en cambio self.position es la posicion de la camara en si, y eye_height es la altura donde se ubica la misma en el jugador.
        self.eye_height = np.array([0.0, 1.7, 0.0])

        #atributos fisicos
        self.gravity = -18.0
        self.vertical_velocity = 0.0
        self.jump_strength = 7.0
        self.is_on_ground = False
        self.is_flying = False
    
    def player_update(self,dt):
        self.update() #metodo update() heredado de FreeCamera

        front_axis = 2
        side_axis = 0
        if self.gamemode == "spectator":
            front_axis = 0
            side_axis = 1
        
        #Actualizamos la direccion en base al input
        if (self.is_W_Pressed and self.is_S_Pressed) or not(self.is_W_Pressed or self.is_S_Pressed):
            self.direction[front_axis] = 0
        elif self.is_W_Pressed:
            self.direction[front_axis] = 1
        else:
            self.direction[front_axis] = -1
        
        if (self.is_A_Pressed and self.is_D_Pressed) or not(self.is_A_Pressed or self.is_D_Pressed):
            self.direction[side_axis] = 0
        elif self.is_A_Pressed:
            self.direction[side_axis] = 1
        else:
            self.direction[side_axis] = -1

        #calculos de direccion del jugador (y la camara)
        if self.gamemode == "spectator":
            #la camara puede moverse libremente

            dir = self.direction[0]*self.forward + self.direction[1]*self.right
            dir_norm = np.linalg.norm(dir)
            if dir_norm:
                dir /= dir_norm
            
            #Fisicas del jugador
            self.velocity += dir*self.speed
            self.position += self.velocity*dt

            self.collider.set_position(self.position)
            self.velocity = np.zeros(3)
            self.focus = self.position + self.forward
            return
        
        #Cuando NO se esta en modo espectador, la camara funciona de forma distinta:
        #- la camara solo se mueve en plano horizontal (x, z) por teclado.
        dir = self.direction[2] * self.forward + self.direction[0] * self.right
        dir[1] = 0.0 
        dir_norm = np.linalg.norm(dir)
        if dir_norm:
            dir /= dir_norm
        
        #aplicamos un salto si es que aplica
        if player.is_SPACE_Pressed and player.is_on_ground and not player.gamemode == "spectator":
            self.vertical_velocity = self.jump_strength

        #calculo de gravedad
        self.vertical_velocity += self.gravity * dt
        self.velocity[1] = self.vertical_velocity
        
        self.velocity[0] = dir[0] * self.speed
        self.velocity[2] = dir[2] * self.speed

        #aplicamos desplazamiento al bounding box del jugador
        self.p_pos += self.velocity * dt
        self.collider.set_position(self.p_pos)

        #se sincroniza la camara
        self.position = self.p_pos + self.eye_height

        #reseteo de atributos
        self.is_on_ground = False

        self.focus = self.position + self.forward
    
    def player_collisions(self, colliders_list):
        if self.gamemode == "spectator":
            return #el "modo espectador" hace que el jugador no colisione con nada
        
        for collider in colliders_list:
            if not collider.detect_collision(self.collider):
                #se ignoran los que no colisionan
                continue

            #distancias de penetracion
            d1 = collider.min - self.collider.max
            d2 = collider.max - self.collider.min

            #se elige la distancia mas corta por cada eje
            dist = d1 if np.linalg.norm(d1) < np.linalg.norm(d2) else d2

            #Buscamos eje de minima penetracion
            min_dist = abs(dist[0])
            axis = 0
            for i in range(3):
                if abs(dist[i]) < min_dist:
                    min_dist = abs(dist[i])
                    axis = i
            
            #se construye el vector de correccion de la posicion
            desplz = np.zeros(3)
            desplz[axis] = dist[axis]

            #corregimos posicion de bounding box
            self.p_pos += desplz
            self.collider.set_position(self.p_pos)

            #corregimos posicion de la camara
            self.position = self.p_pos + self.eye_height

            if axis == 1 and dist[1] > 0:
                self.vertical_velocity = 0.0
                self.is_on_ground = True
        
        #el foco debe actualizarse nuevamente en caso de haberse modificado la posicion de la misma en el for
        self.focus = self.position + self.forward

def get_atlas_uv(offsets, atlas, resolution=16):
    (xoff, yoff) = offsets
    dx = resolution / atlas.width
    dy = resolution / atlas.height
    return [
        dx*xoff         ,dy*yoff,
        dx*(xoff+1)     ,dy*yoff,
        dx*(xoff+1)     ,dy*(yoff+1),
        dx*xoff         ,dy*(yoff+1)
    ]

class Block:
    def __init__(self, id="air", chunk=None) -> None:
        self.id = id
        self.position = np.zeros(3)
        self.chunk = chunk
        self.adyacentBlocksIds = {
            "front": None,
            "back": None,
            "left": None,
            "right": None,
            "top": None,
            "bottom": None
        }
    
    def check_adyacent(self):
        x = int(self.position[0])
        y = int(self.position[1])
        z = int(self.position[2])

        if z < 15:
            self.adyacentBlocksIds["front"] = self.chunk.blocks[y][z+1][x].id
        else:
            self.adyacentBlocksIds["front"] = "air"
        if z > 0:
            self.adyacentBlocksIds["back"] = self.chunk.blocks[y][z-1][x].id
        else:
            self.adyacentBlocksIds["back"] = "air"
        if x > 0:
            self.adyacentBlocksIds["left"] = self.chunk.blocks[y][z][x-1].id
        else:
            self.adyacentBlocksIds["left"] = "air"
        if x < 15:
            self.adyacentBlocksIds["right"] = self.chunk.blocks[y][z][x+1].id
        else:
            self.adyacentBlocksIds["right"] = "air"
        if y < 15:
            self.adyacentBlocksIds["top"] = self.chunk.blocks[y+1][z][x].id
        else:
            self.adyacentBlocksIds["top"] = "air"
        if y > 0:
            self.adyacentBlocksIds["bottom"] = self.chunk.blocks[y-1][z][x].id
        else:
            self.adyacentBlocksIds["bottom"] = "air"

    def check_faces(self):
        self.check_adyacent()
        list = [i == "air" for i in self.adyacentBlocksIds.values()]
        return list

class Chunk(Model):
    #La idea de crear una clase chunk, al igual que en el aux 10, es crear meshes que agrupen varios bloques, para asi optimizar el renderizado.
    #Esto significa que los chunks deben heredar metodos de utils.drawables.Model
    #Codigo sacado de aux 10, con leves modificaciones

    #tamaño del chunk, por cada eje
    COUNT = 16
    SIZE = 16
    def __init__(self, id, atlas):
        super().__init__([],[],[],[]) #informacion que se le da a Model
        self.index_data = []
        self.blocks = np.full((Chunk.COUNT, Chunk.COUNT, Chunk.COUNT), None, dtype=object) #forma, dato con el que rellenar, tipo de dato

        for y in range(Chunk.COUNT):
            for z in range(Chunk.COUNT):
                for x in range(Chunk.COUNT):
                    self.blocks[y][z][x] = Block("air", self) #rellenamos la matriz de bloques con aire (bloque invisible)
        
        self.atlas = atlas
        self.id = id #tupla que contiene ubicacion en x y z respectivamente
    
    #la clase (Chunk) modifica la funcion init_gpu_data de Model
    def init_gpu_data(self, pipeline):
        delta = Chunk.SIZE / Chunk.COUNT
        vcount = 0

        #armado del mesh. Al modelo se le añaden los vertices de cada bloque del chunk (que si sea renderizado, o sea no aire)
        for y in range(Chunk.COUNT):
            for z in range(Chunk.COUNT):
                for x in range(Chunk.COUNT):
                    block = self.blocks[y][z][x]
                    block.position = np.array([x * delta, y * delta, z * delta])

                    if block.id == "air":
                        #se skippea el bloque de aire, o bloque vacio.
                        continue

                    #Version 2: Analisis por cara
                    visible = block.check_faces()
                    deltaV = 0
                    faces_drawn = 0
                    for i in range(6):
                        if not visible[i]:
                            continue
                        deltaV += 4
                        self.uv_data.extend(get_atlas_uv(BLOCKS_UV[block.id][i], self.atlas))

                        for j in range(i*12, (i+1)*12):
                            self.position_data.append(shapes.Cube["position"][j] + block.position[j%3])
                            self.normal_data.append(shapes.Cube["normal"][j])
                        
                        self.index_data.extend([vcount + shapes.Cube["indices"][j] for j in range(faces_drawn*6, (faces_drawn+1)*6)])
                        faces_drawn += 1
                    vcount += deltaV          
        
        #se ejecuta el resto de la funcion init_gpu_data() de Model
        super().init_gpu_data(pipeline)

#Global requerido
spatial_grid = {}

#Funcion responsable de revisar las colisiones del jugador
def check_collisions_old(player, man):
    px, _, pz = player.position

    center_x = int(np.floor(px))
    center_z = int(np.floor(pz))

    candidates = []
    
    #se consulta un vecindario cerrado de 3x3 bloques en el suelo horizontal y=0
    for dx in range(center_x - 1, center_x + 2):
        for dz in range(center_z - 1, center_z + 2):
            grid_key = (dx, 0, dz)
            if grid_key in spatial_grid:
                candidates.append(spatial_grid[grid_key])
    
    #Fase Narrow
    collisions = []
    for collider in candidates:
        if collider.detect_collision(player.collider):
            collisions.append(collider)
    
    if not collisions:
        return

    player.player_collisions(collisions)

def check_collisions(player, man):
    collisions = manager.check_collision("player")
    if not collisions:
        return

    player.player_collisions([manager[b] for b in collisions])

def generar_mundo():
    #GENERACION DE MUNDO
    size = controller.WORLD_SIZE
    #Esto genera una plataforma sencilla de bloques
    chunks=[]
    for z in range(size):
        for x in range(size):
            (posX,posZ) = (x-size//2,z-size//2)
            chunks.append(Chunk((posX,posZ),atlas))
    
    for c in chunks:
        for y in range(1):
            for z in range(Chunk.COUNT):
                for x in range(Chunk.COUNT):
                    c.blocks[y][z][x] = Block("grass", c)
                    manager.add_collider(colliders.AABB(f"{c.id[0]},{c.id[1]}|({x},{y},{z})", [0,0,0], [1,1,1]))
        
        #agregamos el chunk al grafo de escena
        name=f"chunk{c.id[0]},{c.id[1]}"
        world.add_node(
            name=name,
            mesh=c,
            pipeline=pipeline,
            material=DEFAULT_MATERIAL,
            texture=c.atlas,
            position=[c.id[0]*Chunk.SIZE,0,c.id[1]*Chunk.SIZE]
            )
    
    world.update()

    for c in chunks:
        c_pos = world.find_position(f"chunk{c.id[0]},{c.id[1]}")
        for y in range(Chunk.COUNT):
            for z in range(Chunk.COUNT):
                for x in range(Chunk.COUNT):
                    if c.blocks[y][z][x].id == "air":
                        continue #no hay que colisionar con el aire
                    
                    local_pos = c.blocks[y][z][x].position + np.array([-0.5,-0.5,-0.5])
                    global_pos = local_pos + c_pos

                    collider_name = f"{c.id[0]},{c.id[1]}|({x},{y},{z})"
                    manager.set_position(collider_name, global_pos)

                    #Registramos las coordenadas discretas globales en spatial_grid
                    gx = int(np.floor(global_pos[0]))
                    gz = int(np.floor(global_pos[2]))
                    spatial_grid[(gx,0,gz)] = manager[collider_name]

if __name__ == "__main__":
    #Crear la ventana
    controller = Controller(800,600, "CraftMine")
    controller.set_exclusive_mouse(controller.mouseLocked)

    #Contador de FPS para el Debug. Sacado de Aux10 del repo de auxiliares del curso
    fps_label = text.Label(
        text="FPS: 0.00",
        font_name="Arial",
        font_size=16,
        x=controller.width - 10,
        y=controller.height - 10,
        anchor_x="right",
        anchor_y="top",
        color=(255,255,255,255)
    )

    #Para mostrar la posicion en el espacio. Tambien es del Debug
    pos_label = text.Label(
        text="Position: 0.00, 0.00, 0.00",
        font_name="Arial",
        font_size=12,
        x=10,
        y=controller.height - 10,
        anchor_x="left",
        anchor_y="top",
        color=(255,255,255,255)
    )

    vel_label = text.Label(
        text="Velocity: 0.00, 0.00, 0.00",
        font_name="Arial",
        font_size=12,
        x=10,
        y=controller.height - 30,
        anchor_x="left",
        anchor_y="top",
        color=(255,255,255,255)
    )

    game_shaders = os.path.join(os.path.dirname(__file__), "game_shaders")
    pipeline = init_pipeline(game_shaders + "/blinn_phong.vert", game_shaders + "/blinn_phong.frag")

    assets_folder = os.path.join(os.path.dirname(__file__), "assets")
    atlas = Texture(assets_folder + "/atlas.png", minFilterMode=GL_NEAREST, maxFilterMode=GL_NEAREST)

    player = Player([0,20,0], speed=5)

    world = SceneGraph(player)

    #Inicializacion del manager de colisiones, y se registra la colision del jugador
    manager = colliders.CollisionManager()
    manager.add_collider(player.collider)

    generar_mundo()

    world.add_node("sun", light=DirectionalLight(ambient=[0.4,0.4,0.4]), pipeline=pipeline, rotation=[-np.pi/4, -np.pi/4, 0])

    @controller.event
    def on_draw():
        controller.clear()

        glClearColor(*controller.skyColor,1)
        glEnable(GL_DEPTH_TEST)

        if controller.wireframe:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        
        world.draw()
        glDisable(GL_DEPTH_TEST)

        #Renderizar UI
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        if controller.debug:
            fps_label.draw()
            pos_label.draw()
            #vel_label.draw()
    
    @controller.event
    def on_key_press(symbol, modifiers):
        if symbol == key.M:
            #Accion para poder recuperar el mouse y que no este anclado al programa (sin tener que cerrarlo o apretar la tecla Super para esto)
            controller.mouseLocked = not controller.mouseLocked
            controller.set_exclusive_mouse(controller.mouseLocked)
        
        if symbol == key.F3:
            #Activa/Desactiva el Debug
            controller.debug = not controller.debug

        if symbol == key.F5:
            #Activa/desactiva el Wireframe
            controller.wireframe = not controller.wireframe

        #Movimiento
        if symbol == key.W:
            player.is_W_Pressed = True
        if symbol == key.S:
            player.is_S_Pressed = True
        if symbol == key.A:
            player.is_A_Pressed = True
        if symbol == key.D:
            player.is_D_Pressed = True
        if symbol == key.SPACE:
            player.is_SPACE_Pressed = True

    @controller.event
    def on_key_release(symbol, modifiers):        
        if symbol == key.W:
            player.is_W_Pressed = False
        if symbol == key.S:
            player.is_S_Pressed = False
        if symbol == key.A:
            player.is_A_Pressed = False
        if symbol == key.D:
            player.is_D_Pressed = False
        if symbol == key.SPACE:
            player.is_SPACE_Pressed = False

    @controller.event
    def on_mouse_motion(x, y, dx, dy):
        player.yaw += dx * 0.001
        player.pitch += dy * 0.001
        player.pitch = math.clamp(player.pitch, -(np.pi / 2 - 0.01), np.pi / 2 - 0.01)

    def update(dt):
        world.update()
        player.player_update(dt)

        check_collisions(player, manager)

        controller.time += dt

        if controller.debug:
            fps = 1/dt if dt>0 else 0
            fps_label.text = f"FPS: {fps:.2f}"

            pos = player.p_pos
            pos_label.text = f"Position: {pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}"

            vel = player.velocity
            vel_label.text = f"Velocity: {vel[0]:.1f}, {vel[1]:.1f}, {vel[2]:.1f}"

    clock.schedule_interval(update, 1/600)
    run()