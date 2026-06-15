import asyncio
import grpc
from behave import given, when, then
from aiortc import RTCPeerConnection

import signaling_pb2
import signaling_pb2_grpc

SERVER_ADDRESS = "localhost:50051"

# ----------------------------------------------------
# GIVEN: Тепер це просто інформативний крок
# ----------------------------------------------------
@given("the server is running on localhost")
def step_server_running(context):
    # Нам більше не потрібно ініціалізувати канал тут global'но, 
    # щоб уникнути конфліктів асинхронних циклів.
    pass


# ----------------------------------------------------
# СЦЕНАРІЙ 1: Client requests video
# ----------------------------------------------------
async def run_send_offer(context):
    # Створюємо канал і стаб локально всередині цього ж loop
    async with grpc.aio.insecure_channel(SERVER_ADDRESS) as channel:
        stub = signaling_pb2_grpc.SignalingStub(channel)
        
        pc = RTCPeerConnection()
        pc.addTransceiver("video", direction="recvonly")
        
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        request = signaling_pb2.OfferMessage(
            sdp=pc.localDescription.sdp,
            type=pc.localDescription.type
        )
        
        context.response = await stub.SendOffer(request)
        await pc.close()

@when("the client sends an OfferMessage")
def step_client_sends_offer(context):
    asyncio.run(run_send_offer(context))

@then("the client should receive an AnswerMessage")
def step_client_receives_answer(context):
    assert context.response is not None, "No response from server"
    assert context.response.sdp != "", "SDP in AnswerMessage is empty"
    assert context.response.type == "answer", f"Expected type 'answer', got '{context.response.type}'"


# ----------------------------------------------------
# СЦЕНАРІЙ 2: Client sends a chat message
# ----------------------------------------------------
async def run_send_chat_message(context, message_text):
    async with grpc.aio.insecure_channel(SERVER_ADDRESS) as channel:
        stub = signaling_pb2_grpc.SignalingStub(channel)
        request = signaling_pb2.ChatMessage(
            sender="client_test",
            text=message_text
        )
        context.response = await stub.SendMessage(request)

@when('the client sends a ChatMessage "{message_text}"')
def step_client_sends_chat(context, message_text):
    asyncio.run(run_send_chat_message(context, message_text))

@then('the server should respond with an echo "{expected_echo}"')
def step_server_responds_echo(context, expected_echo):
    assert context.response is not None, "No response from server"
    assert context.response.success is True, "Server reported failure in ChatResponse"
    assert context.response.echo == expected_echo, f"Expected echo '{expected_echo}', got '{context.response.echo}'"


# ----------------------------------------------------
# СЦЕНАРІЙ 3: Client receives multiple chat messages
# ----------------------------------------------------
async def run_subscribe_stream(context):
    async with grpc.aio.insecure_channel(SERVER_ADDRESS) as channel:
        stub = signaling_pb2_grpc.SignalingStub(channel)
        request = signaling_pb2.ChatMessage(sender="client_test", text="Subscribe me")
        context.received_messages = []
        
        stream = stub.StreamMessages(request)
        async for message in stream:
            context.received_messages.append(message)

@when("the client subscribes to chat stream")
def step_client_subscribes_stream(context):
    asyncio.run(run_subscribe_stream(context))

@then("the client should receive {count:d} messages")
def step_client_receives_count_messages(context, count):
    actual_count = len(context.received_messages)
    assert actual_count == count, f"Expected {count} messages, but received {actual_count}"
    
    for msg in context.received_messages:
        assert msg.sender == "server", f"Expected sender 'server', got '{msg.sender}'"