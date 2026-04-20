using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace OBDInsightBot.Models
{
    public class UserSession
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public Guid Id { get; private set; } = Guid.NewGuid();

        public DateTime SessionStartTime { get; set; }

        public DateTime lastUseTime { get; set; }

        public string? UploadedDataPath { get; set; }


    }
}
