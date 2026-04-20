using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace OBDInsightBot.Models
{
    public class SingleUse
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.None)]
        public Guid Id { get; private set; } = Guid.NewGuid();


        public DateTime startTime { get; set; } = DateTime.Now;

        public bool UploadFileSucsessfully { get; set; } = false;
        public int UserChatCount { get; set; } = 0;

        public int PreBuiltQuestions { get; set; } = 0;

        public int ResponceErrors { get; set; } = 0; 

        public bool ManualDataEntry { get; set; } = false;

        public string ListOfTopics { get; set; } = string.Empty;

        // Foreign key to the user session -- for when still being used
        public Guid? UserSessionId { get; set; }

        [ForeignKey(nameof(UserSessionId))]
        public UserSession? UserSession { get; set; }
    }
}
