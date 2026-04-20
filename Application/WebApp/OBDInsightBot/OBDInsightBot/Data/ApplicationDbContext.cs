using Microsoft.EntityFrameworkCore;
using OBDInsightBot.Models;

public class ApplicationDbContext : DbContext
{
    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
    }

    public DbSet<UserSession> UserSessions { get; set; }
    public DbSet<UserChatItem> UserChatItems { get; set; }
    public DbSet<UserOBDData> UserOBDDatas { get; set; }

    // Blog posts
    public DbSet<BlogPost> BlogPosts { get; set; }
    public DbSet<BlogItem> BlogItems { get; set; }

    // Analytics 
    public DbSet<SingleUse> SignleUses { get; set; }
    public DbSet<TopicAnalytic> TopicAnalytics { get; set; }


    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Performance indexes for frequently queried columns

        // UserChatItems: Frequently queried by SessionId and ordered by ChatPosition
        modelBuilder.Entity<UserChatItem>()
            .HasIndex(c => c.UserSessionId)
            .HasDatabaseName("IX_UserChatItems_SessionId");

        modelBuilder.Entity<UserChatItem>()
            .HasIndex(c => new { c.UserSessionId, c.ChatPosition })
            .HasDatabaseName("IX_UserChatItems_SessionId_Position");

        // UserOBDData: Frequently looked up by SessionId
        modelBuilder.Entity<UserOBDData>()
            .HasIndex(d => d.UserSessionId)
            .IsUnique()
            .HasDatabaseName("IX_UserOBDData_SessionId");

        // UserSession: lastUseTime used for cleanup queries
        modelBuilder.Entity<UserSession>()
            .HasIndex(s => s.lastUseTime)
            .HasDatabaseName("IX_UserSessions_LastUseTime");
    }
}
