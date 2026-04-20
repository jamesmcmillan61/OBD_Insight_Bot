using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace OBDInsightBot.Models
{
    public class UserOBDData
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.None)]
        public Guid Id { get; private set; } = Guid.NewGuid();

        // Foreign key to the user session
        [Required]
        public Guid UserSessionId { get;  set; }

        [ForeignKey(nameof(UserSessionId))]
        public UserSession UserSession { get; set; }

        public DateTime UploadedAt { get; set; }


        public string? Mark { get; set; }
        public string? Model { get; set; }
        public string? CarYear { get; set; }
        public string? EnginePower { get; set; }
        public string? Automatic { get; set; }
        public string? VehicleId { get; set; }

        // Sensor data
        public string? BarometricPressureKpa { get; set; }
        public string? EngineCoolantTemp { get; set; }
        public string? FuelLevel { get; set; }
        public string? EngineLoad { get; set; }
        public string? AmbientAirTemp { get; set; }
        public string? EngineRpm { get; set; }
        public string? IntakeManifoldPressure { get; set; }
        public string? Maf { get; set; }

        public string? LongTermFuelTrimBank2 { get; set; }
        public string? ShortTermFuelTrimBank1 { get; set; }
        public string? ShortTermFuelTrimBank2 { get; set; }

        public string? FuelType { get; set; }
        public string? AirIntakeTemp { get; set; }
        public string? FuelPressure { get; set; }
        public string? Speed { get; set; }
        public string? EngineRuntime { get; set; }
        public string? ThrottlePos { get; set; }

        // Diagnostics
        public string? DtcNumber { get; set; }
        public string? TroubleCodes { get; set; }
        public string? TimingAdvance { get; set; }
        public string? EquivRatio { get; set; }

        // Time breakdown
        public string? Min { get; set; }
        public string? Hours { get; set; }
        public string? DaysOfWeek { get; set; }
        public string? Months { get; set; }
        public string? Year { get; set; }
    }
}
