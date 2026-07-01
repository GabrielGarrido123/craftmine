#version 330
in vec2 fragTexCoord;
in vec4 colorAdd;

flat in int isSun;
uniform float daytime;

uniform sampler2D u_texture;

out vec4 outColor;

void main() {
    // lo que se le suma al color hace que el sol se haga mas blanco mientras se aleja del horizonte (asi funciona en el juego original)
    // tambien hace que de noche el sol se oscurezca por completo

    outColor = texture(u_texture, fragTexCoord) + colorAdd;
        
}