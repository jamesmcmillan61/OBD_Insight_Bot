using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace OBDInsightBot.Models
{
    public class UserChatItem
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.None)]
        public Guid Id { get; private set; } = Guid.NewGuid();

        // Foreign key to the user session
        [Required]
        public Guid UserSessionId { get; private set; }

        [ForeignKey(nameof(UserSessionId))]
        public UserSession UserSession { get; private set; }

        // Who sent the message
        [Required]
        public ChatSender ItemBy { get; private set; }

        [Range(0, int.MaxValue)]
        public int ChatPosition { get; private set; }

        [Required]
        public DateTime SentAtUtc { get; private set; } = DateTime.UtcNow;

        [Required]
        [MaxLength(4000)]
        public string ChatContent { get; private set; }


        // Required by EF
        private UserChatItem() { }

        public UserChatItem(
            Guid userSessionId,
            ChatSender itemBy,
            string chatContent,
            int chatPosition)
        {
            UserSessionId = userSessionId;
            ItemBy = itemBy;
            ChatContent = chatContent ?? throw new ArgumentNullException(nameof(chatContent));
            ChatPosition = chatPosition;
        }
    }

    public enum ChatSender
    {
        User = 1,
        Bot = 2,
        System = 3
    }
}
