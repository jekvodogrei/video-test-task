import asyncio
import logging

import grpc
import signaling_pb2
import signaling_pb2_grpc
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder

logging.basicConfig(level=logging.INFO, format="[CLIENT] %(message)s")


async def run():
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = signaling_pb2_grpc.SignalingStub(channel)

        pc = RTCPeerConnection()

        pc.addTransceiver("video", direction="recvonly")

        recorder = MediaRecorder("received.mp4")

        @pc.on("track")
        async def on_track(track):
            logging.info(f"Received track: {track.kind}")
            recorder.addTrack(track)
            await recorder.start()

            @track.on("ended")
            async def on_ended():
                await recorder.stop()

        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        grpc_offer = signaling_pb2.OfferMessage(
            sdp=pc.localDescription.sdp,
            type=pc.localDescription.type,
        )

        answer = await stub.SendOffer(grpc_offer)
        await pc.setRemoteDescription(
            RTCSessionDescription(sdp=answer.sdp, type=answer.type),
        )

        logging.info("Connection established, wait for video...")


        await asyncio.sleep(10)
        await recorder.stop()


        logging.info("Send message to chat")
        response = await stub.SendMessage(signaling_pb2.ChatMessage(sender="client", text="Hi looser!"))
        logging.info(f"Server answer: {response.echo}")


        logging.info("Subscribe to server messages")
        async for message in stub.StreamMessages(signaling_pb2.ChatMessage(sender="client", text="subscribe")):
            logging.info(f"Server answer: {message.text}")


if __name__ == "__main__":
    asyncio.run(run())
