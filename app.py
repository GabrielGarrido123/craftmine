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

DEFAULT_MATERIALS = {
    "basic": Material(specular=[0.4,0.4,0.4]),
    "metal": Material(shininess=64)
}

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
    def __init__(self, position=np.zeros(3), camera_type="perspective", direction=np.zeros(3), speed=2):
        super().__init__(position, camera_type)
        self.direction = direction
        self.speed = speed
        self.velocity = np.zeros(3)
        self.gamemode = "creative"
        self.flystate = 0

        self.collider = colliders.AABB("player", [-0.4, -0.4, -0.4], [0.4, 0.4, 0.4])
    
    def player_update(self,dt):
        self.update() #metodo update() heredado de FreeCamera
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
    
    def player_collisions(self, colliders_list):
        if self.gamemode == "spectator":
            return
        for collider in colliders_list:
            if not collider.detect_collision(self.collider):
                #se ignoran los que no colisionan
                continue

            #distancias de penetracion
            d1 = collider.min - self.collider.max
            d2 = collider.max - self.collider.min

            #se elige la distancia mas corta por cada eje
            dist = d1 if np.linalg.norm(d1) < np.linalg.norm(d2) else d2

            #Buscamos eje de minima penetracion para corregir solo esa componente
            min_dist = abs(dist[0])
            desplz = np.array([dist[0], 0.0, 0.0])

            for i in range(3):
                k=abs(dist[i])
                if k < min_dist:
                    desplz = np.zeros(3)
                    desplz[i] = dist[i]
            
            #evitamos que la posicion de la camara atraviese el bloque
            self.position += desplz

            #sincronizamos collider para el siguiente bloque de la lista
            self.collider.set_position(self.position)
        
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

def getWorldBlock(x,y,z):
    #retorna el puntero a un bloque cualquiera, independiente del chunk. None si no existe
    chunk_pos_x = int(x)%Chunk.COUNT
    chunk_pos_z = int(z)%Chunk.COUNT

#Funcion responsable de revisar las colisiones del jugador
def check_collisions(player, man):
    collisions = man.check_collision("player")
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
        for y in range(Chunk.COUNT):
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
            material=DEFAULT_MATERIALS["basic"],
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
                    
                    local_pos = c.blocks[y][z][x].position
                    #Ajustamos la posicion real del AABB sumando la transformacion del chunk correspondiente
                    manager.set_position(f"{c.id[0]},{c.id[1]}|({x},{y},{z})", local_pos + c_pos)

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
        font_size=16,
        x=10,
        y=controller.height - 10,
        anchor_x="left",
        anchor_y="top",
        color=(255,255,255,255)
    )

    vel_label = text.Label(
        text="Velocity: 0.00, 0.00, 0.00",
        font_name="Arial",
        font_size=16,
        x=10,
        y=controller.height - 20,
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

    world.add_node("sun", light=DirectionalLight(ambient=[0.2,0.2,0.2]), pipeline=pipeline, rotation=[-np.pi/4, -np.pi/4, 0])

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
            vel_label.draw()
    
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
        
        if symbol == key.W:
            player.direction[0] = 1
        if symbol == key.S:
            player.direction[0] = -1
        if symbol == key.A:
            player.direction[1] = 1
        if symbol == key.D:
            player.direction[1] = -1
        #if symbol == key.SPACE:
        #    player.velocity[1] = 10

    @controller.event
    def on_key_release(symbol, modifiers):
        if symbol == key.W or symbol == key.S:
            player.direction[0] = 0
        if symbol == key.A or symbol == key.D:
            player.direction[1] = 0
        #if symbol == key.SPACE:
        #    player.velocity[1] = 0

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

            pos = player.position
            pos_label.text = f"Position: {pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}"

            vel = player.velocity
            vel_label.text = f"Velocity: {vel[0]:.1f}, {vel[1]:.1f}, {vel[2]:.1f}"

    clock.schedule_interval(update, 1/600)
    run()