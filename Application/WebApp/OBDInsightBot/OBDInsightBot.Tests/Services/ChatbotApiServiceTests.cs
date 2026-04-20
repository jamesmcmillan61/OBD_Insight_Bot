using System.Net;
using System.Text.Json;
using FluentAssertions;
using Microsoft.Extensions.Logging;
using Moq;
using OBDInsightBot.Models;
using OBDInsightBot.Services;
using OBDInsightBot.Tests.Helpers;

namespace OBDInsightBot.Tests.Services;

public class ChatbotApiServiceTests
{
    private readonly Mock<ILogger<ChatbotApiService>> _mockLogger = new();

    private ChatbotApiService CreateService(HttpMessageHandler handler)
    {
        var client = new HttpClient(handler)
        {
            BaseAddress = new Uri("http://localhost:8000")
        };
        return new ChatbotApiService(client, _mockLogger.Object);
    }

    private static string SerializeResponse(string response, string? intent = null)
    {
        return JsonSerializer.Serialize(new
        {
            response = response,
            session_id = "test-session",
            timestamp = "2024-01-01T00:00:00Z",
            intent_detected = intent,
            processing_time_ms = 50.0
        });
    }

    [Fact]
    public async Task GetBotResponseAsync_SuccessfulResponse_ReturnsResponseText()
    {
        var handler = new MockHttpMessageHandler(
            HttpStatusCode.OK,
            SerializeResponse("Your engine is running fine!", "engine_status"));
        var service = CreateService(handler);

        var result = await service.GetBotResponseAsync("how is my engine", "session-1", null);

        result.Should().Be("Your engine is running fine!");
    }

    [Fact]
    public async Task GetBotResponseAsync_WithVehicleData_CallsSessionCreateFirst()
    {
        var handler = new MockHttpMessageHandler((request, _) =>
        {
            var response = new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(
                    SerializeResponse("Hello!"),
                    System.Text.Encoding.UTF8,
                    "application/json")
            };
            return Task.FromResult(response);
        });
        var service = CreateService(handler);

        var vehicleData = new { mark = "Toyota", model = "Corolla" };
        await service.GetBotResponseAsync("hello", "session-1", vehicleData);

        // Should have made 2 requests: session/create and chat
        handler.SentRequests.Should().HaveCount(2);
        handler.SentRequests[0].RequestUri!.PathAndQuery.Should().Be("/session/create");
        handler.SentRequests[1].RequestUri!.PathAndQuery.Should().Be("/chat");
    }

    [Fact]
    public async Task GetBotResponseAsync_NullVehicleData_SkipsSessionCreate()
    {
        var handler = new MockHttpMessageHandler(
            HttpStatusCode.OK,
            SerializeResponse("Hello!"));
        var service = CreateService(handler);

        await service.GetBotResponseAsync("hello", "session-1", null);

        handler.SentRequests.Should().HaveCount(1);
        handler.SentRequests[0].RequestUri!.PathAndQuery.Should().Be("/chat");
    }

    [Fact]
    public async Task GetBotResponseAsync_SessionCreateFails_StillReturnsChatResponse()
    {
        int requestCount = 0;
        var handler = new MockHttpMessageHandler((request, _) =>
        {
            requestCount++;
            if (request.RequestUri!.PathAndQuery == "/session/create")
            {
                return Task.FromResult(new HttpResponseMessage(HttpStatusCode.InternalServerError));
            }
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(
                    SerializeResponse("Chat works!"),
                    System.Text.Encoding.UTF8,
                    "application/json")
            });
        });
        var service = CreateService(handler);

        var result = await service.GetBotResponseAsync("hello", "session-1", new { mark = "Toyota" });

        result.Should().Be("Chat works!");
    }

    [Fact]
    public async Task GetBotResponseAsync_ChatReturnsBadStatus_ReturnsGenericError()
    {
        var handler = new MockHttpMessageHandler(
            HttpStatusCode.InternalServerError,
            "Internal Server Error");
        var service = CreateService(handler);

        var result = await service.GetBotResponseAsync("hello", "session-1", null);

        result.Should().Be("Sorry, I couldn't process that request. Please try again.");
    }

    [Fact]
    public async Task GetBotResponseAsync_Timeout_ReturnsTimeoutMessage()
    {
        var handler = new MockHttpMessageHandler((_, _) =>
        {
            throw new TaskCanceledException("Request timed out");
        });
        var service = CreateService(handler);

        var result = await service.GetBotResponseAsync("hello", "session-1", null);

        result.Should().Be("Sorry, the request took too long. Please try again.");
    }

    [Fact]
    public async Task GetBotResponseAsync_ConnectionFailure_ReturnsConnectionError()
    {
        var handler = new MockHttpMessageHandler((_, _) =>
        {
            throw new HttpRequestException("Connection refused");
        });
        var service = CreateService(handler);

        var result = await service.GetBotResponseAsync("hello", "session-1", null);

        result.Should().Be("Sorry, I'm having trouble connecting to the chatbot service. Please try again later.");
    }

    [Fact]
    public async Task GetBotResponseAsync_UnexpectedException_ReturnsSomethingWentWrong()
    {
        var handler = new MockHttpMessageHandler((_, _) =>
        {
            throw new InvalidOperationException("Unexpected error");
        });
        var service = CreateService(handler);

        var result = await service.GetBotResponseAsync("hello", "session-1", null);

        result.Should().Be("Sorry, something went wrong. Please try again.");
    }

    [Fact]
    public async Task GetBotResponseAsync_EmptyResponseBody_ReturnsGenericError()
    {
        var handler = new MockHttpMessageHandler(
            HttpStatusCode.OK,
            JsonSerializer.Serialize(new
            {
                response = "",
                session_id = "s1",
                timestamp = "now",
                processing_time_ms = 0.0
            }));
        var service = CreateService(handler);

        var result = await service.GetBotResponseAsync("hello", "session-1", null);

        result.Should().Be("Sorry, I couldn't process that request. Please try again.");
    }
}
