using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace OBDInsightBot.Models
{

    public class BlogPost
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.None)]
        public Guid Id { get; internal set; } = Guid.NewGuid();



        [Required]
        public DateTimeOffset WrittenAt { get; set; } = DateTimeOffset.UtcNow;

        [Required]
        [MaxLength(200)]
        public string Title { get; set; } = string.Empty;

        [Required]
        [MaxLength(500)]
        public string MiniDescription { get; set; } = string.Empty;

        [Required]
        public string Content { get; set; } = string.Empty;

        [Required]
        public DateTimeOffset PostedAt { get; set; } = DateTimeOffset.UtcNow;

        [Required]
        public bool IsHidden { get; set; } = false;

        public string? PathForFeaturedImage { get; set; }
    }
}