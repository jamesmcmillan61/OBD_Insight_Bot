using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace OBDInsightBot.Models
{

    public class BlogItem
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.None)]
        public Guid Id { get; private set; } = Guid.NewGuid();

        [Required] // FK to blog post
        public Guid BlogPostId { get; set; }

        [ForeignKey(nameof(BlogPostId))]
        public BlogPost BlogPost { get; set; }

        [Required]
        public DateTimeOffset WrittenAt { get; set; } = DateTimeOffset.UtcNow;

        [Required]
        public _BlogItemType type { get; set; } = _BlogItemType.p;



        public enum _BlogItemType
        {
            h1,
            h2, h3, h4, h5, h6,
            img, p, div
        }

        public string contence { get; set; }

        public string? cssCode { get; set; }

        public int? PositionInBlog { get; set; } = 0;
    }
}