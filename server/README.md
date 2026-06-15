# gRPC WebRTC Video Server

This project implements a gRPC server that streams an encrypted video to clients using WebRTC and supports simple chat functionality.

---

## Features

- Decrypts a locally stored encrypted video (`sample.mp4.enc`) using AES-CTR.
- Streams video to clients via WebRTC (`aiortc`).
- Supports receiving offers from clients and sending WebRTC answers.
- Provides simple chat functionality:
  - `SendMessage` – echo text messages from clients.
  - `StreamMessages` – stream server-generated messages to clients.

---


## How It Works
### 1. Video Decryption
The decrypt_video(path, key) function:
Opens the encrypted video file.
Reads the first 8 bytes as a nonce.
Uses AES-CTR to decrypt the content.
Writes the decrypted video to a temporary .mp4 file.
Returns the path to the decrypted video.

### 2. gRPC Service (SignalingServicer)
- Initialization:
  - Decrypts the video.
  - Creates a MediaPlayer for the video track.
  - Sets up a MediaRelay to allow streaming to multiple clients.
- Server Methods:
  - SendOffer 
  - Receives an OfferMessage from a client (WebRTC SDP). 
  - Creates an RTCPeerConnection. 
  - Sets the remote description (client SDP). 
  - Adds the video track to the connection. 
  - Creates an answer and returns it to the client. 
  - SendMessage 
  - Receives a text message from a client. 
  - Logs the message and returns an echo confirmation. 
  - StreamMessages 
  - Streams server-generated messages to clients. 
  - Demonstration messages sent with a delay.

### 3. Server Startup
Async gRPC server (grpc.aio.server()).
Registers the SignalingService listens on port 50051.
Runs until terminated


## Build

### Use Dockerfile builds a container that:
- Installs Python 3.11 and ffmpeg. 
- Installs required Python packages. 
- Copies server and protobuf and encode video files. 
- Compiles gRPC code from .proto. 
- Launches the gRPC WebRTC video server.