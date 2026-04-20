using System.Net.Http.Json;
using OBDInsightBot.Models;

namespace OBDInsightBot.Services
{
    public class ChatbotApiService
    {
        private readonly HttpClient _httpClient;
        private readonly ILogger<ChatbotApiService> _logger;

        public ChatbotApiService(HttpClient httpClient, ILogger<ChatbotApiService> logger)
        {
            _httpClient = httpClient;
            _logger = logger;
        }

        public async Task<string> GetBotResponseAsync(string message, string sessionId, object? vehicleData)
        {
            try
            {
                // First, try to create/update session with vehicle data if available
                if (vehicleData != null)
                {
                    try
                    {
                        // Create session with the C# session ID so Python can link them
                        var sessionRequest = new
                        {
                            session_id = sessionId,
                            vehicle_data = vehicleData
                        };
                        var createResponse = await _httpClient.PostAsJsonAsync("/session/create", sessionRequest);
                        if (createResponse.IsSuccessStatusCode)
                        {
                            _logger.LogInformation("Session created/updated for {SessionId}", sessionId);
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogWarning(ex, "Could not create/update session, continuing with chat");
                    }
                }

                // Send chat message
                var chatRequest = new
                {
                    message = message,
                    session_id = sessionId
                };

                var response = await _httpClient.PostAsJsonAsync("/chat", chatRequest);

                if (response.IsSuccessStatusCode)
                {
                    var result = await response.Content.ReadFromJsonAsync<ChatApiResponse>();
                    if (result != null && !string.IsNullOrEmpty(result.Response))
                    {
                        _logger.LogInformation("Bot response received: intent={Intent}, time={Time}ms",
                            result.IntentDetected, result.ProcessingTimeMs);
                        return result.Response;
                    }
                }

                _logger.LogWarning("API returned unsuccessful response: {Status}", response.StatusCode);
                return "Sorry, I couldn't process that request. Please try again.";
            }
            catch (TaskCanceledException)
            {
                _logger.LogWarning("Request to chatbot API timed out");
                return "Sorry, the request took too long. Please try again.";
            }
            catch (HttpRequestException ex)
            {
                _logger.LogError(ex, "Failed to connect to chatbot API");
                return "Sorry, I'm having trouble connecting to the chatbot service. Please try again later.";
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error calling chatbot API");
                return "Sorry, something went wrong. Please try again.";
            }
        }
    }
}
