%% =========================================================================
% PROYECTO DE GRADUACIÓN: HERRAMIENTAS DE SOFTWARE PARA CRAZYFLIE
% Pablo Javier Caal Leiva - 20538
% -------------------------------------------------------------------------
% Verificación de callbacks para fusión de sensores
% =========================================================================

%% Añadir al path las carpetas de comandos usando una ruta relativa
addpath('../Crazyflie-Matlab-Commands');
addpath('../Robotat-Matlab-Commands');

%% Evento específico (Event callback)
%% Conexión con Robotat y Crazyflie
robotat = robotat_connect();
crazyflie_1 = 1; % crazyflie_connect(8);
agent_id = 50;

%% Configurar listener y evento
addlistener(robotat, 'update_crazyflie_position', @(src, event) robotat_update_crazyflie_position(src, event, robotat, crazyflie_1, agent_id));

eventData = struct('Data', []);  % Los datos se obtendrán dentro del callback
notify(robotat, 'update_crazyflie_position', eventData);

%% Uso de event callback con disparador
configureCallback(robotat, "byte", 1, @(src, event) robotat_update_crazyflie_position(crazyflie_1, src, agent_id));
pose = robotat_get_pose(robotat, agent_id)

%% Comando de inicialización vacío
configureCallback(robotat, "byte", 1, @(src, event) crazyflie_robotat_position_callback(crazyflie_1, src, agent_id));
s.dst = 1; % DST_ROBOTAT
s.cmd = 1; % CMD_GET_POSE
s.pld = []; 
write(robotat, uint8(jsonencode(s))); 

%% Desactivar callback
configureCallback(robotat, "off");

%% Lecturas durante delay
Duration = 5; % Duración en segundos
Period = 4; % Lecturas por segundo
N = Duration*Period; % Cantidad de lecturas

Pose_Crazyflie = zeros(N, 6); % Array para lecturas de pose de marker

% Ciclo para realizar lecturas de pose del marker
for i = 1:N
    try 
        Pose_Crazyflie(i,:) = crazyflie_get_pose(crazyflie_1);
    catch ME
        disp('Error al obtener posición.');
        disp(ME.message);
    end 
    pause(1/Period); % Delay de freuencia de muestreo
end

configureCallback(robotat, "off");

robotat_disconnect(robotat);
crazyflie_disconnect(crazyflie_1);

%% Gráfica 3D de lecturas
x_Robotat = Pose_Crazyflie(:, 1);
y_Robotat = Pose_Crazyflie(:, 2);
z_Robotat = Pose_Crazyflie(:, 3);

figure;
plot3(x_Robotat, y_Robotat, z_Robotat, '-*');
grid on;
xlabel('X [m]');
ylabel('Y [m]');
zlabel('Z [m]');
title('Trayectoria del marker en 3D');

% Ajustar los límites de los ejes
% xlim([-2 2]);
% ylim([-2.5 2.5]);
% zlim([0 3]);

% Ajustar el espacio 3D
axis equal;
axis([-2 2 -2.5 2.5 0 3]);
view(3); 

%% Configurar callback para enviar la posición absoluta al dron usando Robotat
configureCallback(robotat, "byte", 1, @(src, event) crazyflie_robotat_position_callback(crazyflie_1, src, agent_id));
pause(15)
configureCallback(robotat, "off");

%% Posición Robotat, actualización y lectura
pose = robotat_get_pose(robotat, agent_id)
crazyflie_update_position(crazyflie_1, pose(1), pose(2), pose(3));
pose = crazyflie_get_pose(crazyflie_1)
