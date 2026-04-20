using FluentAssertions;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Moq;
using OBDInsightBot.Controllers;
using OBDInsightBot.Models;

namespace OBDInsightBot.Tests.Controllers;

public class OtherControllersTests : IDisposable
{
    private readonly ApplicationDbContext _context;
    private readonly HomeController _homeController;
    private readonly Help _helpController;
    private readonly SettingsController _settingsController;

    public OtherControllersTests()
    {
        var options = new DbContextOptionsBuilder<ApplicationDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;

        _context = new ApplicationDbContext(options);

        // Seed some blog posts for HomeController tests
        _context.BlogPosts.Add(new BlogPost
        {
            Title = "Test Blog",
            MiniDescription = "Mini",
            Content = "Content",
            WrittenAt = DateTime.UtcNow
        });
        _context.SaveChanges();

        var logger = new Mock<ILogger<HomeController>>().Object;

        _homeController = new HomeController(logger, _context);
        _helpController = new Help();
        _settingsController = new SettingsController();
    }

    public void Dispose()
    {
        _context.Dispose();
    }

    #region HomeController

    [Fact]
    public async Task Home_Index_ReturnsViewWithBlogPostsAndDbConnected()
    {
        var result = await _homeController.Index();

        var viewResult = result.Should().BeOfType<ViewResult>().Subject;
        viewResult.ViewData.Should().ContainKey("dbConnected");
        viewResult.ViewData.Should().ContainKey("blogPosts");

        var blogs = viewResult.ViewData["blogPosts"] as List<BlogPost>;
        blogs.Should().NotBeNull();
        blogs.Should().HaveCount(1);
    }

    [Fact]
    public void Home_Privacy_ReturnsView()
    {
        var result = _homeController.Privacy();
        result.Should().BeOfType<ViewResult>();
    }

    [Fact]
    public void Home_Error_ReturnsViewWithErrorViewModel()
    {
        // Arrange
        _homeController.ControllerContext = new ControllerContext
        {
            HttpContext = new DefaultHttpContext() 
        };

        var result = _homeController.Error();

        var viewResult = result.Should().BeOfType<ViewResult>().Subject;
        var model = viewResult.Model.Should().BeOfType<ErrorViewModel>().Subject;

        model.RequestId.Should().NotBeNullOrEmpty();
    }

    #endregion

    #region HelpController

    [Fact]
    public void Help_Index_ReturnsView()
    {
        var result = _helpController.Index();
        result.Should().BeOfType<ViewResult>();
    }

    [Fact]
    public void Help_Example_ReturnsView()
    {
        var result = _helpController.Example();
        result.Should().BeOfType<ViewResult>();
    }

    #endregion

    #region SettingsController

    [Fact]
    public void Settings_Index_ReturnsView()
    {
        var result = _settingsController.Index();
        result.Should().BeOfType<ViewResult>();
    }

    #endregion
}