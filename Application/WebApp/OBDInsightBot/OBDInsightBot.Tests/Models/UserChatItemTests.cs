using FluentAssertions;
using OBDInsightBot.Models;

namespace OBDInsightBot.Tests.Models;

public class UserChatItemTests
{
    [Fact]
    public void Constructor_ValidParams_SetsAllProperties()
    {
        var sessionId = Guid.NewGuid();
        var sender = ChatSender.User;
        var content = "Hello bot";
        var position = 5;

        var item = new UserChatItem(sessionId, sender, content, position);

        item.UserSessionId.Should().Be(sessionId);
        item.ItemBy.Should().Be(sender);
        item.ChatContent.Should().Be(content);
        item.ChatPosition.Should().Be(position);
    }

    [Fact]
    public void Constructor_ValidParams_GeneratesUniqueId()
    {
        var item = new UserChatItem(Guid.NewGuid(), ChatSender.User, "test", 0);

        item.Id.Should().NotBeEmpty();
    }

    [Fact]
    public void Constructor_ValidParams_SetsSentAtUtcCloseToNow()
    {
        var before = DateTime.UtcNow;
        var item = new UserChatItem(Guid.NewGuid(), ChatSender.User, "test", 0);
        var after = DateTime.UtcNow;

        item.SentAtUtc.Should().BeOnOrAfter(before);
        item.SentAtUtc.Should().BeOnOrBefore(after);
    }

    [Fact]
    public void Constructor_NullChatContent_ThrowsArgumentNullException()
    {
        var act = () => new UserChatItem(Guid.NewGuid(), ChatSender.User, null!, 0);

        act.Should().Throw<ArgumentNullException>()
           .WithParameterName("chatContent");
    }

    [Fact]
    public void Constructor_BotSender_SetsItemByToBot()
    {
        var item = new UserChatItem(Guid.NewGuid(), ChatSender.Bot, "response", 1);

        item.ItemBy.Should().Be(ChatSender.Bot);
    }

    [Fact]
    public void Constructor_SystemSender_SetsItemByToSystem()
    {
        var item = new UserChatItem(Guid.NewGuid(), ChatSender.System, "welcome", 0);

        item.ItemBy.Should().Be(ChatSender.System);
    }

    [Fact]
    public void Constructor_ZeroPosition_SetsPositionToZero()
    {
        var item = new UserChatItem(Guid.NewGuid(), ChatSender.User, "first", 0);

        item.ChatPosition.Should().Be(0);
    }

    [Fact]
    public void Constructor_TwoInstances_HaveDifferentIds()
    {
        var item1 = new UserChatItem(Guid.NewGuid(), ChatSender.User, "a", 0);
        var item2 = new UserChatItem(Guid.NewGuid(), ChatSender.User, "b", 1);

        item1.Id.Should().NotBe(item2.Id);
    }
}
