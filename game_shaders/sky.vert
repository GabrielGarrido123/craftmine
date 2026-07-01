#version 330

in vec3 position;
in vec2 texCoord;

in int isSun;
uniform float daytime;

out vec2 fragTexCoord;
out vec4 colorAdd;

uniform mat4 u_model = mat4(1.0);
uniform mat4 u_view = mat4(1.0);
uniform mat4 u_projection = mat4(1.0);

void main() {
    fragTexCoord = texCoord;
    gl_Position = u_projection * u_view * u_model * vec4(position, 1.0f);

    if (isSun == 1.0){
        colorAdd = vec4(1,1,1,0) * clamp(1.25 * sin(daytime * 3.1415), -0.5, 1.0);
    } else {
        //esto hace que la luna sea levemente transparente mientras sale del horizonte
        colorAdd = - vec4(0,0,0,1) * clamp(sin(clamp(daytime,1,2) * 3.1415 * 2 + 3.1415/2), 0.0, 1.0) * 0.5;
    }
    
}