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

class Controller(Window):
    #hereda caracteristicas de pyglet.window.Window
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args,**kwargs)

        self.time = 0

        self.wireframe = False
        self.mouseLocked = True
        self.debug = False

        self.skyColor = np.array([0.2,0.55,0.85])
        self.WORLD_SIZE = 8

class Player(FreeCamera):
    #clase del jugador. El jugador sera básicamente una camara, asi que\
    #hereda caracteristicas de utils.camera.FreeCamera
    def __init__(self, position=np.zeros(3), camera_type="perspective", direction=np.zeros(3), speed=2):
        super().__init__(position, camera_type)
        self.direction = direction
        self.speed = speed
        self.velocity = np.zeros(3)
        self.gamemode = "spectator"
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

DEFAULT_MATERIALS = {
    "basic": Material(specular=[0.4,0.4,0.4]),
    "metal": Material(shininess=64)
}

BLOCKS_UV = {
    "air": [],
    "grass": [(27, 20), (27, 20), (27, 20), (27, 20), (28, 18), (23, 23)],
    "cobblestone": [(2,16),(2,16),(2,16),(2,16),(2,16),(2,16)]
}

class Block:
    def __init__(self, id="air") -> None:
        self.id = id
        self.position = np.zeros(3)

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
                    self.blocks[y][z][x] = Block("air") #rellenamos la matriz de bloques con aire (bloque invisible)
        
        self.atlas = atlas
        self.id = id
    
    #la clase (Chunk) modifica la funcion init_gpu_data de Model
    def init_gpu_data(self, pipeline):
        delta = Chunk.SIZE / Chunk.COUNT
        cube_pos = [(coord + 0.5)*delta for coord in shapes.Cube["position"]]
        cube_pos = np.reshape(cube_pos, (len(cube_pos) // 3, 3))
        deltaV = cube_pos.shape[0]
        vcount = 0

        #armado del mesh. Al modelo se le añaden los vertices de cada bloque del chunk (que si sea renderizado)
        for y in range(Chunk.COUNT):
            for z in range(Chunk.COUNT):
                for x in range(Chunk.COUNT):
                    block = self.blocks[y][z][x]
                    block.position = np.array([x * delta, y * delta, z * delta])

                    if block.id == "air":
                        #se skippea el bloque de aire, o bloque vacio.
                        continue
                    
                    for p in cube_pos:
                        self.position_data.extend(p + block.position)
                    
                    for uv in BLOCKS_UV[block.id]:
                        self.uv_data.extend(get_atlas_uv(uv, self.atlas))
                    
                    self.normal_data.extend(shapes.Cube["normal"])
                    self.index_data.extend([vcount + i for i in shapes.Cube["indices"]])
                    vcount += deltaV
        
        #se ejecuta el resto de la funcion init_gpu_data() de Model
        super().init_gpu_data(pipeline)

#Funcion responsable de revisar las colisiones del jugador
def check_collisions(player, man):
    collisions = man.check_collision("player")
    if not collisions:
        return
    
    player.player_collisions([manager[b] for b in collisions])


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
        text="XYZ: 0.00, 0.00, 0.00",
        font_name="Arial",
        font_size=16,
        x=10,
        y=controller.height - 10,
        anchor_x="left",
        anchor_y="top",
        color=(255,255,255,255)
    )

    game_shaders = os.path.join(os.path.dirname(__file__), "game_shaders")
    pipeline = init_pipeline(game_shaders + "/blinn_phong.vert", game_shaders + "/blinn_phong.frag")

    assets_folder = os.path.join(os.path.dirname(__file__), "assets")
    atlas = Texture(assets_folder + "/atlas.png", minFilterMode=GL_NEAREST, maxFilterMode=GL_NEAREST)

    player = Player([0,5,0])

    world = SceneGraph(player)

    #Inicializacion del manager de colisiones, y se registra la colision del jugador
    manager = colliders.CollisionManager()
    manager.add_collider(player.collider)

    #GENERACION DE MUNDO
    size = controller.WORLD_SIZE
    #Esto genera una plataforma sencilla de bloques
    chunks=[]
    for z in range(size):
        for x in range(size):
            (posX,posZ) = (x-size//2,z-size//2)
            chunks.append(Chunk((posX,posZ),atlas))
    
    for c in chunks:
        for z in range(Chunk.COUNT):
            for x in range(Chunk.COUNT):
                c.blocks[0][z][x] = Block("grass")
                manager.add_collider(colliders.AABB(f"{c.id[0]},{c.id[1]}|({x},0,{z})", [0,0,0], [1,1,1]))
        
        c.blocks[1][0][0] = Block("cobblestone")
        manager.add_collider(colliders.AABB(f"{c.id[0]},{c.id[1]}|(0,1,0)", [0,0,0], [1,1,1]))
        
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
            pos_label.text = f"XYZ: {pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}"

    clock.schedule_interval(update, 1/600)
    run()