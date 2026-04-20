using System.Text.Json.Serialization;

namespace OBDInsightBot.Models
{
    public class ChatApiResponse
    {
        [JsonPropertyName("response")]
        public string Response { get; set; } = string.Empty;

        [JsonPropertyName("session_id")]
        public string SessionId { get; set; } = string.Empty;

        [JsonPropertyName("timestamp")]
        public string Timestamp { get; set; } = string.Empty;

        [JsonPropertyName("intent_detected")]
        public string? IntentDetected { get; set; }

        [JsonPropertyName("processing_time_ms")]
        public double ProcessingTimeMs { get; set; }
    }
}
