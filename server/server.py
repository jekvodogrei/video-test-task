import asyncio
import logging
import os
import tempfile

import grpc
import signaling_pb2
import signaling_pb2_grpc
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaRelay
from Crypto.Cipher import AES

logging.basicConfig(level=logging.INFO, format="[SERVER] %(message)s")


GRPC_HOST = "0.0.0.0"
GRPC_PORT = 50051
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_FILE = os.path.join(BASE_DIR, "sample.mp4.enc")
VIDEO_KEY = "2b45754d4ada09a1e5aed0733fdceec4e3e9f277061da55fe4197cc2eb009cb1"


def decrypt_video(path, key: str):
    if not os.path.exists(path):
        raise FileNotFoundError(logging.error(f"No encrypted VideoTrack {VIDEO_FILE}!"))


    with open(path, "rb") as f_in:
        key_hex = bytes.fromhex(key)
        nonce = f_in.read(8)
        cipher = AES.new(key_hex, AES.MODE_CTR, nonce=nonce)

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
        with os.fdopen(tmp_fd, "wb") as f_out:
            while chunk := f_in.read(4096):
                f_out.write(cipher.decrypt(chunk))

    logging.info(f"Video decrypted to {tmp_path}")
    return tmp_path


class SignalingServicer(signaling_pb2_grpc.SignalingServicer):
    def __init__(self):
        logging.info("Initializing...")
        self.relay = MediaRelay()
        self.decrypted_file = decrypt_video(VIDEO_FILE, VIDEO_KEY)
        self.player = MediaPlayer(self.decrypted_file)

        if not self.player.video:
            raise RuntimeError(logging.error("No VideoTrack found!"))

        logging.info(f"Video is ready: {self.player.video}")

    async def SendOffer(self, request, context):
        logging.info("Received OfferMessage from client")
        offer = RTCSessionDescription(sdp=request.sdp, type=request.type)

        pc = RTCPeerConnection()
        logging.info("Established RTCPeerConnection")

        try:
            await pc.setRemoteDescription(offer)
            logging.info("Remote description established")
        except Exception as e:
            logging.error(f"Failed to set remote description: {e}")
            raise

        try:
            video_track = self.relay.subscribe(self.player.video)
            pc.addTrack(video_track)
            logging.info(f"Video track added to PeerConnection ({video_track.kind})")
        except Exception as e:
            logging.error(f"Failed to add video track: {e}")
            raise

        try:
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            logging.info("Local description established (Answer created)")
        except Exception as e:
            logging.error(f"Failed to create/set local description: {e}")
            raise

        logging.info(f"Returning AnswerMessage: type={pc.localDescription.type}, sdp_len={len(pc.localDescription.sdp)}")

        return signaling_pb2.AnswerMessage(
            sdp=pc.localDescription.sdp,
            type=pc.localDescription.type,
        )

    async def SendMessage(self, request, context):
        logging.info(f"Message from - {request.sender}: {request.text}")
        return signaling_pb2.ChatResponse(success=True, echo=request.text)

    async def StreamMessages(self, request, context):
        logging.info(f"{request.sender}v- new subscriber")
        messages = ["Hi from server", "What's up", "Please watch video from stream"]
        for msg in messages:
            await asyncio.sleep(1)
            yield signaling_pb2.ChatMessage(sender="server", text=msg)


async def serve():
    server = grpc.aio.server()
    signaling_pb2_grpc.add_SignalingServicer_to_server(SignalingServicer(), server)
    server.add_insecure_port(f"{GRPC_HOST}:{GRPC_PORT}")
    logging.info(f"RUN gRPC server port {GRPC_PORT}...")
    await server.start()
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())
