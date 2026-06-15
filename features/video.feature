Feature: Video server interaction
  In order to test gRPC server behaviour
  As a QA engineer
  I want to verify both video delivery and chat messages

  Scenario: Client requests video
    Given the server is running on localhost
    When the client sends an OfferMessage
    Then the client should receive an AnswerMessage

  Scenario: Client sends a chat message
    Given the server is running on localhost
    When the client sends a ChatMessage "Hello"
    Then the server should respond with an echo "Hello"

  Scenario: Client receives multiple chat messages
    Given the server is running on localhost
    When the client subscribes to chat stream
    Then the client should receive 3 messages
