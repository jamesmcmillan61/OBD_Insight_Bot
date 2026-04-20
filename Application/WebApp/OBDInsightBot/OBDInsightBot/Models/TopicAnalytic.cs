using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace OBDInsightBot.Models
{
    public class TopicAnalytic
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.None)]
        public Guid Id { get; private set; } = Guid.NewGuid();

        [Required]
        public DateOnly Date { get; set; }

        [Required]
        public TopicType TopicName { get; set; }

        [Required]
        public int TopicCount { get; set; } = 0;

        public enum TopicType
        {
            Fuel,
            Temperature,
            Rpm,
            Speed,
            Engine,
            FuelLevel,
            EngineCoolantTemp,
            EngineRpm,
            TroubleCodes
        }
    }
}
