# smart-office
A university project for IoT course
This system is used for managing offices
We have 3 parts:
- End Node (an iot device such as arduino, rasbery pi, ...): that is located in each room
- Local Server: This part should be an HTTP server, CoAP sever and an MQTT client for communication with endnode, admins and users
- Centeral Server: An HTTP server, managing all of offices and their room, saving data that communicate with local server


## Features
- MQTT Client/Broker (local server)
- CoAP Client/Server (local server)
- HTTP Server (local and centeral servers)
- LiteSQL Database (local and centeral servers)
