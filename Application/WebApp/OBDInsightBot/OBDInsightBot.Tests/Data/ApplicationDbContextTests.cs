using FluentAssertions;
using Microsoft.EntityFrameworkCore;
using OBDInsightBot.Models;

namespace OBDInsightBot.Tests.Data;

public class ApplicationDbContextTests : IDisposable
{
    private readonly ApplicationDbContext _context;

    public ApplicationDbContextTests()
    {
        var options = new DbContextOptionsBuilder<ApplicationDbContext>()
            .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
            .Options;
        _context = new ApplicationDbContext(options);
    }

    public void Dispose()
    {
        _context.Dispose();
    }

    [Fact]
    public void CanAddAndRetrieveUserSession()
    {
        var session = new UserSession
        {
            SessionStartTime = DateTime.Now,
            lastUseTime = DateTime.Now
        };
        _context.UserSessions.Add(session);
        _context.SaveChanges();

        _context.UserSessions.Should().HaveCount(1);
        _context.UserSessions.First().Id.Should().Be(session.Id);
    }

    [Fact]
    public void CanAddUserChatItemLinkedToSession()
    {
        var session = new UserSession
        {
            SessionStartTime = DateTime.Now,
            lastUseTime = DateTime.Now
        };
        _context.UserSessions.Add(session);
        _context.SaveChanges();

        var chatItem = new UserChatItem(session.Id, ChatSender.User, "Hello", 0);
        _context.UserChatItems.Add(chatItem);
        _context.SaveChanges();

        _context.UserChatItems.Should().HaveCount(1);
        _context.UserChatItems.First().UserSessionId.Should().Be(session.Id);
    }

    [Fact]
    public void CanAddUserOBDDataLinkedToSession()
    {
        var session = new UserSession
        {
            SessionStartTime = DateTime.Now,
            lastUseTime = DateTime.Now
        };
        _context.UserSessions.Add(session);
        _context.SaveChanges();

        var obdData = new UserOBDData
        {
            UserSessionId = session.Id,
            UploadedAt = DateTime.UtcNow,
            Mark = "Toyota",
            Model = "Corolla"
        };
        _context.UserOBDDatas.Add(obdData);
        _context.SaveChanges();

        _context.UserOBDDatas.Should().HaveCount(1);
        _context.UserOBDDatas.First().UserSessionId.Should().Be(session.Id);
        _context.UserOBDDatas.First().Mark.Should().Be("Toyota");
    }

    [Fact]
    public void MultipleChatItemsForSameSession_AllRetrievable()
    {
        var session = new UserSession
        {
            SessionStartTime = DateTime.Now,
            lastUseTime = DateTime.Now
        };
        _context.UserSessions.Add(session);
        _context.SaveChanges();

        _context.UserChatItems.Add(new UserChatItem(session.Id, ChatSender.User, "Hello", 0));
        _context.UserChatItems.Add(new UserChatItem(session.Id, ChatSender.Bot, "Hi there!", 1));
        _context.UserChatItems.Add(new UserChatItem(session.Id, ChatSender.User, "How is my car?", 2));
        _context.SaveChanges();

        var items = _context.UserChatItems
            .Where(c => c.UserSessionId == session.Id)
            .OrderBy(c => c.ChatPosition)
            .ToList();

        items.Should().HaveCount(3);
        items[0].ChatContent.Should().Be("Hello");
        items[1].ItemBy.Should().Be(ChatSender.Bot);
        items[2].ChatPosition.Should().Be(2);
    }

    [Fact]
    public void DeleteSession_DoesNotCascadeByDefault()
    {
        var session = new UserSession
        {
            SessionStartTime = DateTime.Now,
            lastUseTime = DateTime.Now
        };
        _context.UserSessions.Add(session);
        _context.SaveChanges();

        _context.UserSessions.Remove(session);
        _context.SaveChanges();

        _context.UserSessions.Should().BeEmpty();
    }
}
